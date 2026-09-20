import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from mcbench.budgets import Budgets, DIMENSIONS
from mcbench.clocks import Clocks
from mcbench.controller import Controller
from mcbench.records import BudgetLedger
from mcbench.reconfiguration import Reconfigurations
from mcbench.storage import Database, Fault, canonical, digest
from test_controls import Controls, SyntheticSettings
from test_storage_controller import CAPACITY, READINESS, REF, setup_campaign, start


@pytest.fixture
def repair_env(database, cas, operator, configs, example):
    now, mono = [100.0], [1000.0]
    controller = Controller(database, simulation=True, cas=cas, clock=lambda: now[0])
    config, epoch = setup_campaign(controller, configs)
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    repairs = Reconfigurations(controller, controls, monotonic=lambda: mono[0])
    def put(value):
        return cas.put(operator, 'operator', 'operator', canonical(value))
    witness = cas.put(operator, 'operator', 'operator', b'Synthetic worker witness; no Minecraft.')
    policy = {'schema': 'strata/RepairPolicy/1', 'is_example': True, 'campaign_id': 'c1',
              'system_digest': config.system_digest, 'protocol_ref': config.protocol_ref,
              'condition': 'training', 'reconfiguration_allowed': True,
              'profiles': {'a1': adapter.state['profile_id'], 'a2': 'synthetic-profile-2'}}
    budgets = Budgets(database)
    budgets.create_account('a1', dict.fromkeys(DIMENSIONS, 100000), 'c1', 'a1', category='training')

    def budget(posting='reserve', operation='repair-op', primitive_events=20):
        body = example('BudgetLedger') | {'is_example': False, 'campaign_id': 'c1', 'agent_id': 'a1',
            'operation_id': operation, 'source_event_id': operation + ':' + posting,
            'parent_operation_id': None, 'kind': 'tool', 'posting': posting, 'campaign_account': 'training',
            'usage': {key: 0 for key in example('BudgetLedger')['usage']} | {'primitive_events': primitive_events},
            'metering': 'reported', 'reason': 'synthetic-repair', 'model_identity': None}
        budgets.post('a1', BudgetLedger.model_validate(body))

    def begin(condition='training', allowed=True):
        repairs.configure('c1', 'owner', epoch, put(policy | {'condition': condition,
                                                           'reconfiguration_allowed': allowed}))
        start(controller, config, epoch)
        controls.plan('a1', 'tx', ['target'])
        budget()

    def request():
        return repairs.request('c1', 'owner', epoch, 'tx', 'a1', 'repair-op', deadline_unix=150.0)

    def proof(ready=False, *, changes=None, observation_changes=None):
        status = repairs.status('tx')
        body = {'schema': 'strata/RepairReady/1' if ready else 'strata/RepairStop/1',
                'is_example': True, 'campaign_id': 'c1', 'agent_id': 'a1', 'transaction_id': 'tx',
                'epoch': status['epoch'], 'generation': status['generation'], 'profile_id': adapter.state['profile_id'],
                'fingerprint': adapter.state['fingerprint'], 'observed_unix': now[0], 'source_refs': [witness],
                'inputs_released': True}
        if ready:
            keymap = digest({key: value['key'] for key, value in adapter.state['bindings'].items()})
            observation = example('Observation') | {'is_example': True, 'campaign_id': 'c1', 'agent_id': 'a1',
                'epoch': status['epoch'], 'recorded_at': datetime.fromtimestamp(now[0], timezone.utc).isoformat().replace('+00:00', 'Z'),
                'control_revision': adapter.state['revision'], 'keymap_digest': keymap,
                'age_at_send_ms': 0, 'gateway_sent_mono_ms': 1000, 'captured_mono_ms': 1000, 'held_keys': []}
            observation['state']['connected'] = True
            observation['state']['active_request_id'] = None
            observation.update(observation_changes or {})
            body |= {'connected': True, 'control_revision': adapter.state['revision'],
                     'keymap_digest': keymap, 'observation_ref': put(observation)}
        else:
            body |= {'old_lease_id': status['request']['old_lease_id'], 'pending_cancelled': True}
        return put(body | (changes or {}))

    def grant(agent='a1', methods=None):
        return controller.grant('c1', 'owner', epoch, agent, f'campaign:c1:agent:{agent}', methods or ['act', 'observe'])

    return SimpleNamespace(**locals())


def test_only_target_avatar_is_fenced_then_released_with_new_authority(repair_env):
    e = repair_env
    e.begin()
    first, teammate = e.grant(), e.grant('a2')
    old = e.controller.input_authority('c1', 'owner', e.epoch, 'a1')
    receipt = e.request()
    assert receipt == e.request()
    assert e.controller.status('c1')['state'] == 'RUNNING'
    assert e.controller.input_authority('c1', 'owner', e.epoch, 'a1')['state'] == 'QUIESCING'
    with pytest.raises(Fault, match='FORBIDDEN'):
        e.controller.authorize(first, 'c1', 'a1', e.epoch, 'act', 101)
    with pytest.raises(Fault, match='INPUT_SUSPENDED'):
        e.grant()
    assert e.controller.authorize(teammate, 'c1', 'a2', e.epoch, 'act', 101)
    assert e.controller.authorize(e.grant(methods=['observe']), 'c1', 'a1', e.epoch, 'observe', 101)
    with pytest.raises(Fault, match='REPAIR_RECOVERY_REQUIRED'):
        e.repairs.apply('tx', 'owner', e.epoch)
    stop = e.proof()
    e.repairs.enter('tx', 'owner', e.epoch, stop)
    e.repairs.enter('tx', 'owner', e.epoch, stop)
    assert e.repairs.apply('tx', 'owner', e.epoch)['phase'] == 'AWAITING_OBSERVATION'
    with pytest.raises(Fault, match='REPAIR_BUDGET_UNSETTLED'):
        e.repairs.finish('tx', 'owner', e.epoch, e.proof(True))
    e.budget('settle', primitive_events=8)
    ready = e.proof(True)
    done = e.repairs.finish('tx', 'owner', e.epoch, ready)
    assert done['result']['input_resumed'] is True
    assert e.repairs.finish('tx', 'owner', e.epoch, ready) == done
    current = e.controller.input_authority('c1', 'owner', e.epoch, 'a1')
    assert current['generation'] > old['generation'] and current['lease_id'] != old['lease_id']
    assert e.controller.authorize(e.grant(), 'c1', 'a1', e.epoch, 'act', 101)
    with pytest.raises(Fault, match='FORBIDDEN'):
        e.controller.authorize(first, 'c1', 'a1', e.epoch, 'act', 101)
    assert e.budgets.status('a1')['committed_and_reserved']['primitive_events'] == 8


@pytest.mark.parametrize('changes', [{'pending_cancelled': False}, {'inputs_released': False},
    {'old_lease_id': 'wrong'}, {'agent_id': 'a2'}, {'generation': 999}, {'profile_id': 'wrong'},
    {'observed_unix': 90.0}, {'source_refs': ['cas:sha256:' + '0' * 64]}, {'is_example': False}])
def test_release_receipt_failure_retains_hold_and_never_writes(repair_env, changes):
    e = repair_env
    e.begin()
    e.request()
    with pytest.raises(Fault):
        e.repairs.enter('tx', 'owner', e.epoch, e.proof(changes=changes))
    assert e.repairs.status('tx')['phase'] == 'QUIESCING'
    assert not e.adapter.requests


@pytest.mark.parametrize('condition,allowed,code', [('cognitive_probe', True, 'PROBE_RECONFIGURATION_FORBIDDEN'),
    ('cognitive_probe', False, 'RECONFIGURATION_FORBIDDEN'), ('training', False, 'RECONFIGURATION_FORBIDDEN')])
def test_frozen_policy_forbids_cognitive_probe_repair(repair_env, condition, allowed, code):
    e = repair_env
    with pytest.raises(Fault, match=code):
        e.begin(condition, allowed)
        e.request()
    assert not e.adapter.requests


def test_policy_cannot_change_after_start_and_request_cannot_change_intent(repair_env):
    e = repair_env
    e.begin()
    with pytest.raises(Fault, match='POLICY_IMMUTABLE'):
        e.repairs.configure('c1', 'owner', e.epoch, e.put(e.policy | {'condition': 'keymap_learning'}))
    e.request()
    with pytest.raises(Fault, match='IDEMPOTENCY_CONFLICT'):
        e.repairs.request('c1', 'owner', e.epoch, 'tx', 'a1', 'repair-op', deadline_unix=140.0)


@pytest.mark.parametrize('mutation', ['old-time', 'other-agent', 'keys-held', 'disconnected', 'active-action', 'keymap'])
def test_stale_or_wrong_observation_never_restores_input(repair_env, mutation):
    e = repair_env
    e.begin()
    e.request()
    e.repairs.enter('tx', 'owner', e.epoch, e.proof())
    e.repairs.apply('tx', 'owner', e.epoch)
    e.budget('settle')
    changes = {}
    if mutation == 'old-time':
        changes['recorded_at'] = '1970-01-01T00:00:01Z'
    elif mutation == 'other-agent':
        changes['agent_id'] = 'a2'
    elif mutation == 'keys-held':
        changes['held_keys'] = [copy.deepcopy(e.adapter.state['bindings']['target']['key'])]
    elif mutation == 'keymap':
        changes['keymap_digest'] = '0' * 64
    else:
        state = e.example('Observation')['state']
        state['connected'] = mutation != 'disconnected'
        state['active_request_id'] = 'pending' if mutation == 'active-action' else None
        changes['state'] = state
    with pytest.raises(Fault, match='FRESH_OBSERVATION_REQUIRED'):
        e.repairs.finish('tx', 'owner', e.epoch, e.proof(True, observation_changes=changes))
    assert e.controller.input_authority('c1', 'owner', e.epoch, 'a1')['lease_id'] is None


def test_clock_intervals_charge_repair_and_preserve_dedup_across_finish(repair_env):
    e = repair_env
    e.begin()
    e.request()
    clocks = Clocks(e.database)
    values = dict(elapsed_ms=1000, n=2, server_stopped=False, inference_suspended=False,
                  server_ticks=18, avatar_ticks=18, disconnected_body_ms=1000, boot_id='synthetic-boot')
    clocks.record('c1', 'repair-interval', **values)
    with pytest.raises(Fault, match='REPAIR_EXPOSURE_REQUIRED'):
        clocks.record('c1', 'false-free-pause', **(values | {'server_stopped': True, 'inference_suspended': True,
                                                         'server_ticks': 0, 'avatar_ticks': 0}))
    with pytest.raises(Fault, match='CLOCK_ROSTER_MISMATCH'):
        clocks.record('c1', 'wrong-team-size', **(values | {'n': 1}))
    e.repairs.enter('tx', 'owner', e.epoch, e.proof())
    e.repairs.apply('tx', 'owner', e.epoch)
    e.budget('settle')
    e.repairs.finish('tx', 'owner', e.epoch, e.proof(True))
    clocks.record('c1', 'repair-interval', **values)
    assert clocks.totals('c1')['active_ms'] == 1000
    assert clocks.totals('c1')['reserved_body_ms'] == 2000
    assert [tuple(row) for row in e.database.connection.execute('SELECT * FROM clock_repairs')] == [
        ('c1', 'repair-interval', 'a1', 'tx')]


def test_crash_after_forward_write_requires_rollback_not_replay(repair_env):
    e = repair_env
    e.begin()
    e.request()
    e.repairs.enter('tx', 'owner', e.epoch, e.proof())
    original = e.adapter.verify_and_restart
    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt('synthetic process interruption')
    e.adapter.verify_and_restart = interrupted
    with pytest.raises(KeyboardInterrupt):
        e.repairs.apply('tx', 'owner', e.epoch)
    assert e.repairs.status('tx')['phase'] == 'RECOVERY_REQUIRED'
    with pytest.raises(Fault, match='REPAIR_RECOVERY_REQUIRED'):
        e.repairs.apply('tx', 'owner', e.epoch)
    e.adapter.verify_and_restart = original
    assert e.repairs.rollback('tx', 'owner', e.epoch)['phase'] == 'AWAITING_OBSERVATION'
    e.budget('settle', primitive_events=6)
    assert e.repairs.finish('tx', 'owner', e.epoch, e.proof(True))['result']['control_phase'] == 'rolled_back'
    assert [direction for _, direction, _ in e.adapter.requests] == [False, True]


def test_timeout_despite_wall_clock_reversal_keeps_input_off(repair_env):
    e = repair_env
    e.begin()
    e.request()
    e.mono[0] += 2
    e.now[0] -= 10
    assert e.repairs.expire() == ['tx']
    assert e.repairs.expire() == []
    assert e.controller.input_authority('c1', 'owner', e.epoch, 'a1')['state'] == 'INTERRUPTED'


def test_controller_takeover_retains_repair_and_cannot_resume_whole_team_around_it(repair_env):
    e = repair_env
    e.begin()
    e.request()
    e.now[0] += 7
    epoch = e.controller.claim('c1', 'new-owner', e.controller.status('c1')['revision'])
    adopted = e.repairs.adopt_recovery('tx', 'new-owner', epoch)
    assert adopted['epoch'] == epoch and adopted['phase'] == 'RECOVERY_REQUIRED'
    with pytest.raises(Fault, match='REPAIR_RECOVERY_REQUIRED'):
        e.repairs.apply('tx', 'new-owner', epoch)
    e.repairs.rollback('tx', 'new-owner', epoch)
    e.budget('settle', primitive_events=0)
    e.repairs.finish('tx', 'new-owner', epoch, e.proof(True))
    assert e.controller.input_authority('c1', 'new-owner', epoch, 'a1')['repair'] is None


def test_database_reopen_does_not_clear_repair_hold(repair_env):
    e = repair_env
    e.begin()
    e.request()
    reopened = Database(e.database.path)
    try:
        controller = Controller(reopened, simulation=True, clock=lambda: e.now[0], cas=e.cas)
        controls = Controls(reopened, e.adapter)
        repairs = Reconfigurations(controller, controls, monotonic=lambda: e.mono[0])
        assert repairs.status('tx')['phase'] == 'QUIESCING'
        with pytest.raises(Fault, match='INPUT_SUSPENDED'):
            controller.grant('c1', 'owner', e.epoch, 'a1', 'campaign:c1:agent:a1', ['act'])
        assert repairs.expire() == ['tx']
    finally:
        reopened.close()


def test_second_executor_input_grant_revokes_first_but_preserves_other_avatar(repair_env):
    e = repair_env
    e.begin()
    first, other = e.grant(), e.grant('a2')
    second = e.grant()
    with pytest.raises(Fault, match='FORBIDDEN'):
        e.controller.authorize(first, 'c1', 'a1', e.epoch, 'act', 101)
    assert e.controller.authorize(second, 'c1', 'a1', e.epoch, 'act', 101)
    assert e.controller.authorize(other, 'c1', 'a2', e.epoch, 'act', 101)


def test_budget_overrun_is_retained_and_repair_cannot_resume_input(repair_env):
    e = repair_env
    e.begin()
    e.request()
    e.repairs.enter('tx', 'owner', e.epoch, e.proof())
    e.repairs.apply('tx', 'owner', e.epoch)
    e.budget('settle', primitive_events=100001)
    finished = e.repairs.finish('tx', 'owner', e.epoch, e.proof(True))
    assert finished['result']['state'] == 'INTERRUPTED' and not finished['result']['input_resumed']
    assert e.budgets.status('a1')['committed_and_reserved']['primitive_events'] == 100001
    with pytest.raises(Fault, match='INPUT_SUSPENDED'):
        e.grant()


def test_lease_expiry_during_verification_retains_native_result_but_no_input(repair_env):
    e = repair_env
    e.begin()
    e.request()
    e.repairs.enter('tx', 'owner', e.epoch, e.proof())
    original = e.adapter.verify_and_restart
    def verify(*args, **kwargs):
        result = original(*args, **kwargs)
        e.now[0] += 7
        e.mono[0] += 7
        return result
    e.adapter.verify_and_restart = verify
    with pytest.raises(Fault, match='LEASE_EXPIRED'):
        e.repairs.apply('tx', 'owner', e.epoch)
    assert e.controls.status('tx')['phase'] == 'committed'
    assert e.repairs.status('tx')['phase'] == 'RECOVERY_REQUIRED'
    assert e.database.connection.execute("SELECT lease_id FROM avatar_lanes WHERE agent='a1'").fetchone()[0] is None


def test_concurrent_requests_cannot_hold_the_same_profile_twice(repair_env):
    e = repair_env
    e.begin()
    e.controls.plan('a1', 'tx2', ['target'])
    e.budget(operation='repair-op-2')
    def request(pair):
        transaction_id, operation = pair
        db = Database(e.database.path)
        try:
            controller = Controller(db, simulation=True, clock=lambda: 100.0)
            controls = Controls(db, e.adapter)
            repairs = Reconfigurations(controller, controls, monotonic=lambda: 1000.0)
            repairs.request('c1', 'owner', e.epoch, transaction_id, 'a1', operation, deadline_unix=150.0)
            return 'held'
        except Fault as error:
            return error.code
        finally:
            db.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(request, [('tx', 'repair-op'), ('tx2', 'repair-op-2')])) == ['SETTINGS_BUSY', 'held']
    assert e.database.connection.execute('SELECT COUNT(*) FROM repairs').fetchone()[0] == 1


def test_budget_operation_cannot_pay_for_two_repairs(repair_env):
    e = repair_env
    e.begin()
    e.request()
    # The unique operation binding survives completion, independently of phase.
    e.database.connection.execute("UPDATE repairs SET phase='COMPLETE' WHERE id='tx'")
    e.database.connection.execute("UPDATE avatar_lanes SET repair=NULL,state='READY',lease_id='new' WHERE agent='a1'")
    e.controls.plan('a1', 'tx2', ['target'])
    with pytest.raises(Fault, match='REPAIR_BUDGET_REUSED'):
        e.repairs.request('c1', 'owner', e.epoch, 'tx2', 'a1', 'repair-op', deadline_unix=150.0)


def test_slow_snapshot_cannot_publish_expired_readiness(repair_env):
    e = repair_env
    e.begin()
    e.request()
    e.repairs.enter('tx', 'owner', e.epoch, e.proof())
    e.repairs.apply('tx', 'owner', e.epoch)
    e.budget('settle')
    ready_ref = e.proof(True)
    snapshot = e.adapter.snapshot
    def slow():
        result = snapshot()
        e.now[0] += 3
        e.mono[0] += 3
        return result
    e.adapter.snapshot = slow
    with pytest.raises(Fault, match='REPAIR_EVIDENCE_INVALID'):
        e.repairs.finish('tx', 'owner', e.epoch, ready_ref)
    assert e.controller.input_authority('c1', 'owner', e.epoch, 'a1')['lease_id'] is None


def test_action_grant_requires_ready_avatar_and_legacy_authority_is_not_inferred(database, configs):
    controller = Controller(database, simulation=True)
    config, epoch = setup_campaign(controller, configs)
    controller.certify('w', 'fp', CAPACITY, REF, simulation=True)
    controller.admit('c1', 'owner', epoch, controller.status('c1')['revision'], 'w', 'fp',
                     CAPACITY | {'bodies': 2})
    with pytest.raises(Fault, match='INPUT_SUSPENDED'):
        controller.grant('c1', 'owner', epoch, 'a1', 'campaign:c1:agent:a1', ['act'])
    read_grant = controller.grant('c1', 'owner', epoch, 'a1', 'campaign:c1:agent:a1', ['observe'])
    controller.ready('c1', 'owner', epoch, controller.status('c1')['revision'],
                     {a: dict.fromkeys(READINESS, REF) for a in config.agent_ids})
    assert controller.authorize(read_grant, 'c1', 'a1', epoch, 'observe', controller.clock() + 1)
    database.connection.execute("DELETE FROM avatar_lanes WHERE campaign='c1'")
    with pytest.raises(Fault, match='INPUT_AUTHORITY_REQUIRED'):
        controller.grant('c1', 'owner', epoch, 'a1', 'campaign:c1:agent:a1', ['observe'])
