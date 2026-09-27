"""Actual controller/worker/guardian/JVM replacement; synthetic body and verification producer."""

import json
import http.client
import sqlite3
from urllib.parse import urlsplit
from datetime import datetime, timezone
import copy
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.native_resume import NativeResumeDecision
from mcbench.worker_publication import WorkerPublicationClient, WorkerControlPublication, WorkerRepairAccounting
from mcbench.native_settings_effects import EffectRequest
from mcbench.native_repair_restart import NativeRepairRestart
from mcbench.native_repair_resume import NativeRepairResume
from mcbench.worker_resume import WorkerResumeClient, WorkerResumeUnknown
from mcbench.worker_restart import WorkerRestartClient, WorkerRestartUnknown
from mcbench.native_settings_effects import EffectOutcomeUnknown
from mcbench.storage import Fault
from test_native_repair_flow import verification
from mcbench.native_effect_evidence import NativeEffectEvidence
from mcbench.native_essential_plan import NativeEssentialInputs
from mcbench.native_control_plan import FIXED_ESCAPE
from mcbench.native_repair_flow import NativeRepairFlow
from mcbench.native_settings_projection import NativeSettingsProjection
from test_native_settings_projection import qualified_fixture
from test_storage_controller import start
from mcbench.storage import canonical, digest
from mcbench.worker_repair import WorkerRepairClient
from test_native_control_plan import prepare, target_for
from test_native_settings_effects_jvm import ID, ORIGINAL, effects_jvm as _effects_jvm, terminal
from test_reconfiguration import repair_env as _repair_env

effects_jvm, repair_env = _effects_jvm, _repair_env


@pytest.mark.parametrize("repair_env", ["real-clock"], indirect=True)
@pytest.mark.parametrize("lost", [None, "prepare", "detach", "attach", "resume", "resume_lost", "publish"])
def test_controller_adopts_replacement_and_finishes_native_writes_without_replay(effects_jvm, repair_env, tmp_path, monkeypatch, lost, example):
    resuming = lost in {"resume", "resume_lost", "publish"}
    node = os.environ.get("STRATA_CLIENT_TEST_NODE")
    if os.name != "nt" or not node:
        pytest.skip("explicit pinned Node and Windows guardian required")
    worker_js = Path(__file__).resolve().parents[1] / "backends/mineflayer/dist/src/worker.js"
    def run(args):
        return subprocess.run(args, check=True, capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    capability = json.loads(run([node, str(worker_js), "--forge-capabilities", "a" * 64]).stdout)["digest"]
    e = repair_env
    # Declare a G/G conflict before creating the fixture's first native store.
    options = ORIGINAL.replace("key_key.inventory:key.keyboard.e", "key_key.inventory:key.keyboard.g")
    if lost is None:
        options += "key_key.forward:key.keyboard.w\r\nkey_key.sprint:key.keyboard.left.control\r\n"
    with effects_jvm(repair_owner=True, commit_owner=True, restart_owner=True, resume_owner=resuming, capability_digest=capability, scope=("c1", "a1"), options_text=options) as (client, game, profile, game_root):
        if lost is None:
            # Real HTTP state drives the controller plan. Qualification reports
            # and the remaining generic essential proof are explicitly synthetic.
            q = qualified_fixture(client.call("settings_snapshot", {}), client,
                profile=e.adapter.state["profile_id"], clock=time.time)
            (tmp_path / "qualification-fixture.json").write_text(json.dumps(
                {ref: raw.decode() for ref, raw in q.data.items()}, indent=2), encoding="utf-8")
            e.controls.adapter = q.projection
            e.repairs.configure("c1", "owner", e.epoch, e.put(e.policy))
            start(e.controller, e.config, e.epoch)
            e.controls.plan("a1", "tx", [ID])
            e.budget()
        else:
            prepare(e, ids=(ID, "minecraft:key.inventory:0"), initial=(71, "g"), replacement=(302, "f13"))
        lease = e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"]
        descriptor = tmp_path / "connection-1.json"
        identity = json.loads(run([sys.executable, "-I", "-m", "mcbench.process_guard", "--inspect", str(game.pid)]).stdout)
        guard, config, state = tmp_path / "guard.json", tmp_path / "worker.json", tmp_path / "worker-state"
        state.mkdir()
        guard.write_bytes(canonical({"schema": "strata/ForgeProcessGuardGrant/2", "shutdown_policy": "java-tree1000-lease750/1",
            "purpose": "dedicated-development-client-lifetime", "campaign_id": "c1", "agent_id": "a1",
            "epoch": e.epoch, "process": identity, "expires_unix_ms": int(time.time() * 1000) + 60000, "max_wall_ms": 25000,
            "connection_file": str(descriptor), "connection_digest": digest(json.loads(descriptor.read_text())),
            "native_fingerprint": "a" * 64, "body_fingerprint": "b" * 64, "capability_digest": capability, "primitive_limit": 1000}))
        config.write_bytes(canonical({**({"schema": "strata/ForgeDevelopmentWorker/6" if lost == "publish" else "strata/ForgeDevelopmentWorker/5", "resume_policy": "operator-owned-settings-resume/1", **({"publication_policy": "verified-controls-after-settlement/1"} if lost == "publish" else {})} if resuming else {"schema": "strata/ForgeDevelopmentWorker/4"}), "restart_policy": "operator-owned-client-replacement/1", "repair_policy": "operator-owned-fixed-repair-pause/1",
            "purpose": "manual-conformance", "server_kind": "e9e", "backend": "forge_client", "pack_version": "1.27.0",
            "connection_file": str(descriptor), "native_fingerprint": "a" * 64, "body_fingerprint": "b" * 64,
            "state_directory": str(state), "max_wall_ms": 20000, "primitive_limit": 1000,
            "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch, "lease_id": lease,
            "process_guard_file": str(guard), "guard_python": sys.executable}))
        parent = subprocess.Popen([node, str(worker_js), str(config), "--operator-stop"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            grant = state / f"repair-grant-{e.epoch}.json"
            until = time.monotonic() + 8
            while not grant.exists() and time.monotonic() < until:
                assert parent.poll() is None
                e.controller.heartbeat("c1", "owner", e.epoch)
                time.sleep(0.02)
            assert grant.exists()
            worker = WorkerRepairClient.from_file(grant)
            if lost == "publish":
                public_grant = state / f"grant-{e.epoch}.json"
                while not public_grant.exists() and time.monotonic() < until:
                    time.sleep(.01)
                initial = subprocess.run([node, str(worker_js.with_name("cli.js")), "look-at", "--x", "1", "--y", "65", "--z", "2", "--json"],
                    capture_output=True, timeout=3, creationflags=subprocess.CREATE_NO_WINDOW,
                    env=os.environ | {"STRATA_GAME_GRANT": str(public_grant)})
                assert initial.returncode in (0, 2), initial.stderr
                initial_ack = json.loads(initial.stdout)["result"]
                assert initial_ack["status"] == "accepted" and initial_ack["action_seq"] == 1
                native_game = NativeGameClient(client.connection)
                until = time.monotonic() + 2
                while True:
                    outcome = native_game.call("action_status", {"request_id": initial_ack["request_id"]})
                    if outcome["status"] not in {"accepted", "executing"} or time.monotonic() > until:
                        break
                    time.sleep(.01)
                assert outcome["status"] == "emitted" and outcome["release_confirmed"]
                # Native completion precedes the worker's observation/charge
                # join. The preplay baseline must include that terminal receipt.
                until = time.monotonic() + 2
                while True:
                    settled = subprocess.run([node, str(worker_js.with_name("cli.js")), "action-status",
                        "--request-id", initial_ack["request_id"], "--json"], capture_output=True, timeout=3,
                        creationflags=subprocess.CREATE_NO_WINDOW, env=os.environ | {"STRATA_GAME_GRANT": str(public_grant)})
                    assert settled.returncode in (0, 2), settled.stdout
                    preplay = json.loads(settled.stdout)["result"]
                    if preplay["status"] not in {"accepted", "executing"} or time.monotonic() > until:
                        break
                assert preplay["status"] == "emitted" and preplay["release_confirmed"]
                (tmp_path / "initial-worker-terminal.json").write_bytes(canonical(preplay))
            e.controller.heartbeat("c1", "owner", e.epoch)
            e.repairs.request("c1", "owner", e.epoch, "tx", "a1", "repair-op", deadline_unix=time.time() + 15)
            target = target_for(e, client)
            if lost is None:
                target = q.projection.target()
            receipt = e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
            plan = receipt["admission"]
            flow = NativeRepairFlow(e.repairs)
            assert flow.apply("tx", "owner", e.epoch, worker, client)["control"]["phase"] == "verifying"
            producer = NativeEffectEvidence(e.repairs)
            expectations = []
            if lost is None:
                head = client.call("settings_snapshot", {})
                for i, slot in enumerate(e.controls.status("tx")["plan"]["binding_checks"]):
                    selected = slot["binding_id"] == ID and slot["stage"] == "after_restart"
                    req = EffectRequest(id="after" if selected else "declared-" + str(i), transaction_id="tx",
                        expected_revision=head["revision"], expected_digest=head["digest"],
                        plan_digest=plan["worker_plan"]["plan_digest"], binding_id=slot["binding_id"],
                        context=slot["context"], stage=slot["stage"], hold_ms=1250 if selected else 50, settle_ticks=2)
                    expectations.append({"schema": "strata/NativeEffectExpectation/1", "request": req.model_dump(),
                        "settings_fingerprint": client.settings_fingerprint, "predicate": "screen_transition",
                        "initial_screen": "none", "final_screen": "fixture.Screen", "required_openings": [],
                        "forbidden_openings": [], "min_horizontal_distance": 0.0, "max_horizontal_distance": .25})
                producer.register("tx", "owner", e.epoch, worker, client, expectations)
                essential = NativeEssentialInputs(e.repairs)
                required, _, essential_head = essential.requirements("tx", "owner", e.epoch, worker, client)
                essential_cases = []
                for slot in required:
                    declared = None
                    sprint = slot["role"] == "sprint" and slot["context"] == "IN_GAME"
                    if slot["role"] == "escape" and slot["context"] == "GUI":
                        request = EffectRequest(id="escape-" + slot["stage"], transaction_id="tx",
                            expected_revision=essential_head.revision, expected_digest=essential_head.digest,
                            plan_digest=plan["worker_plan"]["plan_digest"], binding_id=FIXED_ESCAPE,
                            context="GUI", stage=slot["stage"],
                            hold_ms=1250 if slot["stage"] == "before_restart" else 50, settle_ticks=2)
                        declared = {"schema": "strata/NativeEffectExpectation/1", "request": request.model_dump(),
                            "settings_fingerprint": client.settings_fingerprint, "predicate": "screen_transition",
                            "initial_screen": "fixture.Screen", "final_screen": "none", "required_openings": [],
                            "forbidden_openings": [], "min_horizontal_distance": 0.0, "max_horizontal_distance": .25}
                    if sprint:
                        request = EffectRequest(id="sprint-" + slot["stage"], transaction_id="tx",
                            expected_revision=essential_head.revision, expected_digest=essential_head.digest,
                            plan_digest=plan["worker_plan"]["plan_digest"], binding_id=slot["binding_id"],
                            context="IN_GAME", stage=slot["stage"], hold_ms=150, settle_ticks=2)
                        declared = {"schema": "strata/NativeEffectExpectation/1", "request": request.model_dump(),
                            "settings_fingerprint": client.settings_fingerprint, "predicate": "horizontal_motion",
                            "initial_screen": "none", "final_screen": "none", "required_openings": [],
                            "forbidden_openings": [], "min_horizontal_distance": .1, "max_horizontal_distance": 2.0}
                    essential_cases.append({"role": slot["role"], "context": slot["context"], "stage": slot["stage"],
                        "expectation": declared, "unverified_reason": None if declared else "FIXTURE_PREREQUISITE_UNAVAILABLE",
                        "motion_axis": [1.0, 0.0, 0.0] if sprint else None, "minimum_motion": .1 if sprint else 0.0})
                essential.register("tx", "owner", e.epoch, worker, client, essential_cases)
                assert FIXED_ESCAPE not in head["bindings"] and FIXED_ESCAPE not in e.controls.status("tx")["plan"]["backup"]
                with pytest.raises(Fault, match="EFFECT_EVIDENCE_INCOMPLETE"):
                    producer.effect_checks("tx", "owner", e.epoch, worker, client)

            def capture_stage(native, stage):
                for expected in expectations:
                    e.controller.heartbeat("c1", "owner", e.epoch)
                    request = EffectRequest.model_validate(expected["request"])
                    if request.stage != stage:
                        continue
                    if request.binding_id != ID:
                        # A charged ordinary inventory gesture prepares the next synthetic context.
                        close = request.model_copy(update={"id": "close-" + stage, "context": "GUI"})
                        native.call("settings_effect_start", close.model_dump(), timeout_ms=500,
                            effect_deadline_unix_ms=min(plan["worker_plan"]["expires_unix_ms"], int(time.time() * 1000) + 1000))
                        assert terminal(native, close)["state"] == "observed"
                    producer.capture("tx", "owner", e.epoch, worker, native, request.id)
            if lost is None:
                capture_stage(client, "before_restart")
                e.controller.heartbeat("c1", "owner", e.epoch)
                essential.capture("tx", "owner", e.epoch, worker, client, "escape", "GUI", "before_restart")
                essential.capture("tx", "owner", e.epoch, worker, client, "sprint", "IN_GAME", "before_restart")
            coordinator = NativeRepairRestart(e.repairs)
            restart = WorkerRestartClient.from_file(state / f"restart-grant-{e.epoch}.json")
            handoff_before = tuple(e.database.connection.execute("SELECT * FROM repair_native_handoffs WHERE id='tx'").fetchone())
            native_result = client._result
            native_calls, worker_calls = [], []
            def lose_native(operation, *args, **kwargs):
                result = native_result(operation, *args, **kwargs)
                native_calls.append(operation)
                if lost == "prepare" and operation == "settings_restart_prepare":
                    raise TimeoutError("synthetic reply loss after durable native prepare")
                return result
            monkeypatch.setattr(client, "_result", lose_native)
            worker_call = restart.call
            def lose_worker(operation, *args, **kwargs):
                result = worker_call(operation, *args, **kwargs)
                worker_calls.append(operation)
                if operation == lost:
                    raise WorkerRestartUnknown("lost-reply")
                return result
            monkeypatch.setattr(restart, "call", lose_worker)
            wrong_restart = WorkerRestartClient(restart.grant.model_copy(update={"repair_binding_digest": "0" * 64}))
            with pytest.raises(Fault, match="RESTART_WORKER_MISMATCH"):
                coordinator.prepare_and_detach("tx", "owner", e.epoch, worker, wrong_restart, client, "restart-1")
            assert not native_calls and not worker_calls
            def detach():
                return coordinator.prepare_and_detach("tx", "owner", e.epoch, worker, restart, client, "restart-1")
            if lost in {"prepare", "detach"}:
                with pytest.raises(EffectOutcomeUnknown if lost == "prepare" else WorkerRestartUnknown):
                    detach()
            prepared = detach()
            checkpoint = prepared["checkpoint"]
            detached = e.cas.json(e.operator, "operator", prepared["source_ref"])["state"]
            assert detached["phase"] == "detached" and detached["old_terminal"]["termination_confirmed"] is True
            with pytest.raises(Fault, match="REPAIR_RESTART_IN_PROGRESS"):
                flow.commit("tx", "owner", e.epoch, worker, client, verification(e))
            assert game.wait(timeout=1) is not None and parent.poll() is None
            supervisor_before = [json.loads(line) for line in (state / f"supervisor-{e.epoch}.jsonl").read_text().splitlines()]
            child_pid = next(x["value"]["pid"] for x in supervisor_before if x["kind"] == "worker_started")
            assert detach()["phase"] == "DETACHED"
            with effects_jvm(repair_owner=True, commit_owner=True, restart_owner=True, resume_owner=resuming) as (replacement, second, _, _):
                descriptor2 = tmp_path / "connection-2.json"
                identity2 = json.loads(run([sys.executable, "-I", "-m", "mcbench.process_guard", "--inspect", str(second.pid)]).stdout)
                guard2 = tmp_path / "guard-2.json"
                old_guard = json.loads(guard.read_text())
                guard2.write_bytes(canonical(old_guard | {**({"schema": "strata/ForgeProcessGuardGrant/4", "resume_policy": "operator-owned-settings-resume/1"} if resuming else {"schema": "strata/ForgeProcessGuardGrant/3"}),
                    "restart_checkpoint": checkpoint, "repair_plan": plan["worker_plan"],
                    "process": identity2, "connection_file": str(descriptor2),
                    "connection_digest": digest(json.loads(descriptor2.read_text()))}))
                paths = {"connection_file": str(descriptor2), "process_guard_file": str(guard2)}
                with pytest.raises(Fault, match="RESTART_CONNECTION_MISMATCH"):
                    coordinator.adopt("tx", "owner", e.epoch, worker, restart, client, client,
                        {"connection_file": str(descriptor), "process_guard_file": str(guard2)})
                assert coordinator._row("tx")["phase"] == "DETACHED" and "attach" not in worker_calls
                def adopt():
                    return coordinator.adopt("tx", "owner", e.epoch, worker, restart, client, replacement, paths)
                if lost == "attach":
                    with pytest.raises(WorkerRestartUnknown):
                        adopt()
                adopted = adopt()
                assert adopted["phase"] == "ADOPTED" and adopt() == adopted
                if lost is None:
                    e.controls.adapter = NativeSettingsProjection(replacement, q.ref, q.read,
                        simulation=True, clock=time.time)
                    assert e.controls._policy(e.controls.adapter.snapshot()) == e.controls.status("tx")["plan"]["policy_digest"]
                attached = e.cas.json(e.operator, "operator", adopted["source_ref"])["worker_state"]
                assert attached["phase"] == "attached" and attached["input_resumed"] is False
                assert attached["primitive_events"] >= detached["primitive_events"]
                assert parent.poll() is None
                assert tuple(e.database.connection.execute("SELECT * FROM repair_native_handoffs WHERE id='tx'").fetchone()) == handoff_before
                with pytest.raises(Fault, match="REPAIR_NOT_OWNED"):
                    flow.commit("tx", "owner", e.epoch, worker, client, verification(e))
                head = replacement.call("settings_snapshot", {})
                effect = EffectRequest(id="after", transaction_id="tx", expected_revision=head["revision"],
                    expected_digest=head["digest"], plan_digest=plan["worker_plan"]["plan_digest"], binding_id=ID,
                    context="IN_GAME", stage="after_restart", hold_ms=50, settle_ticks=2)
                proofs = verification(e)
                if lost is None:
                    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
                        producer.register("tx", "owner", e.epoch, worker, replacement,
                            [dict(x, final_screen="fixture.Other") for x in expectations])
                    original_result = replacement._result
                    emitted = []
                    def lose_effect(operation, *args, **kwargs):
                        value = original_result(operation, *args, **kwargs)
                        if operation == "settings_effect_start" and args[0]["id"] == "after":
                            emitted.append(operation)
                            raise TimeoutError("synthetic reply loss after native effect dispatch")
                        return value
                    monkeypatch.setattr(replacement, "_result", lose_effect)
                    e.controller.heartbeat("c1", "owner", e.epoch)
                    with pytest.raises(EffectOutcomeUnknown):
                        producer.capture("tx", "owner", e.epoch, worker, replacement, "after")
                    e.controller.heartbeat("c1", "owner", e.epoch)
                    checked = producer.capture("tx", "owner", e.epoch, worker, replacement, "after")
                    assert checked == producer.capture("tx", "owner", e.epoch, worker, replacement, "after")
                    assert emitted == ["settings_effect_start"] and checked["check"]["status"] == "pass"
                    capture_stage(replacement, "after_restart")
                    e.controller.heartbeat("c1", "owner", e.epoch)
                    source = essential.capture("tx", "owner", e.epoch, worker, replacement, "escape", "GUI", "after_restart")
                    assert essential.capture("tx", "owner", e.epoch, worker, replacement, "escape", "GUI", "after_restart") == source
                    e.controller.heartbeat("c1", "owner", e.epoch)
                    essential.capture("tx", "owner", e.epoch, worker, replacement, "sprint", "IN_GAME", "after_restart")
                    coverage = essential.coverage("tx")
                    assert sum(c["status"] == "pass" for c in coverage["cases"]) == 4
                    assert not coverage["input_cases_complete"] and not coverage["essential_controls_verified"]
                    assert coverage["recovery_qualification_required"]
                    e.controller.heartbeat("c1", "owner", e.epoch)
                    matrix = producer.effect_checks("tx", "owner", e.epoch, worker, replacement)
                    assert all(c["status"] == "pass" for c in matrix["checks"].values())
                    assert "essential-controls" not in matrix["checks"]
                    original_reader = e.controls.evidence_reader
                    e.controls.evidence_reader = lambda ref, max_bytes: (original_reader(ref, max_bytes=max_bytes)
                        if ref in e.adapter.evidence else e.cas.read(e.operator, "operator", ref, max_bytes=max_bytes))
                    proofs["binding_checks"] = matrix["binding_checks"]
                    proofs["checks"].update(matrix["checks"])
                    retained = coordinator._row("tx")["source_ref"]
                    retained_body = e.cas.json(e.operator, "operator", retained)
                    for path, wrong in [("worker_state.old_terminal.termination_confirmed", False),
                                        ("native_state.input_resumed", True), ("native_head.digest", "0" * 64),
                                        ("native_head.options_sha256", "0" * 64), ("old_binding", "0" * 64),
                                        ("is_example", False)]:
                        e.controller.heartbeat("c1", "owner", e.epoch)
                        altered = copy.deepcopy(retained_body)
                        target_body = altered
                        parts = path.split(".")
                        for part in parts[:-1]:
                            target_body = target_body[part]
                        target_body[parts[-1]] = wrong
                        bad_ref = e.cas.put(e.operator, "operator", "operator", canonical(altered))
                        with e.database.transaction() as db:
                            db.execute("UPDATE repair_native_restarts SET source_ref=? WHERE id='tx'", (bad_ref,))
                        with pytest.raises(ValueError):
                            producer.restart_check("tx", "owner", e.epoch, worker, replacement)
                    with e.database.transaction() as db:
                        db.execute("UPDATE repair_native_restarts SET source_ref=? WHERE id='tx'", (retained,))
                    proofs["checks"]["restart-persistence"] = producer.restart_check("tx", "owner", e.epoch, worker, replacement)
                else:
                    replacement.call("settings_effect_start", effect.model_dump(), timeout_ms=500)
                    assert terminal(replacement, effect)["state"] == "observed"
                assert flow.commit("tx", "owner", e.epoch, worker, replacement, proofs)["control"]["phase"] == "committed"
                if resuming:
                    resume = WorkerResumeClient.from_file(state / f"resume-grant-{e.epoch}.json")
                    joined = NativeRepairResume(e.repairs)
                    wrong = WorkerResumeClient(resume.grant.model_copy(update={"restart_binding_digest": "0" * 64}))
                    with pytest.raises(Fault, match="RESUME_WORKER_MISMATCH"):
                        joined.resume_committed("tx", "owner", e.epoch, worker, restart, wrong, replacement)
                    # Corrupt only this synthetic fixture's private evidence;
                    # every refusal must precede durable resume intent/input.
                    retained_ref = coordinator._row("tx")["source_ref"]
                    retained_body = e.cas.json(e.operator, "operator", retained_ref)
                    mutations = [
                        [("worker_state.replacement.connection_digest", "0" * 64)],
                        [("worker_state.replacement.body_fingerprint", "0" * 64)],
                        [("worker_state.old_connection_digest", "0" * 64),
                         ("worker_state.old_terminal.connection_digest", "0" * 64)],
                        [("native_state.current_instance", "other-instance"),
                         ("native_state.continued_instance", "other-instance")],
                        [("is_example", False)],
                    ]
                    try:
                        for changes in mutations:
                            altered = copy.deepcopy(retained_body)
                            for path, value in changes:
                                target_body = altered
                                parts = path.split(".")
                                for part in parts[:-1]:
                                    target_body = target_body[part]
                                target_body[parts[-1]] = value
                            bad_ref = e.cas.put(e.operator, "operator", "operator", canonical(altered))
                            with e.database.transaction() as db:
                                db.execute("UPDATE repair_native_restarts SET source_ref=? WHERE id='tx'", (bad_ref,))
                            with pytest.raises(Fault, match="RESTART_EVIDENCE_INVALID|RESUME_INSTANCE_MISMATCH"):
                                joined.resume_committed("tx", "owner", e.epoch, worker, restart, resume, replacement)
                    finally:
                        with e.database.transaction() as db:
                            db.execute("UPDATE repair_native_restarts SET source_ref=? WHERE id='tx'", (retained_ref,))
                    with e.database.transaction() as db:
                        db.execute("UPDATE operations SET uncertain=1 WHERE id='repair-op'")
                    try:
                        with pytest.raises(Fault, match="REPAIR_BUDGET_REQUIRED"):
                            joined.resume_committed("tx", "owner", e.epoch, worker, restart, resume, replacement)
                    finally:
                        with e.database.transaction() as db:
                            db.execute("UPDATE operations SET uncertain=0 WHERE id='repair-op'")
                    assert e.database.connection.execute("SELECT count(*) FROM repair_worker_resumes").fetchone()[0] == 0
                    original_resume = resume.call
                    resume_calls = []
                    def dispatch(operation, *args, **kwargs):
                        reply = original_resume(operation, *args, **kwargs)
                        resume_calls.append(operation)
                        if operation == "resume" and lost == "resume_lost":
                            raise WorkerResumeUnknown("lost-worker-reply")
                        return reply
                    monkeypatch.setattr(resume, "call", dispatch)
                    def resume_once():
                        e.controller.heartbeat("c1", "owner", e.epoch)
                        return joined.resume_committed("tx", "owner", e.epoch, worker, restart, resume, replacement)
                    if lost == "publish":
                        from mcbench.inference_dispatch import InferenceAttempt, InferenceDispatches
                        from mcbench.records import BudgetLedger
                        gate = InferenceDispatches(e.database, e.cas, simulation=True)
                        price = e.put({"is_example": True, "fixture": "synthetic pricing"})
                        reserve = BudgetLedger.model_validate(example("BudgetLedger") | {
                            "is_example": False, "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch,
                            "ledger_id": "helper-reserve", "operation_id": "helper-pending", "parent_operation_id": None,
                            "source_event_id": "helper-reserve", "campaign_account": "training", "posting": "reserve",
                            "kind": "helper", "model_identity": "synthetic-no-model", "pricing_ref": price,
                            "raw_usage_ref": None, "metering": "estimated", "reason": "synthetic helper",
                            "usage": {key: 0 for key in example("BudgetLedger")["usage"]} | {
                                "input_tokens": 1, "output_tokens": 1, "model_calls": 1, "spend_microusd": 1}})
                        fields = {"runtime_job_id": "synthetic-helper", "profile_digest": "a" * 64,
                            "provider": "openai", "auth_mode": "chatgpt_oauth", "request_digest": "b" * 64}
                        bound = e.put({"schema": "strata/InferenceDispatchBound/1", "is_example": True, **fields,
                            "reservation_digest": digest(reserve.model_dump()), "pricing_ref": price, "currency": "USD",
                            "finite_dispatch_bound_verified": True, "pricing_semantics_verified": True,
                            "expires_unix_ms": int(time.time() * 1000) + 60000})
                        attempt = InferenceAttempt.model_validate({"schema": "strata/InferenceAttempt/1", **fields, "bound_ref": bound})
                        gate._begin("a1", attempt, reserve)
                        with pytest.raises(Fault, match="REPAIR_INFERENCE_PENDING"):
                            resume_once()
                        assert resume_calls == []
                        assert e.database.connection.execute("SELECT count(*) FROM repair_worker_resumes").fetchone()[0] == 0
                        assert e.database.connection.execute("SELECT count(*) FROM repair_resume_inference").fetchone()[0] == 0
                        assert joined.inference.audit("tx", "owner", e.epoch)["admission_closed"]
                        settlement = BudgetLedger.model_validate(reserve.model_dump() | {
                            "ledger_id": "helper-settle", "source_event_id": "helper-settle", "posting": "settle",
                            "metering": "reported", "raw_usage_ref": e.put({"is_example": True, "fixture": "synthetic usage receipt"})})
                        gate.settle("helper-pending", "synthetic-helper-event", settlement)
                    if lost == "resume_lost":
                        with pytest.raises(WorkerResumeUnknown):
                            resume_once()
                        assert e.database.connection.execute("SELECT phase FROM repair_worker_resumes").fetchone()[0] == "UNKNOWN"
                    resumed = resume_once()
                    assert resumed["worker_state"]["gameplay_resumed"] is (lost != "publish")
                    assert not resumed["campaign_permission_published"]
                    again = resume_once()
                    assert again["worker_state"]["decision"] == resumed["worker_state"]["decision"]
                    assert resume_calls.count("resume") == 1
                    assert resume_calls.count("status") >= 1
                    assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
                    assert e.repairs.status("tx")["phase"] == "AWAITING_OBSERVATION"
                    row = e.database.connection.execute("SELECT * FROM repair_worker_resumes WHERE id='tx'").fetchone()
                    witness = e.cas.json(e.operator, "operator", row["source_ref"])
                    assert witness["schema"] == "strata/ControllerResumeWitness/2"
                    inference = e.cas.json(e.operator, "operator", witness["inference_ref"])
                    assert inference["tracked_dispatches_settled"] and inference["admission_closed"]
                    assert not inference["costs_reposted"] and not inference["complete_repair_accounting"]
                    if lost == "publish":
                        assert [c["operation_id"] for c in inference["calls"]] == ["helper-pending"]
                        assert inference["calls"][0]["actual"]["model_calls"] == 1
                    assert not witness["campaign_permission_published"] and not witness["consumption_settled"]
                    assert witness["worker_state"]["decision"]["worker_plan"]["lease_id"] == lease
                    with pytest.raises(Fault, match="REPAIR_WORKER_RESUME_REQUIRED"):
                        e.repairs.finish("tx", "owner", e.epoch, "cas:sha256:" + "0" * 64)
                    if lost == "publish":
                        grant = json.loads((state / f"publication-grant-{e.epoch}.json").read_text())
                        assert grant["resume_binding_digest"] == resume.binding_digest
                        publisher = WorkerPublicationClient.from_file(state / f"publication-grant-{e.epoch}.json")
                        publisher.validate_resume(resume)
                        measurement = joined.measure_prepared("tx", "owner", e.epoch, worker, restart, resume, publisher, replacement)
                        measured = WorkerRepairAccounting.model_validate(measurement["receipt"])
                        stored_measurement = e.cas.json(e.operator, "operator", measurement["source_ref"])
                        assert stored_measurement["worker_receipt"] == measured.model_dump()
                        assert not stored_measurement["consumption_settled"] and not stored_measurement["complete_repair_accounting"]
                        assert joined.measure_prepared("tx", "owner", e.epoch, worker, restart, resume, publisher, replacement) == measurement
                        assert measured.opening.primitive_events > 0
                        assert measured.charged_primitive_events == measured.closing.primitive_events - measured.opening.primitive_events > 0
                        assert measured.closing.primitive_events == resumed["worker_state"]["primitive_events"]
                        assert measured.elapsed_ms > 0 and measured.complete_repair_accounting is False
                        assert measured.avatar_ticks is None and measured.model_usage is None
                        floor = e.database.connection.execute(
                            "SELECT minimum,body FROM budget_consumption_floors WHERE operation='repair-op'").fetchone()
                        assert floor["minimum"] == measured.charged_primitive_events
                        assert json.loads(floor["body"])["evidence"]["worker_receipt"] == measured.model_dump()
                        assert e.database.connection.execute(
                            "SELECT actual FROM operations WHERE id='repair-op'").fetchone()[0] is None
                        assert publisher.measure(NativeResumeDecision.model_validate(resumed["worker_state"]["decision"])) == measured
                        with sqlite3.connect((state / "actions.sqlite").as_uri() + "?mode=ro", uri=True) as db:
                            opening_row = json.loads(db.execute("SELECT opening FROM repair_accounting WHERE transaction_id='tx'").fetchone()[0])
                            assert opening_row == measured.opening.model_dump()
                            assert json.loads(db.execute("SELECT body FROM events WHERE cursor=?", (measured.opening.cursor,)).fetchone()[0])["plan"] == measured.worker_plan.model_dump()
                            charged = sum(json.loads(row[0])["charged_delta"] for row in db.execute(
                                "SELECT body FROM events WHERE kind='native_usage' AND cursor>? AND cursor<=?",
                                (measured.opening.cursor, measured.closing.cursor)))
                            assert charged == measured.charged_primitive_events
                        control = e.controls.status("tx")["receipt"]
                        decision = resumed["worker_state"]["decision"]
                        # Test-only accounting producer. The actual controller settlement
                        # producer/publication transaction remains a separate requirement.
                        publication = {"schema": "strata/WorkerControlPublication/1", "policy": grant["policy"],
                            "publication_id": "publication", "worker_plan": decision["worker_plan"],
                            "resume_digest": digest(decision), "control_revision": control["revision"],
                            "keymap_digest": control["keymap_digest"], "verification_ref": decision["verification_ref"],
                            "settlement_ref": e.put({"is_example": True, "fixture": "synthetic settlement producer"}),
                            "primitive_events": resumed["worker_state"]["primitive_events"]}
                        def publish(operation, value=publication):
                            return publisher.publish(operation, WorkerControlPublication.model_validate(value)).model_dump()
                        cli_env = os.environ | {"STRATA_GAME_GRANT": str(state / f"grant-{e.epoch}.json")}
                        def play():
                            return subprocess.run([node, str(worker_js.with_name("cli.js")), "look-at", "--x", "1", "--y", "65", "--z", "2", "--json"],
                                capture_output=True, timeout=3, creationflags=subprocess.CREATE_NO_WINDOW, env=cli_env)
                        refused = play()
                        assert refused.returncode != 0 and b"RECONFIGURING" in refused.stdout
                        published = publish("publish")
                        assert published["published"]
                        assert published["observation"]["keymap_digest"] == control["keymap_digest"]
                        assert published["observation"]["control_revision"] == control["revision"]
                        assert publish("status")["decision"] == publication
                        publication_value = WorkerControlPublication.model_validate(publication)
                        published_accounting = publisher.publication_accounting(publication_value)
                        assert published_accounting.measurement == measured
                        # A failed private store must not complete the repair or repeat publication.
                        original_put = joined.flow._put
                        def unavailable_store(_):
                            raise OSError("synthetic publication evidence storage failure")
                        with monkeypatch.context() as fault:
                            fault.setattr(joined.flow, "_put", unavailable_store)
                            with pytest.raises(OSError, match="synthetic publication evidence"):
                                joined.capture_publication("tx", "owner", e.epoch, publisher, publication_value)
                        assert joined.flow._put == original_put
                        assert e.database.connection.execute("SELECT count(*) FROM repair_publication_evidence").fetchone()[0] == 0
                        captured_publication = joined.capture_publication("tx", "owner", e.epoch, publisher, publication_value)
                        publication_witness = e.cas.json(e.operator, "operator", captured_publication["source_ref"])
                        assert publication_witness["worker_receipt"] == published_accounting.model_dump()
                        assert publication_witness["measurement_ref"] == measurement["source_ref"]
                        assert publication_witness["inference_ref"] == witness["inference_ref"]
                        assert not publication_witness["consumption_settled"] and not publication_witness["campaign_permission_published"]
                        with sqlite3.connect((state / "actions.sqlite").as_uri() + "?mode=ro", uri=True) as db:
                            commits = db.execute("SELECT body FROM events WHERE kind='repair_publication_confirmed'").fetchall()
                            assert len(commits) == 1
                            publication_commit = json.loads(commits[0][0])
                            assert published_accounting.commit.model_dump() == publication_commit
                            assert publication_commit["schema"] == "strata/WorkerControlPublicationCommit/1"
                            assert publication_commit["decision"] == publication
                            assert publication_commit["observation"] == published["observation"]
                            assert publication_commit["measurement_digest"] == digest(measured.model_dump())
                            assert publication_commit["clock_id"] == measured.clock_id
                            boundary = publication_commit["boundary"]
                            assert boundary["sources"] == measured.closing.sources
                            assert boundary["primitive_events"] == measured.closing.primitive_events
                            assert boundary["cursor"] >= measured.closing.cursor
                            assert boundary["mono_ms"] >= measured.closing.mono_ms
                            assert publication_commit["complete_repair_accounting"] is False
                        accepted = play()
                        assert accepted.returncode in (0, 2), accepted.stderr
                        ack = json.loads(accepted.stdout)["result"]
                        assert ack["status"] == "accepted" and ack["action_seq"] == 2
                        native_game = NativeGameClient(replacement.connection)
                        until = time.monotonic() + 2
                        while True:
                            outcome = native_game.call("action_status", {"request_id": ack["request_id"]})
                            if outcome["status"] not in {"accepted", "executing"} or time.monotonic() > until:
                                break
                            time.sleep(.01)
                        assert outcome["status"] == "emitted" and outcome["release_confirmed"]
                        assert native_game.call("observe", {"cursor": None})["state"]["yaw"] == .25
                        assert publisher.publication_accounting(publication_value) == published_accounting
                        assert joined.capture_publication("tx", "owner", e.epoch, publisher, publication_value) == captured_publication
                        assert e.database.connection.execute("SELECT count(*) FROM repair_publication_evidence").fetchone()[0] == 1
                        with sqlite3.connect((state / "actions.sqlite").as_uri() + "?mode=ro", uri=True) as db:
                            assert db.execute("SELECT body FROM events WHERE kind='repair_publication_confirmed'").fetchall() == commits
                            public_batch = json.loads(db.execute("SELECT request FROM actions WHERE request_id=?", (ack["request_id"],)).fetchone()[0])
                            translated = json.loads(db.execute("SELECT body FROM events WHERE kind='native_action_translation' ORDER BY cursor DESC").fetchone()[0])
                            assert public_batch["keymap_digest"] == control["keymap_digest"]
                            assert translated["public_digest"] == digest(public_batch)
                            assert translated["native_batch"]["keymap_digest"] is None
                            assert translated["native_batch"]["control_revision"] == e.epoch
                            assert translated["native_digest"] == digest(translated["native_batch"])
                            original = json.loads(db.execute("SELECT request FROM actions WHERE request_id=?", (initial_ack["request_id"],)).fetchone()[0])
                        public = json.loads(public_grant.read_text())
                        address = urlsplit(public["url"])
                        connection = http.client.HTTPConnection(address.hostname, address.port, timeout=2)
                        try:
                            connection.request("POST", address.path, canonical({"schema": "strata/GameRequest/1",
                                "request_id": original["request_id"], "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch,
                                "deadline_at": datetime.fromtimestamp(time.time() + 2, timezone.utc).isoformat().replace("+00:00", "Z"),
                                "method": "act", "action": original,
                                "target_request_id": None, "after": None}),
                                {"Content-Type": "application/json", "Authorization": "Bearer " + public["token"]})
                            response = connection.getresponse()
                            replay = json.loads(response.read())
                            assert response.status == 200, replay
                            assert replay["result"]["status"] == "emitted" and replay["result"]["action_seq"] == 1
                        finally:
                            connection.close()

                else:
                    assert flow.rollback("tx", "owner", e.epoch, worker, replacement)["control"]["phase"] == "rolled_back"
                    assert (profile / "options.txt").read_bytes() == options.encode()
                assert native_calls.count("settings_restart_prepare") == 1
                assert worker_calls.count("detach") == 1 and worker_calls.count("attach") == 1
                assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
                assert e.controller.input_authority("c1", "owner", e.epoch, "a2")["state"] == "READY"
                assert e.budgets.status("a1")["committed_and_reserved"]["primitive_events"] == 20
                parent.stdin.write(canonical({"schema": "strata/WorkerStop/1", "policy": "operator-stdin-stop2250/1",
                    "request_id": "stop", "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch, "lease_id": lease}) + b"\n")
                parent.stdin.flush()
                assert parent.wait(timeout=6) == 0
                assert second.wait(timeout=2) is not None
            records = [json.loads(line) for line in (state / f"supervisor-{e.epoch}.jsonl").read_text().splitlines()]
            assert [x["value"]["pid"] for x in records if x["kind"] == "worker_started"] == [child_pid]
            assert sum(x["kind"] == "guard_stopped" for x in records) == 2
            assert sum(x["kind"] == "repair_restart_old_terminal" for x in records) == 1
            assert sum(x["kind"] == "repair_restart_replacement_guarded" for x in records) == 1
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)
            parent.stdout.close()
            parent.stderr.close()
            parent.stdin.close()
