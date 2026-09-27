# ruff: noqa: F401, F811
"""Synthetic game, publication and native identity; real signed source and ledgers."""

import copy
import json
from pathlib import Path

import pytest

from mcbench.budgets import DIMENSIONS
from mcbench.records import BudgetLedger
from mcbench.storage import Fault, canonical, digest
from strata_evaluator.body_ticks import BodyTicks
from test_bound_clocks import (clock_source, sampled, fields_history, team_history, globals_history,
    clocked, history, native, reference, repair_env)
from test_craft_reference import ACTOR
from test_clock_barriers import later
from test_worker_publication import committed
from test_setup_facts import renumber
from test_telemetry_auth import signed, write

pytestmark = pytest.mark.parametrize("fields_history", [6], indirect=True)


def allocations(e, bound=100):
    e.budgets.create_account('a2', dict.fromkeys(DIMENSIONS, 100000), 'c1', 'a2', category='training')
    result = {}
    for agent in ('a1', 'a2'):
        operation = 'body-' + agent
        record = e.example('BudgetLedger') | {'is_example': False, 'campaign_id': 'c1', 'agent_id': agent,
            'operation_id': operation, 'source_event_id': operation + ':reserve', 'parent_operation_id': None,
            'kind': 'tool', 'posting': 'reserve', 'campaign_account': 'training', 'model_identity': None,
            'metering': 'reported', 'reason': 'synthetic continuous body reservation',
            'usage': dict.fromkeys(e.example('BudgetLedger')['usage'], 0) | {'avatar_ticks': bound}}
        e.budgets.post(agent, BudgetLedger.model_validate(record))
        result[agent] = {'account': agent, 'operation': operation}
    return result


@pytest.fixture
def window(repair_env, clock_source):
    e = repair_env
    e.begin()
    source = clock_source(campaign='c1', roster={'a1': ACTOR, 'a2': '22222222-2222-2222-2222-222222222222'})
    service = BodyTicks(e.controller)
    return e, source, service


def test_continuous_window_charges_actual_roster_once_and_survives_cas_failure(window, monkeypatch):
    e, s, service = window
    assigned = allocations(e)
    opened = service.open('body', 'c1', 'owner', e.epoch, s.source, s.first, assigned)
    assert service.open('body', 'c1', 'owner', e.epoch, s.source, s.first, assigned) == opened
    e.request()
    put = service._put
    monkeypatch.setattr(service, '_put', lambda _: (_ for _ in ()).throw(OSError('synthetic evidence fault')))
    with pytest.raises(OSError, match='synthetic evidence fault'):
        service.advance('body', 'owner', e.epoch, s.source, s.last)
    floors = e.budgets.consumption_floors(e.database.connection)
    assert floors['body-a1']['avatar_ticks'] == 1 and floors['body-a2']['avatar_ticks'] == 0
    assert 'repair-op' not in floors
    monkeypatch.setattr(service, '_put', put)
    measured = service.advance('body', 'owner', e.epoch, s.source, s.last)
    assert measured['avatar_ticks'] == {'a1': 1, 'a2': 0}
    assert service.advance('body', 'owner', e.epoch, s.source, s.last) == measured
    assert e.database.connection.execute('SELECT count(*) FROM body_tick_samples').fetchone()[0] == 1
    assert e.database.connection.execute("SELECT count(*) FROM operations WHERE actual IS NOT NULL").fetchone()[0] == 0
    assert e.controller.input_authority('c1', 'owner', e.epoch, 'a1')['lease_id'] is None


def test_overrun_retains_actual_amount_and_repeated_read_cannot_bypass_bound(window):
    e, s, service = window
    service.open('body', 'c1', 'owner', e.epoch, s.source, s.first, allocations(e, bound=0))
    for _ in range(2):
        with pytest.raises(Fault, match='BUDGET_EXHAUSTED'):
            service.advance('body', 'owner', e.epoch, s.source, s.last)
    assert e.budgets.status('a1')['committed_and_reserved']['avatar_ticks'] == 1


@pytest.mark.parametrize('damage', ['roster', 'sibling', 'mixed', 'late-repair-operation', 'second-window', 'same-operation'])
def test_body_reservations_are_exclusive_complete_and_owned(window, damage):
    e, s, service = window
    assigned = allocations(e)
    if damage == 'roster':
        assigned.pop('a2')
    elif damage == 'sibling':
        assigned['a1']['account'] = 'a2'
    elif damage == 'mixed':
        assigned['a1']['operation'] = 'repair-op'
    elif damage == 'late-repair-operation':
        e.request()
        with e.database.transaction() as db:
            db.execute("UPDATE repairs SET budget_operation='body-a1'")
    elif damage == 'same-operation':
        assigned['a2'] = assigned['a1']
    else:
        service.open('first', 'c1', 'owner', e.epoch, s.source, s.first, assigned)
    with pytest.raises(ValueError):
        service.open('body', 'c1', 'owner', e.epoch, s.source, s.first, assigned)


def publication_fixture(e, source):
    proof = committed(e.example)
    plan = proof['measurement']['worker_plan']
    plan.update(campaign_id='c1', agent_id='a1', epoch=e.epoch, transaction_id='tx')
    proof['commit']['decision']['worker_plan'] = copy.deepcopy(plan)
    proof['commit']['observation'].update(campaign_id='c1', agent_id='a1', epoch=e.epoch)
    proof['commit']['measurement_digest'] = digest(proof['measurement'])
    ref = e.put({'schema': 'strata/ControllerPublicationEvidence/1', 'is_example': True,
                 'transaction_id': 'tx', 'worker_receipt': proof})
    with e.database.transaction() as db:
        db.execute('CREATE TABLE repair_publication_evidence (id TEXT PRIMARY KEY,binding TEXT,source_ref TEXT)')
        db.execute("INSERT INTO repair_publication_evidence VALUES ('tx','synthetic',?)", (ref,))
        db.execute("INSERT INTO repair_native_handoffs VALUES ('tx','synthetic',?,'{}','CONFIRMED','synthetic')",
                   (canonical({'body_fingerprint': source.source.observe(source.first)['body_fingerprints']['a1']}).decode(),))


@pytest.mark.parametrize('damage', [None, 'late', 'no-publication', 'overlap', 'wrong-body', 'stale-sample'])
def test_repair_coverage_requires_preexisting_window_and_after_publication_sample(window, damage):
    e, s, service = window
    assigned = allocations(e)
    if damage == 'late':
        e.request()
    service.open('body', 'c1', 'owner', e.epoch, s.source, s.first, assigned)
    if damage != 'late':
        e.request()
    if damage != 'no-publication':
        publication_fixture(e, s)
    if damage == 'overlap':
        with e.database.transaction() as db:
            e.budgets.retain_consumption_floor(db, 'a1', 'repair-op', 'old-tick-proof', 'avatar_ticks', 1, {'synthetic': True})
    if damage == 'wrong-body':
        with e.database.transaction() as db:
            db.execute("UPDATE repair_native_handoffs SET target=?", (canonical({'body_fingerprint': '0' * 64}).decode(),))
    s.body['records'] = s.first
    s.persist()
    if damage not in (None, 'stale-sample'):
        with pytest.raises(ValueError):
            service.request_repair_coverage('body', e.repairs, 'tx', 'owner', e.epoch, s.source)
        return
    requested = service.request_repair_coverage('body', e.repairs, 'tx', 'owner', e.epoch, s.source)
    if damage:
        later(s, s.first)
    else:
        # A second post-request health/clock pair can acknowledge the first.
        health, sample = copy.deepcopy(s.events[s.last - 2:s.last])
        acknowledged = s.last
        for event in (health, sample):
            event['server_tick'] += 1
        health['payload']['durable_event_seq_before_sample'] = acknowledged
        sample['payload']['completed_server_ticks'] += 1
        sample['payload']['elapsed_wall_ns'] += health['payload']['interval_wall_ns']
        sample['payload']['observed_tick_work_ns'] += health['payload']['observed_tick_work_ns']
        sample['payload']['avatar_tick_events'][ACTOR] += 1
        s.events[s.last:s.last] = [health, sample]
        renumber(s.events)
        s.last += 2
        write(s.path, signed(s.broker.authority, Path(s.broker.authority.key_file).read_bytes(), s.events))
        s.body.update(records=s.last, clock_sample_cursor=s.last)
        s.persist()
    if damage:
        with pytest.raises(Fault, match='CLOCK_BARRIER_NOT_REACHED'):
            service.cover_repair('body', e.repairs, 'tx', 'owner', e.epoch, s.source)
        return
    result = service.cover_repair('body', e.repairs, 'tx', 'owner', e.epoch, s.source)
    assert result['closing_request_ref'] == requested['request_ref']
    assert result['continuous_consumption']['avatar_ticks'] == {'a1': 2, 'a2': 0}
    assert result['exact_repair_ticks'] is None and not result['repair_tick_cost_reposted']
    assert not result['complete_repair_accounting'] and not result['campaign_permission_published']
    assert service.cover_repair('body', e.repairs, 'tx', 'owner', e.epoch, s.source) == result


def test_body_tick_operation_cannot_be_reused_by_repair(window):
    e, s, service = window
    service.open('body', 'c1', 'owner', e.epoch, s.source, s.first, allocations(e))
    with pytest.raises(Fault, match='BODY_TICK_DOUBLE_ALLOCATION'):
        e.repairs.request('c1', 'owner', e.epoch, 'tx', 'a1', 'body-a1', deadline_unix=150)
