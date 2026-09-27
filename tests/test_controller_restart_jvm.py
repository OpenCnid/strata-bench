"""Actual controller/worker/guardian/JVM replacement; synthetic body and verification producer."""

import json
import copy
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from mcbench.native_settings_effects import EffectRequest
from mcbench.native_repair_restart import NativeRepairRestart
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
@pytest.mark.parametrize("lost", [None, "prepare", "detach", "attach"])
def test_controller_adopts_replacement_and_finishes_native_writes_without_replay(effects_jvm, repair_env, tmp_path, monkeypatch, lost):
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
    with effects_jvm(repair_owner=True, commit_owner=True, restart_owner=True, capability_digest=capability, scope=("c1", "a1"), options_text=options) as (client, game, profile, game_root):
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
        config.write_bytes(canonical({"schema": "strata/ForgeDevelopmentWorker/4", "restart_policy": "operator-owned-client-replacement/1", "repair_policy": "operator-owned-fixed-repair-pause/1",
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
                        context=slot["context"], stage=slot["stage"], hold_ms=50, settle_ticks=2)
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
                            context="GUI", stage=slot["stage"], hold_ms=50, settle_ticks=2)
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
                        native.call("settings_effect_start", close.model_dump())
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
            with effects_jvm(repair_owner=True, commit_owner=True, restart_owner=True) as (replacement, second, _, _):
                descriptor2 = tmp_path / "connection-2.json"
                identity2 = json.loads(run([sys.executable, "-I", "-m", "mcbench.process_guard", "--inspect", str(second.pid)]).stdout)
                guard2 = tmp_path / "guard-2.json"
                old_guard = json.loads(guard.read_text())
                guard2.write_bytes(canonical(old_guard | {"schema": "strata/ForgeProcessGuardGrant/3",
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
                    with pytest.raises(EffectOutcomeUnknown):
                        producer.capture("tx", "owner", e.epoch, worker, replacement, "after")
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
