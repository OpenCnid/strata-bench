"""Actual Windows file leases with synthetic pair, capacity and budget records."""

import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from mcbench.budgets import DIMENSIONS
from mcbench.controller import Controller, reserved_resources
from mcbench.native_probe_binding import read_binding
from mcbench.storage import Fault, Principal, canonical
from strata_evaluator.native_probe_bindings import ProbeNativeBindings
from strata_evaluator.native_probe_views import ProbeNativeViews
from strata_evaluator.probe_custody import ProbeCustody
from test_probe_pairs import EVALUATOR, pair_source as _pair_source
from test_storage_controller import setup_campaign

pair_source = _pair_source
pytestmark = [pytest.mark.skipif(os.name != "nt", reason="actual Windows deny-write lease"),
              pytest.mark.parametrize("pair_source", [{"probe_spend": 1000}], indirect=True)]

PER_ARM = {"bodies": 1, "memory_mib": 128, "disk_bytes": 1000000, "model_slots": 3}
CAPACITY = {k:v*2 for k,v in PER_ARM.items()}


@pytest.fixture
def custody(pair_source, tmp_path, example):
    pairs, request, _, runtime = pair_source
    pairs.prepare(EVALUATOR, request(), tmp_path / "pair")
    views = ProbeNativeViews(pairs)
    views.prepare(EVALUATOR, "p1", tmp_path / "native", max_bytes=1024*1024)
    bindings = ProbeNativeBindings(views)
    runtime.budgets.create_account("probe-total", dict.fromkeys(DIMENSIONS, 1000000), "*", category="evaluation")
    destinations = {}
    for arm in ("initial", "experienced"):
        d = {"job_id":arm+"-job", "campaign_id":arm+"-probe", "agent_id":"avatar", "account":arm+"-account",
             "operation_id":arm+"-operation", "supply_helper_artifacts":True}
        destinations[arm] = {"a1":d}
        runtime.budgets.create_account(d["account"], dict.fromkeys(DIMENSIONS,100000), d["campaign_id"],d["agent_id"],
                                      parent="probe-total",category="evaluation")
    refs = bindings.bind(EVALUATOR,"p1",destinations)
    reserves = {}
    for group in refs.values():
        body = read_binding(bindings.db.connection,bindings.cas,group["a1"])
        d = body.destination
        reserves[d.job_id] = example("BudgetLedger") | {"is_example":False,"campaign_id":d.campaign_id,
            "epoch":1,"campaign_account":"evaluation","agent_id":d.agent_id,"operation_id":d.operation_id,
            "parent_operation_id":None,"source_event_id":d.job_id+"-reserve","ledger_id":d.job_id+"-ledger",
            "posting":"reserve","kind":"model","model_identity":body.model,
            "usage":{"input_tokens":100,"output_tokens":10,"cached_input_tokens":0,"reasoning_tokens":0,
                     "model_calls":2,"primitive_events":0,"avatar_ticks":0,"wall_ms":0,"spend_microusd":100}}
    now = [time.time()]
    controller = Controller(bindings.db,simulation=True,clock=lambda:now[0])
    controller.certify("probe-worker","fixture-pins",CAPACITY,"cas:sha256:"+"a"*64,simulation=True)
    service = ProbeCustody(bindings,clock=lambda:now[0])
    yield service,reserves,controller,now
    service.close()


def acquire(fixture, **updates):
    service,reserves,_,_ = fixture
    return service.acquire(EVALUATOR,"p1",reserves,**({"worker":"probe-worker","fingerprint":"fixture-pins",
        "per_arm_resources":PER_ARM,"lifetime_s":120}|updates))


def state(service):
    row=service.db.connection.execute("SELECT state FROM probe_pair_custody").fetchone()
    return row[0] if row else None


def test_whole_pair_holds_actual_files_budgets_capacity_and_closes_without_refunding(custody, tmp_path):
    service = acquire(custody)
    assert service.check()["state"] == "HELD" and not service.check()["native_launch_authorized"]
    assert reserved_resources(service.db.connection,"probe-worker") == CAPACITY
    assert service.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200
    pair=json.loads(service.db.connection.execute("SELECT plan FROM probe_pair_staging").fetchone()[0])
    files=[tmp_path/"pair"/pair["arm_directories"][a]/"server/world/level.dat" for a in pair["arm_order"]]
    before=[p.read_bytes() for p in files]
    for path in files:
        with pytest.raises(PermissionError):
            path.write_bytes(b"changed")
        with pytest.raises(PermissionError):
            path.unlink()
    script="from pathlib import Path; Path("+repr(str(files[0]))+").write_bytes(b'foreign writer')"
    child=subprocess.run([sys.executable,"-I","-c",script],capture_output=True,text=True,timeout=10,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    assert child.returncode != 0 and "PermissionError" in child.stderr
    assert [p.read_bytes() for p in files] == before
    (tmp_path/"physical-custody.json").write_bytes(canonical({"parent_write_delete_denials":4,
        "child_returncode":child.returncode,"child_stderr":child.stderr,
        "world_hashes":[hashlib.sha256(raw).hexdigest() for raw in before],
        "held_state":service.check(),"budget_hold":200,"resources":CAPACITY}))
    service.release_undispatched_resources()
    assert state(service)=="CLOSED" and service.lease.closed
    assert not any(reserved_resources(service.db.connection,"probe-worker").values())
    assert service.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200
    files[0].write_bytes(before[0])  # handle release actually occurred
    with pytest.raises(Fault,match="PROBE_CUSTODY_CONSUMED"):
        ProbeCustody(service.bindings).acquire(EVALUATOR,"p1",custody[1],worker="probe-worker",
            fingerprint="fixture-pins",per_arm_resources=PER_ARM)


@pytest.mark.parametrize("shortage",["budget","capacity"])
def test_failure_on_whole_pair_admission_leaves_no_partial_envelope_or_resources(custody,shortage):
    service,_,_,_=custody
    db=service.db.connection
    if shortage=="budget":
        limits=dict.fromkeys(DIMENSIONS,1000000)|{"spend_microusd":150}
        db.execute("UPDATE accounts SET limits=? WHERE id='probe-total'",(canonical(limits).decode(),))
    else:
        db.execute("UPDATE workers SET capacity=? WHERE id='probe-worker'",(canonical(CAPACITY|{"bodies":1}).decode(),))
    with pytest.raises(Fault,match="BUDGET_EXHAUSTED|CAPACITY_EXCEEDED"):
        acquire(custody)
    assert state(service)=="FAILED" and service.lease.closed
    assert db.execute("SELECT count(*) FROM operations WHERE account LIKE '%-account'").fetchone()[0]==0
    assert db.execute("SELECT count(*) FROM probe_pair_resources").fetchone()[0]==0
    assert service.runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"]==56


@pytest.mark.parametrize("fault",["missing_member","unmatched_budget","wrong_category","wrong_model","partial_team","helper_slots"])
def test_preflight_refuses_incomplete_or_unmatched_admission_without_intent(custody,fault):
    service,reserves,_,_=custody
    resource=PER_ARM
    if fault=="missing_member":
        del reserves["initial-job"]
    elif fault=="unmatched_budget":
        reserves["initial-job"]["usage"]["input_tokens"]-=1
    elif fault=="wrong_category":
        reserves["initial-job"]["campaign_account"]="training"
    elif fault=="wrong_model":
        reserves["initial-job"]["model_identity"]="other"
    elif fault=="partial_team":
        resource=PER_ARM|{"bodies":2}
    else:
        resource=PER_ARM|{"model_slots":1}
    with pytest.raises(Fault,match="NATIVE_PROBE_ROSTER|PROBE_UNMATCHED_ENVELOPES|PROBE_RESERVATION_SCOPE|PARTIAL_TEAM_FORBIDDEN"):
        acquire(custody,per_arm_resources=resource)
    assert state(service) is None and service.lease is None


def test_campaigns_and_new_worker_profiles_cannot_overbook_held_pair(custody,configs):
    service=acquire(custody)
    controller=custody[2]
    config,epoch=setup_campaign(controller,configs,n=1,campaign="unrelated")
    assert controller.admit("unrelated","owner",epoch,controller.status("unrelated")["revision"],
        "probe-worker","fixture-pins",PER_ARM)=="QUEUED"
    with pytest.raises(Fault,match="WORKER_IN_USE"):
        controller.certify("probe-worker","changed",CAPACITY,"cas:sha256:"+"a"*64,simulation=True)
    assert service.check()["state"]=="HELD"
    service.release_undispatched_resources()
    assert controller.admit("unrelated","owner",epoch,controller.status("unrelated")["revision"],
        "probe-worker","fixture-pins",PER_ARM)=="STARTING"


@pytest.mark.parametrize("fault",["expiry","extra_directory","account_category","uncertainty","resource_row","envelope_marker",
                                  "original_ledger","negative_resource"])
def test_lost_custody_fences_without_releasing_capacity_or_costs(custody,tmp_path,fault):
    service=acquire(custody)
    db=service.db.connection
    if fault=="expiry":
        custody[3][0]+=121
    elif fault=="extra_directory":
        (tmp_path/"native/copy-0/body-0/profile/foreign").mkdir()
    elif fault=="account_category":
        db.execute("UPDATE accounts SET category='training' WHERE id='initial-account'")
    elif fault=="uncertainty":
        service.runtime.budgets.hold_uncertain("initial-account","initial-operation","synthetic unknown")
    elif fault=="resource_row":
        db.execute("UPDATE probe_pair_resources SET resources=?",(canonical(CAPACITY|{"bodies":1}).decode(),))
    elif fault=="envelope_marker":
        db.execute("DELETE FROM budget_envelopes WHERE operation='initial-operation'")
    elif fault=="original_ledger":
        db.execute("UPDATE ledger SET digest=? WHERE campaign='initial-probe'",("f"*64,))
    else:
        db.execute("UPDATE reservations SET resources=? WHERE campaign='c1'",(canonical(PER_ARM|{"bodies":-1}).decode(),))
        db.execute("UPDATE reservations SET worker='probe-worker' WHERE campaign='c1'")
    with pytest.raises(Fault,match="PROBE_CUSTODY_EXPIRED|MIXED_SNAPSHOT|NATIVE_PROBE_ACCOUNT|PROBE_ENVELOPE_CHANGED|METERING_UNKNOWN|PROBE_RESOURCE_HOLD_CHANGED|CAPACITY_RESERVATION_CORRUPT"):
        service.check()
    assert state(service)=="FENCED"
    assert db.execute("SELECT released FROM probe_pair_resources").fetchone()[0]==0
    assert db.execute("SELECT count(*) FROM operations WHERE account LIKE '%-account' AND actual IS NULL").fetchone()[0]==2
    with pytest.raises(Fault,match="PROBE_CUSTODY_LOST"):
        service.release_undispatched_resources()


def test_new_owner_cannot_inherit_file_handles_or_release_stale_reservations(custody):
    service=acquire(custody)
    other=ProbeCustody(service.bindings)
    other.pair_id,other.plan=service.pair_id,service.plan
    with pytest.raises(Fault,match="PROBE_CUSTODY_NOT_HELD"):
        other.check()
    assert state(service)=="HELD"
    assert service.check()["state"]=="HELD"
    service.close()
    assert state(service)=="FENCED" and reserved_resources(service.db.connection,"probe-worker")==CAPACITY


def test_journal_failure_rolls_back_both_envelopes_and_capacity(custody,monkeypatch):
    service=custody[0]
    original=service.db.event
    def fail(db,kind,body):
        if kind=="probe.custody_held":
            assert db.execute("SELECT count(*) FROM operations WHERE account LIKE '%-account'").fetchone()[0]==2
            raise OSError("synthetic journal failure")
        return original(db,kind,body)
    monkeypatch.setattr(service.db,"event",fail)
    with pytest.raises(OSError,match="synthetic journal failure"):
        acquire(custody)
    assert state(service)=="FAILED" and service.lease.closed
    event=json.loads(service.db.connection.execute("SELECT body FROM outbox WHERE kind='probe.custody_fenced'").fetchone()[0])
    assert event["reason"]=="OSError"
    assert service.db.connection.execute("SELECT count(*) FROM probe_pair_resources").fetchone()[0]==0
    assert service.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"]==0


def test_actual_owner_process_exit_retains_holds_and_prevents_reacquisition(custody,tmp_path):
    service,reserves,_,_=custody
    repo=Path(__file__).resolve().parents[1]
    config=tmp_path/"child.json"
    config.write_bytes(canonical({"db":str(service.db.path),"objects":str(service.cas.root),"reservations":reserves}))
    script="""
import json,os,sys
from pathlib import Path
sys.path[:0]=[sys.argv[1]+'/src',sys.argv[1]+'/evaluator/src']
from mcbench.storage import Database,CAS,Principal
from mcbench.native import NativeExec
from mcbench.native_skill_activation import NativeSkillSets
from strata_evaluator.probe_pairs import ProbePairs
from strata_evaluator.native_probe_views import ProbeNativeViews
from strata_evaluator.native_probe_bindings import ProbeNativeBindings
from strata_evaluator.probe_custody import ProbeCustody
v=json.loads(Path(sys.argv[2]).read_bytes())
db=Database(Path(v['db'])); cas=CAS(db,Path(v['objects']))
runtime=NativeExec(db,cas,simulation=True)
bindings=ProbeNativeBindings(ProbeNativeViews(ProbePairs(NativeSkillSets(runtime),'evaluation:test')))
held=ProbeCustody(bindings).acquire(Principal('evaluation:test','evaluator'),'p1',v['reservations'],
    worker='probe-worker',fingerprint='fixture-pins',per_arm_resources={'bodies':1,'memory_mib':128,'disk_bytes':1000000,'model_slots':3})
assert held.check()['state']=='HELD'
os._exit(87)
"""
    result=subprocess.run([sys.executable,"-I","-c",script,str(repo),str(config)],capture_output=True,text=True,
                          timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode==87,result.stderr
    assert state(service)=="HELD"
    assert reserved_resources(service.db.connection,"probe-worker")==CAPACITY
    assert service.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"]==200
    with pytest.raises(Fault,match="PROBE_CUSTODY_CONSUMED"):
        acquire(custody)
    target=tmp_path/"pair/copy-0/server/world/level.dat"
    target.write_bytes(target.read_bytes())  # OS released the dead owner's lease.
    assert state(service)=="HELD"  # A persisted row is never a new live handle.
    (tmp_path/"owner-death.json").write_bytes(canonical({"returncode":result.returncode,"stderr":result.stderr,
        "state":state(service),"resources":reserved_resources(service.db.connection,"probe-worker"),
        "budget_hold":200,"same_pair_reacquisition_refused":True,"dead_owner_file_handles_released":True}))


def test_wrong_principal_cannot_observe_or_allocate_pair(custody):
    service=custody[0]
    before=list(service.db.connection.iterdump())
    with pytest.raises(Fault,match="FORBIDDEN"):
        service.acquire(Principal("a1","executor"),"p1",custody[1],worker="probe-worker",
                        fingerprint="fixture-pins",per_arm_resources=PER_ARM)
    assert list(service.db.connection.iterdump())==before


def test_failed_physical_preflight_cannot_be_repaired_into_a_new_custody_attempt(custody,tmp_path):
    service=custody[0]
    path=tmp_path/"native/copy-0/body-0/workspace/active/revisions.json"
    raw=path.read_bytes()
    path.write_bytes(b"changed")
    with pytest.raises(Fault,match="CORRUPT_EVIDENCE"):
        acquire(custody)
    assert service.db.connection.execute("SELECT state FROM probe_native_views").fetchone()[0]=="FAILED"
    path.write_bytes(raw)
    with pytest.raises(Fault,match="PROBE_VIEWS_NOT_PREPARED"):
        acquire(custody)
    assert state(service) is None
    assert service.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"]==0


def test_wall_clock_rollback_does_not_extend_live_custody(custody):
    service=custody[0]
    monotonic=[100.0]
    service.monotonic=lambda:monotonic[0]
    acquire(custody)
    custody[3][0]-=1000
    monotonic[0]+=121
    with pytest.raises(Fault,match="PROBE_CUSTODY_EXPIRED"):
        service.check()
    assert state(service)=="FENCED"
    event=json.loads(service.db.connection.execute("SELECT body FROM outbox WHERE kind='probe.custody_fenced'").fetchone()[0])
    assert event["reason"]=="PROBE_CUSTODY_EXPIRED"
    assert reserved_resources(service.db.connection,"probe-worker")==CAPACITY
    assert service.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"]==200
