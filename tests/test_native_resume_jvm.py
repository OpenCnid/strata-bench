"""Real JVM/HTTP resume and status recovery; synthetic body and verification only."""
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.native_resume import NativeResumeDecision
from mcbench.native_restart import NativeRestartCheckpoint, NativeRestartRequest
from mcbench.native_settings_effects import EffectOutcomeUnknown
from test_native_commit import decision as commit_decision
from test_native_repair_admission_jvm import admission
from test_native_settings_effects_jvm import effects_jvm as _effects_jvm

effects_jvm = _effects_jvm


def request(client, plan, phase):
    head = client.call("settings_snapshot", {})
    identity = NativeGameClient(client.connection).call("identity", {})
    return NativeResumeDecision.model_validate({"schema": "strata/NativeSettingsResumeDecision/1",
        "policy": "operator-owned-settings-resume/1", "resume_id": "resume-1", "worker_plan": plan.worker_plan.model_dump(),
        "expected_revision": head["revision"], "expected_digest": head["digest"], "completion_phase": phase,
        "verification_ref": "cas:sha256:" + "c" * 64, "connection_generation": identity["connection_generation"],
        "lease_until_unix_ms": min(int(time.time() * 1000) + 5000, plan.worker_plan.expires_unix_ms)})


def finish_settings(client, plan, phase):
    if phase == "committed":
        head = client.call("settings_snapshot", {})
        commit = commit_decision(head["revision"], head["digest"], plan.worker_plan.plan_digest)
        commit = commit.model_copy(update={"verification_ref": "cas:sha256:" + "c" * 64})
        client.call("settings_commit", commit.model_dump(), timeout_ms=1000)
    else:
        client.call("settings_rollback", {"transaction_id": "tx"}, timeout_ms=1000)


@pytest.mark.parametrize("phase", ["committed", "rolled_back"])
def test_lost_resume_reply_status_and_reopen_do_not_repeat_authority(effects_jvm, monkeypatch, phase):
    with effects_jvm(repair_owner=True, commit_owner=True, resume_owner=True) as (client, process, profile, game_root):
        plan = admission(client, 15000)
        client.call("settings_repair_bind", plan.model_dump(), timeout_ms=1000)
        client.call("settings_apply", plan.patch.model_dump(), timeout_ms=1000)
        finish_settings(client, plan, phase)
        req = request(client, plan, phase)
        original = client._result
        def lose(operation, *args, **kwargs):
            value = original(operation, *args, **kwargs)
            if operation == "settings_resume":
                raise TimeoutError("synthetic reply loss after actual native resume")
            return value
        monkeypatch.setattr(client, "_result", lose)
        with pytest.raises(EffectOutcomeUnknown) as error:
            client.call("settings_resume", req.model_dump(), timeout_ms=1000)
        assert error.value.transaction_id == "tx"
        state = client.call("settings_resume_status", {"transaction_id": "tx"}, expected_resume=req)
        assert state["input_resumed"] is True and state["health"]["epoch"] == 1
        charged = state["health"]["attempted_primitive_events"]
        assert client.call("settings_resume_status", {"transaction_id": "tx"}, expected_resume=req)["health"]["attempted_primitive_events"] == charged
        game = NativeGameClient(client.connection)
        game.call("stop_all", {})
        assert client.call("settings_resume_status", {"transaction_id": "tx"}, expected_resume=req)["input_resumed"] is False
        rows = [json.loads(line)["payload"] for line in (game_root / "game-actions.jsonl").read_text().splitlines()]
        assert sum(row["kind"] == "repair_resumed" for row in rows) == 1
    assert process.poll() == 0
    with effects_jvm(repair_owner=True, commit_owner=True, resume_owner=True) as (client, _, _, _):
        state = client.call("settings_resume_status", {"transaction_id": "tx"}, expected_resume=req)
        assert state["source_instance"] != state["current_instance"] and state["input_resumed"] is False
        assert client.call("settings_resume", req.model_dump())["input_resumed"] is False


def test_resume_after_real_jvm_replacement_uses_original_plan(effects_jvm):
    with effects_jvm(repair_owner=True, commit_owner=True, restart_owner=True, resume_owner=True) as (client, first, _, _):
        plan = admission(client, 15000)
        client.call("settings_repair_bind", plan.model_dump(), timeout_ms=1000)
        client.call("settings_apply", plan.patch.model_dump(), timeout_ms=1000)
        head = client.call("settings_snapshot", {})
        restart = NativeRestartRequest.model_validate({"schema": "strata/NativeSettingsRestartRequest/1",
            "transaction_id": "tx", "plan_digest": plan.worker_plan.plan_digest, "restart_id": "restart-1",
            "expected_revision": head["revision"], "expected_digest": head["digest"]})
        checkpoint = NativeRestartCheckpoint.model_validate(client.call("settings_restart_prepare", restart.model_dump())["checkpoint"])
    assert first.poll() == 0
    with effects_jvm(repair_owner=True, commit_owner=True, restart_owner=True, resume_owner=True) as (client, _, _, _):
        client.call("settings_restart_continue", checkpoint.model_dump(), timeout_ms=1000)
        finish_settings(client, plan, "committed")
        req = request(client, plan, "committed")
        state = client.call("settings_resume", req.model_dump(), timeout_ms=1000)
        assert state["input_resumed"] is True and state["decision"]["worker_plan"]["expires_unix_ms"] == plan.worker_plan.expires_unix_ms


@pytest.mark.parametrize("fault", ["unfinished", "head", "verification", "generation", "stopped", "mode"])
def test_resume_refusals_keep_native_input_fenced(effects_jvm, fault):
    with effects_jvm(repair_owner=True, commit_owner=True, resume_owner=fault != "mode") as (client, _, _, game_root):
        plan = admission(client, 15000)
        client.call("settings_repair_bind", plan.model_dump(), timeout_ms=1000)
        client.call("settings_apply", plan.patch.model_dump(), timeout_ms=1000)
        if fault != "unfinished":
            finish_settings(client, plan, "committed")
        req = request(client, plan, "committed")
        if fault == "head":
            req = req.model_copy(update={"expected_revision": req.expected_revision + 1})
        if fault == "verification":
            req = req.model_copy(update={"verification_ref": "cas:sha256:" + "f" * 64})
        if fault == "generation":
            req = req.model_copy(update={"connection_generation": req.connection_generation + 1})
        game = NativeGameClient(client.connection)
        if fault == "stopped":
            game.call("stop_all", {})
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_resume", req.model_dump(), timeout_ms=1000)
        assert game.call("lane_status", {})["fenced"] is True
        rows = [json.loads(line)["payload"] for line in (game_root / "game-actions.jsonl").read_text().splitlines()]
        assert not any(row["kind"] == "repair_resumed" for row in rows)


def test_compiled_node_transport_resumes_actual_jvm_without_new_epoch(effects_jvm, tmp_path):
    node = os.environ.get("STRATA_CLIENT_TEST_NODE")
    if not node:
        pytest.skip("explicit pinned Node required")
    with effects_jvm(repair_owner=True, commit_owner=True, resume_owner=True) as (client, _, _, _):
        plan = admission(client, 15000)
        client.call("settings_repair_bind", plan.model_dump(), timeout_ms=1000)
        client.call("settings_apply", plan.patch.model_dump(), timeout_ms=1000)
        finish_settings(client, plan, "committed")
        req = request(client, plan, "committed")
        module = (Path(__file__).resolve().parents[1] / "backends/mineflayer/dist/src/native_game.js").as_uri()
        script = tmp_path / "resume.mjs"
        script.write_text(f"import {{ NativeGameClient }} from {json.dumps(module)};\n" + """
let raw='';for await(const chunk of process.stdin)raw+=chunk;
const input=JSON.parse(raw),client=new NativeGameClient(input.connection);
const resumed=await client.call('settings_resume',input.decision,1000);
const status=await client.call('settings_resume_status',{transaction_id:input.decision.worker_plan.transaction_id},1000);
process.stdout.write(JSON.stringify({resumed,status}));
""", encoding="utf-8")
        connection = client.connection.model_dump(mode="json")
        connection["bearer_token"] = client.connection.bearer_token.get_secret_value()
        run = subprocess.run([node, str(script)], input=json.dumps({"connection": connection, "decision": req.model_dump()}),
            text=True, capture_output=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        assert run.returncode == 0, "compiled Node transport failed"
        result = json.loads(run.stdout)
        assert result["resumed"]["input_resumed"] is result["status"]["input_resumed"] is True
        assert result["resumed"]["health"]["epoch"] == 1
        assert result["resumed"]["decision"] == req.model_dump()
