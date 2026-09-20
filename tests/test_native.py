"""Real process supervision with synthetic JSONL producers; no model execution."""

import base64
import json
import sys
import time

import pytest

from mcbench.budgets import DIMENSIONS
from mcbench.inventory import file_hash
from mcbench.native import NativeExec, NativeLaunch, native_argv
from mcbench.records import BudgetLedger
from mcbench.storage import Fault


@pytest.fixture
def runtime(database, cas):
    adapter = NativeExec(database, cas, simulation=True)
    adapter.budgets.create_account("a1", dict.fromkeys(DIMENSIONS, 100000), "c1", "a1",
                                  category="training")
    yield adapter
    for job in list(adapter.live):
        if job in adapter.live:
            adapter.interrupt(job, "test_cleanup")


@pytest.fixture
def make_plan(tmp_path, example):
    def make(job="job1", parent=None, role="executor", **updates):
        workspace, profile = tmp_path / (job + "-workspace"), tmp_path / (job + "-profile")
        workspace.mkdir(exist_ok=True)
        profile.mkdir(exist_ok=True)
        plan = NativeLaunch.model_validate({"schema": "strata/NativeLaunch/1", "job_id": job,
            "campaign_id": "c1", "agent_id": "a1", "epoch": 1, "role": role,
            "parent_job_id": parent, "depth": 1 if parent else 0, "account": "a1",
            "operation_id": job + "-call", "workspace": str(workspace),
            "profile_directory": str(profile), "executable": sys.executable,
            "binary_digest": file_hash(__import__("pathlib").Path(sys.executable)),
            "binary_version": "synthetic-python-producer", "dovetail_commit": "synthetic",
            "model": "synthetic-no-model", "config_overrides": {}, "environment": {},
            "prompt": "ordinary synthetic gameplay goal", "hard_timeout_s": 3,
            "output_limit_bytes": 1024 * 1024, "qualification_ref": None, **updates})
        body = example("BudgetLedger")
        reserve = BudgetLedger.model_validate(body | {"is_example": False, "posting": "reserve",
            "operation_id": plan.operation_id, "parent_operation_id": parent + "-call" if parent else None,
            "source_event_id": job + "-reserve", "kind": "helper" if parent else "model",
            "usage": body["usage"] | {"input_tokens": 1000, "output_tokens": 200,
                "spend_microusd": 100, "model_calls": 10, "reasoning_tokens": None}})
        return plan, reserve
    return make


def command(code):
    return [sys.executable, "-I", "-c", code]


def wait_end(runtime, job):
    until = time.monotonic() + 6
    while time.monotonic() < until:
        status = runtime.pump(job)
        if status["state"] != "RUNNING":
            return status
        time.sleep(0.01)
    raise AssertionError("fixture process did not end")


def test_native_exit_keeps_actual_unknown_and_duplicate_never_reexecutes(runtime, make_plan):
    plan, reserve = make_plan()
    events = [{"type": "thread.started", "thread_id": "fixture"}, {"type": "turn.started"},
              {"type": "turn.completed", "usage": {"input_tokens": 23,
                "cached_input_tokens": 3, "output_tokens": 5}}]
    code = "import json; events=" + repr(events) + "; [print(json.dumps(e)) for e in events]"
    fixture = command(code)
    assert runtime.start(plan, reserve, fixture_argv=fixture)["state"] == "RUNNING"
    assert wait_end(runtime, plan.job_id)["returncode"] == 0
    assert runtime.status(plan.job_id)["state"] == "UNSETTLED"
    captured = runtime.events(plan.job_id)
    assert [json.loads(base64.b64decode(e["body"]["raw_base64"])) for e in captured] == events
    assert runtime.budgets.status("a1")["uncertain"]
    assert runtime.usage_report(plan.job_id)["usage"]["input_tokens"] == 23
    assert runtime.usage_report(plan.job_id)["all_call_accounting_verified"] is False
    assert runtime.start(plan, reserve, fixture_argv=fixture)["state"] == "UNSETTLED"
    assert plan.job_id not in runtime.live
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        runtime.finalize(plan.job_id)
    settled = reserve.model_dump() | {"posting": "settle", "source_event_id": "provider-settled",
        "metering": "reported", "reason": "synthetic complete provider receipt"}
    runtime.budgets.post("a1", BudgetLedger.model_validate(settled))
    assert runtime.finalize(plan.job_id)["state"] == "FINALIZED"
    assert not runtime.budgets.status("a1")["uncertain"]


@pytest.mark.parametrize("code,reason", [
    ("print('not-json')", "runtime_event_invalid"),
    ("import sys; sys.stdout.write('{\"type\":\"turn.started\"}')", "runtime_event_invalid"),
    ("import sys; sys.stdout.buffer.write(bytes([255])+b'\\n')", "runtime_event_invalid"),
    ("print('x'*2048)", "runtime_output_quota"),
    ("import time; time.sleep(30)", "runtime_hard_timeout"),
])
def test_invalid_output_and_timeout_stop_and_keep_unsettled(runtime, make_plan, code, reason):
    plan, reserve = make_plan(hard_timeout_s=1, output_limit_bytes=1024)
    runtime.start(plan, reserve, fixture_argv=command(code))
    status = wait_end(runtime, plan.job_id)
    assert status["state"] == "UNSETTLED" and status["reason"].startswith(reason)
    assert runtime.budgets.status("a1")["uncertain"]


def test_revocation_before_kill_and_single_executor(runtime, make_plan):
    order = []
    plan, reserve = make_plan()
    runtime.revoke_game = lambda *scope: order.append(("revoke", scope))
    runtime.start(plan, reserve, fixture_argv=command("import time;time.sleep(30)"))
    managed = runtime.live[plan.job_id]["process"]
    original_stop = managed.stop
    def stop():
        order.append(("stop", None))
        original_stop()
    managed.stop = stop
    other, hold = make_plan("job2")
    with pytest.raises(Fault, match="EXECUTOR_BUSY"):
        runtime.start(other, hold, fixture_argv=command("print('must not run')"))
    runtime.interrupt(plan.job_id, "operator_stop")
    assert order[0] == ("revoke", ("c1", "a1", 1))
    assert managed.poll() is not None


def test_helpers_no_avatar_grant_distinct_boundary_limits_and_parent_shutdown(runtime, make_plan):
    parent, hold = make_plan()
    fixture = command("import time;time.sleep(30)")
    runtime.start(parent, hold, fixture_argv=fixture)
    child, reserve = make_plan("helper1", parent="job1", role="helper")
    with pytest.raises(Fault, match="HELPER_CANNOT_ACT"):
        runtime.start(child.model_copy(update={"environment": {"STRATA_GAME_GRANT": "own.json"}}),
                      reserve, fixture_argv=fixture)
    with pytest.raises(Fault, match="HELPER_BOUNDARY_MISMATCH"):
        runtime.start(child.model_copy(update={"workspace": parent.workspace}), reserve,
                      fixture_argv=fixture)
    runtime.start(child, reserve, fixture_argv=fixture)
    grandchild, reserve2 = make_plan("helper2", parent="helper1", role="helper", depth=2)
    runtime.start(grandchild, reserve2, fixture_argv=fixture)
    another, reserve3 = make_plan("helper3", parent="job1", role="helper")
    with pytest.raises(Fault, match="HELPER_CAPACITY"):
        runtime.start(another, reserve3, fixture_argv=fixture)
    runtime.interrupt("job1", "end_episode")
    assert runtime.live == {}
    assert all(runtime.status(j)["state"] == "UNSETTLED" for j in ("job1", "helper1", "helper2"))


def test_failure_to_revoke_still_kills_process_and_holds_budget(runtime, make_plan):
    plan, reserve = make_plan()
    runtime.start(plan, reserve, fixture_argv=command("import time;time.sleep(30)"))
    process = runtime.live[plan.job_id]["process"]
    def broken(*_):
        raise RuntimeError("synthetic failed gateway")
    runtime.revoke_game = broken
    with pytest.raises(Fault, match="CLEANUP_FAILED|REVOCATION_FAILED"):
        runtime.interrupt(plan.job_id, "stop")
    assert process.poll() is not None and plan.job_id not in runtime.live
    assert runtime.status(plan.job_id)["state"] == "UNSETTLED"
    assert runtime.budgets.status("a1")["uncertain"]


def test_live_gate_rejects_fixture_and_missing_qualification(database, cas, make_plan):
    runtime = NativeExec(database, cas, revoke_game=lambda *_: None)
    plan, reserve = make_plan()
    with pytest.raises(Fault, match="FORBIDDEN"):
        runtime.start(plan, reserve, fixture_argv=command("print('no')"))
    from mcbench.runtime import CODEX_VERSION, DOVETAIL_COMMIT
    plan = plan.model_copy(update={"binary_version": CODEX_VERSION, "dovetail_commit": DOVETAIL_COMMIT})
    with pytest.raises(Fault, match="RUNTIME_UNQUALIFIED"):
        runtime.start(plan, reserve)
    with pytest.raises(Fault, match="SIMULATION_STORE"):
        NativeExec(database, cas, simulation=True)


def test_conformance_bootstrap_requires_safety_billing_and_cannot_admit_a_campaign(
        database, cas, make_plan):
    from mcbench.native import CONFORMANCE_PREREQUISITES
    from mcbench.storage import Principal, canonical, digest
    runtime = NativeExec(database, cas, revoke_game=lambda *_: None)
    plan, reserve = make_plan(purpose="conformance")
    principal = Principal("operator", "operator")

    def evidence(checks, purpose="conformance"):
        refs = {}
        for check in checks:
            item = {"result": "pass", "is_example": False, "check": check,
                    "profile_digest": plan.profile_digest(), "workspace": plan.workspace,
                    "profile_directory": plan.profile_directory, "role": plan.role,
                    "environment_digest": digest(plan.environment), "currency": "USD",
                    "auth_mode": "chatgpt_oauth", "pricing_semantics_verified": True,
                    "finite_dispatch_bound_verified": True}
            refs[check] = cas.put(principal, "operator", "operator", canonical(item))
        return cas.put(principal, "operator", "operator", canonical({
            "schema": "strata/RuntimeQualification/1", "is_example": False,
            "purpose": purpose, "profile_digest": plan.profile_digest(),
            "expires_unix": time.time() + 60, "checks": refs}))

    # Synthetic attestation parser checks only. This fixture does not start any process.
    ref = evidence(CONFORMANCE_PREREQUISITES)
    runtime._proof(plan.model_copy(update={"qualification_ref": ref}))
    for omitted in CONFORMANCE_PREREQUISITES:
        partial = evidence(CONFORMANCE_PREREQUISITES - {omitted})
        with pytest.raises(Fault, match="RUNTIME_UNQUALIFIED"):
            runtime._proof(plan.model_copy(update={"qualification_ref": partial}))
    with pytest.raises(Fault, match="RUNTIME_UNQUALIFIED"):
        runtime._proof(plan.model_copy(update={"purpose": "campaign", "qualification_ref": ref}))
    with pytest.raises(Fault, match="CONFORMANCE_ACCOUNT_REQUIRED"):
        runtime.start(plan, reserve)
    assert runtime.live == {}


def test_arguments_keep_native_loop_and_stdin_prompt(make_plan):
    plan, _ = make_plan(config_overrides={"model_reasoning_effort": "low"})
    argv = native_argv(plan)
    assert argv[1] == "exec" and argv[-1] == "-"
    assert plan.prompt not in argv
    assert {"--json", "--ignore-user-config", "--ignore-rules", "--ephemeral"} <= set(argv)
    assert '--dangerously-bypass-approvals-and-sandbox' not in argv


def settle(runtime, reserve):
    record = reserve.model_dump() | {"posting": "settle",
        "source_event_id": reserve.operation_id + "-settled", "metering": "reported"}
    runtime.budgets.post("a1", BudgetLedger.model_validate(record))


def test_export_fresh_handoff_resume_epoch_cost_and_artifact_authorization(runtime, make_plan, cas):
    from mcbench.storage import Principal
    plan, reserve = make_plan()
    fixture = command("print('{\"type\":\"turn.started\"}')")
    runtime.start(plan, reserve, fixture_argv=fixture)
    wait_end(runtime, plan.job_id)
    with pytest.raises(Fault, match="RUNTIME_NOT_QUIESCENT"):
        runtime.export_state(plan.job_id, workspace_ref="no", skills_ref="no", handoff_ref=None,
                             artifact_namespace="campaign:c1:agent:a1")
    settle(runtime, reserve)
    runtime.finalize(plan.job_id)
    namespace = "campaign:c1:agent:a1"
    principal = Principal(namespace, "executor")
    workspace = cas.put(principal, namespace, "agent", b"synthetic admitted workspace manifest")
    handoff = cas.put(principal, namespace, "agent", b"Resume from the public village.")
    state = runtime.export_state(plan.job_id, workspace_ref=workspace, skills_ref=workspace,
                                 handoff_ref=handoff, artifact_namespace=namespace)
    with pytest.raises(Fault, match="FORBIDDEN"):
        runtime.export_state(plan.job_id, workspace_ref=workspace, skills_ref=workspace,
                             handoff_ref=handoff, artifact_namespace="campaign:c2:agent:a2")
    with pytest.raises(Fault, match="FORBIDDEN"):
        runtime.export_state(plan.job_id, workspace_ref=workspace, skills_ref=workspace,
                             handoff_ref=handoff, artifact_namespace="campaign:c2:agent:a1")
    new_plan, new_reserve = make_plan("resumed")
    with pytest.raises(Fault, match="STALE_STATE"):
        runtime.resume(state, new_plan, new_reserve, fixture_argv=fixture)
    new_plan = new_plan.model_copy(update={"epoch": 2})
    new_reserve = new_reserve.model_copy(update={"epoch": 2})
    with pytest.raises(Fault, match="HANDOFF_MISSING"):
        runtime.resume(state, new_plan, new_reserve, fixture_argv=fixture)
    new_plan = new_plan.model_copy(update={"prompt": "Resume from the public village."})
    before = runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"]
    runtime.resume(state, new_plan, new_reserve, fixture_argv=fixture)
    wait_end(runtime, new_plan.job_id)
    assert runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == before + 100


def test_crashed_owner_requires_explicit_fencing_and_never_replays(runtime, make_plan, cas):
    from mcbench.storage import Principal, canonical
    plan, reserve = make_plan()
    fixture = command("import time;time.sleep(30)")
    runtime.start(plan, reserve, fixture_argv=fixture)
    live = runtime.live.pop(plan.job_id)
    live["process"].stop()
    for thread in live["threads"]:
        thread.join(timeout=1)
    live["process"].close()
    # Durable status survived; a new owner has no license to launch that ID again.
    replacement = NativeExec(runtime.db, cas, simulation=True)
    assert replacement.start(plan, reserve, fixture_argv=fixture)["state"] == "RUNNING"
    assert replacement.live == {}
    proof = {"schema": "strata/RuntimeFenced/1", "is_example": True, "job_id": plan.job_id,
             "epoch": 1, "process_tree_dead": True, "game_grants_revoked": False}
    ref = cas.put(Principal("operator", "operator"), "operator", "operator", canonical(proof))
    with pytest.raises(Fault, match="FENCING_UNVERIFIED"):
        replacement.recover_fenced(plan.job_id, ref)
    proof["game_grants_revoked"] = True
    ref = cas.put(Principal("operator", "operator"), "operator", "operator", canonical(proof))
    assert replacement.recover_fenced(plan.job_id, ref)["state"] == "UNSETTLED"
    assert replacement.budgets.status("a1")["uncertain"]


def test_failed_child_revocation_still_stops_all_siblings(runtime, make_plan):
    fixture = command("import time;time.sleep(30)")
    plans = [make_plan(), make_plan("h1", parent="job1", role="helper"),
             make_plan("h2", parent="job1", role="helper")]
    for plan, reserve in plans:
        runtime.start(plan, reserve, fixture_argv=fixture)
    processes = [entry["process"] for entry in runtime.live.values()]
    def fail(*_):
        raise RuntimeError("synthetic gateway failure")
    runtime.revoke_game = fail
    with pytest.raises(Fault, match="CLEANUP_FAILED"):
        runtime.interrupt("job1", "stop")
    assert not runtime.live
    assert all(process.poll() is not None for process in processes)


def test_journal_write_failure_fences_process_before_propagating(runtime, make_plan):
    plan, reserve = make_plan()
    runtime.start(plan, reserve, fixture_argv=command("print('{\"type\":\"turn.started\"}')"))
    managed = runtime.live[plan.job_id]["process"]
    original = runtime._event
    def fail(*_):
        raise OSError("synthetic disk full")
    runtime._event = fail
    try:
        with pytest.raises(OSError, match="disk full"):
            wait_end(runtime, plan.job_id)
    finally:
        runtime._event = original
    assert managed.poll() is not None
    assert plan.job_id not in runtime.live
    assert runtime.budgets.status("a1")["uncertain"]
