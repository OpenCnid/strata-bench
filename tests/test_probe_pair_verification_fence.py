"""Real controller-process exits with synthetic source/world records; no model/game."""

import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from mcbench.storage import Fault, Principal, canonical
from test_probe_pairs import EVALUATOR, pair_source as _pair_source

pair_source = _pair_source


def state(service):
    return service.db.connection.execute("SELECT state FROM probe_pair_staging WHERE id='p1'").fetchone()[0]


def events(service):
    return [r[0] for r in service.db.connection.execute(
        "SELECT kind FROM outbox WHERE kind LIKE 'probe.pair_%' ORDER BY cursor")]


def test_failed_check_cannot_be_repaired_into_a_reusable_pair(pair_source, tmp_path):
    service, request, _, runtime = pair_source
    before = runtime.budgets.status("a1")
    target = tmp_path / "pair"
    plan = service.prepare(EVALUATOR, request(), target)
    path = target / plan["arm_directories"]["initial"] / "server/world/level.dat"
    original = path.read_bytes()
    path.write_bytes(b"changed fixture")
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE|MIXED_SNAPSHOT"):
        service.verify(EVALUATOR, "p1")
    assert state(service) == "FAILED"
    path.write_bytes(original)
    with pytest.raises(Fault, match="PROBE_PAIR_NOT_PREPARED"):
        service.verify(EVALUATOR, "p1")
    with pytest.raises(Fault, match="PROBE_INSTANCE_CONSUMED"):
        service.prepare(EVALUATOR, request(pair_id="p2"), tmp_path / "replacement")
    assert events(service)[-2:] == ["probe.pair_verifying", "probe.pair_verification_failed"]
    assert "probe.pair_verified" not in events(service)
    assert runtime.budgets.status("a1") == before


@pytest.mark.parametrize("fault", [OSError, KeyboardInterrupt])
def test_verification_intent_commits_before_source_read_and_fault_keeps_evidence(
        pair_source, tmp_path, monkeypatch, fault):
    service, request, _, _ = pair_source
    service.prepare(EVALUATOR, request(), tmp_path / "pair")
    original_plan = service.db.connection.execute("SELECT plan FROM probe_pair_staging").fetchone()[0]
    def failed(*_):
        with sqlite3.connect(service.db.path.as_uri() + "?mode=ro", uri=True) as reader:
            assert reader.execute("SELECT state FROM probe_pair_staging").fetchone()[0] == "VERIFYING"
            assert reader.execute("SELECT count(*) FROM outbox WHERE kind='probe.pair_verifying'").fetchone()[0] == 1
        raise fault("interrupted source inspection")
    monkeypatch.setattr(service, "_derive", failed)
    with pytest.raises(fault, match="interrupted source inspection"):
        service.verify(EVALUATOR, "p1")
    assert state(service) == "FAILED"
    assert service.db.connection.execute("SELECT plan FROM probe_pair_staging").fetchone()[0] == original_plan
    assert (tmp_path / "pair/pair.json").is_file()


def test_unknown_pair_and_unauthorized_caller_cannot_poison_prepared_state(pair_source, tmp_path):
    service, request, _, _ = pair_source
    expected = service.prepare(EVALUATOR, request(), tmp_path / "pair")
    before = events(service)
    for caller in (Principal("evaluation:other", "evaluator"), Principal("a1", "executor"),
                   Principal("a1", "helper")):
        with pytest.raises(Fault, match="FORBIDDEN"):
            service.verify(caller, "p1")
    with pytest.raises(Fault, match="PROBE_PAIR_NOT_PREPARED"):
        service.verify(EVALUATOR, "missing")
    assert events(service) == before and state(service) == "PREPARED"
    assert service.verify(EVALUATOR, "p1") == expected
    assert service.verify(EVALUATOR, "p1") == expected
    assert events(service)[-4:] == ["probe.pair_verifying", "probe.pair_verified"] * 2
    assert not expected["dispatch_authorized"]


def test_failed_intent_commit_does_not_inspect_or_change_pair(pair_source, tmp_path, monkeypatch):
    service, request, _, _ = pair_source
    service.prepare(EVALUATOR, request(), tmp_path / "pair")
    service.db.connection.execute("CREATE TRIGGER fail_verifying BEFORE INSERT ON outbox "
        "WHEN NEW.kind='probe.pair_verifying' BEGIN SELECT RAISE(ABORT,'synthetic journal full'); END")
    def forbidden(*_):
        pytest.fail("source read after failed intent commit")
    monkeypatch.setattr(service, "_derive", forbidden)
    with pytest.raises(sqlite3.IntegrityError, match="synthetic journal full"):
        service.verify(EVALUATOR, "p1")
    assert state(service) == "PREPARED"
    assert "probe.pair_verifying" not in events(service)


def test_failed_failure_journal_leaves_unusable_verifying_intent(pair_source, tmp_path, monkeypatch):
    service, request, _, _ = pair_source
    service.prepare(EVALUATOR, request(), tmp_path / "pair")
    service.db.connection.execute("CREATE TRIGGER fail_failure BEFORE INSERT ON outbox "
        "WHEN NEW.kind='probe.pair_verification_failed' BEGIN SELECT RAISE(ABORT,'synthetic journal full'); END")
    def failed(*_):
        raise OSError("synthetic read failure")
    monkeypatch.setattr(service, "_check", failed)
    with pytest.raises(sqlite3.IntegrityError, match="synthetic journal full"):
        service.verify(EVALUATOR, "p1")
    assert state(service) == "VERIFYING"
    with pytest.raises(Fault, match="PROBE_PAIR_NOT_PREPARED"):
        service.verify(EVALUATOR, "p1")
    assert events(service)[-1] == "probe.pair_verifying"


# Each child opens the actual shared controller/CAS, then bypasses every Python
# finalizer at a known boundary. This is process death, not a power-loss test.
CRASH_CHILD = """
import json, os, sys
from pathlib import Path
from mcbench.storage import CAS, Database, Principal
from mcbench.native import NativeExec
from mcbench.native_skill_activation import NativeSkillSets
from strata_evaluator.probe_pairs import ProbePairs
args = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
db = Database(Path(args['database']))
cas = CAS(db, Path(args['cas']))
service = ProbePairs(NativeSkillSets(NativeExec(db, cas, simulation=True)), args['namespace'])
principal = Principal(args['namespace'], 'evaluator')
def crash():
    with Path(args['marker']).open('x', encoding='utf-8') as stream:
        stream.write(args['mode'])
        stream.flush()
        os.fsync(stream.fileno())
    os._exit(83)
if args['mode'] == 'preparing':
    original = cas.copy_to
    def copy_then_die(*args, **kwargs):
        original(*args, **kwargs)
        crash()
    cas.copy_to = copy_then_die
    service.prepare(principal, args['request'], Path(args['target']))
else:
    def check_then_die(*args):
        service._check_original(*args)
        crash()
    service._check_original = service._check
    service._check = check_then_die
    service.verify(principal, 'p1')
raise AssertionError('crash boundary was not reached')
"""


@pytest.mark.parametrize("mode", ["preparing", "verifying"])
def test_abrupt_controller_process_death_never_rearms_fixture(pair_source, tmp_path, mode):
    service, request, _, runtime = pair_source
    target, marker = tmp_path / "pair", tmp_path / "crash-marker"
    before = runtime.budgets.status("a1")
    if mode == "verifying":
        service.prepare(EVALUATOR, request(), target)
    args = {"database": str(service.db.path), "cas": str(service.cas.root), "namespace": EVALUATOR.namespace,
        "target": str(target), "request": request(), "marker": str(marker), "mode": mode}
    input_path = tmp_path / "crash-input.json"
    input_path.write_bytes(canonical(args))
    root = Path(__file__).resolve().parents[1]
    env = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "LANG"}}
    env["PYTHONPATH"] = os.pathsep.join(str(root / p) for p in ("src", "evaluator/src"))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run([sys.executable, "-c", CRASH_CHILD, str(input_path)],
        cwd=tmp_path, env=env, capture_output=True, timeout=30)
    assert result.returncode == 83, result.stderr.decode(errors="replace")
    assert marker.read_text() == mode
    assert state(service) == mode.upper()
    assert events(service)[-1] == "probe.pair_" + mode
    assert "probe.pair_verified" not in events(service)
    if mode == "preparing":
        assert len([p for p in target.rglob("*") if p.is_file()]) == 1
    else:
        assert (target / "pair.json").is_file()
    from mcbench.storage import CAS, Database
    from mcbench.native import NativeExec
    from mcbench.native_skill_activation import NativeSkillSets
    from strata_evaluator.probe_pairs import ProbePairs
    reopened_db = Database(service.db.path)
    try:
        reopened = ProbePairs(NativeSkillSets(NativeExec(reopened_db, CAS(reopened_db, service.cas.root),
            simulation=True)), EVALUATOR.namespace)
        with pytest.raises(Fault, match="PROBE_PAIR_NOT_PREPARED"):
            reopened.verify(EVALUATOR, "p1")
        with pytest.raises(Fault, match="PROBE_INSTANCE_CONSUMED"):
            reopened.prepare(EVALUATOR, request(pair_id="p2", fixture_patch={"instance_id": "i2"}),
                             tmp_path / "replacement")
        assert state(reopened) == mode.upper()
    finally:
        reopened_db.close()
    assert runtime.budgets.status("a1") == before
    assert not (tmp_path / "replacement").exists()
