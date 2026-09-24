"""Pinned private worker leases and native-runner lifetime; no game/provider calls."""
from copy import deepcopy
import json

import pytest

from mcbench.launch_integrity import IntegrityError, safe
from mcbench.storage import Fault, canonical
from mcbench.worker_bundle import HeldWorkerBundle
import test_worker_bundle as bundle_tests

import test_worker_stop as stop_tests

inputs = bundle_tests.inputs
stop_archive = stop_tests.archive


@pytest.fixture
def prepared(inputs):
    result = bundle_tests.prepare(inputs)
    return {"path": result["manifest"], "sha256": result["sha256"]}


def test_manifest_and_all_runtime_inputs_are_held_until_context_exit(prepared):
    from pathlib import Path
    with HeldWorkerBundle(prepared) as runtime:
        assert runtime.command("--check-vanilla-runtime") == [runtime.body["node"], runtime.body["worker"],
                                                             "--check-vanilla-runtime"]
        for path in (prepared["path"], *[runtime.body[k] for k in ("node", "worker", "python", "acl_helper")]):
            with pytest.raises(PermissionError):
                with open(path, "r+b"):
                    pytest.fail("write open while runtime is held")
        assert runtime.receipt()["manifest_held"]
    Path(prepared["path"]).write_bytes(b"handles released")


@pytest.mark.parametrize("change", ["anchor", "file", "extra", "hardlink", "launch", "profile", "flags",
                                    "tree", "outside", "duplicate", "quota", "missing_worker"])
def test_modified_or_incomplete_runtime_never_enters(prepared, change, tmp_path):
    import hashlib
    from pathlib import Path
    path = Path(prepared["path"])
    body = json.loads(path.read_bytes())
    if change == "anchor":
        prepared["sha256"] = "a" * 64
    elif change == "file":
        Path(body["worker"]).write_bytes(b"changed")
    elif change == "extra":
        (Path(body["root"]) / "unlisted.js").write_bytes(b"changed")
    elif change == "hardlink":
        (tmp_path / "alias").hardlink_to(body["python"])
    else:
        if change == "launch":
            body["worker"] = str(tmp_path / "outside.js")
        elif change == "profile":
            body["runtime_qualified"] = True
        elif change == "flags":
            body["python_arguments"] = ["-I"]
        elif change == "tree":
            body["inventory"]["trees"] = []
        elif change == "outside":
            body["inventory"]["files"][0]["path"] = str(safe(tmp_path / "outside"))
        elif change == "duplicate":
            body["inventory"]["files"].append(deepcopy(body["inventory"]["files"][0]))
        elif change == "quota":
            body["inventory"]["files"][0]["bytes"] = 1024**3
        else:
            value = str(safe(Path(body["worker"])))
            body["inventory"]["files"] = [e for e in body["inventory"]["files"] if e["path"] != value]
            body["inventory"]["trees"][0]["files"].remove(value)
            Path(body["worker"]).unlink()
        raw = canonical(body)
        path.write_bytes(raw)
        prepared["sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises((Fault, IntegrityError)):
        with HeldWorkerBundle(prepared):
            pytest.fail("untrusted runtime admitted")


def test_added_file_after_acquisition_blocks_the_next_launch(prepared):
    from pathlib import Path
    with HeldWorkerBundle(prepared) as runtime:
        (Path(runtime.body["root"]) / "late.js").write_bytes(b"unlisted")
        with pytest.raises(IntegrityError, match="BOOTSTRAP_TREE_CHANGED"):
            runtime.command("worker-config.json")


def test_oversized_descriptor_never_publishes_a_launchable_bundle(inputs, monkeypatch):
    from mcbench import worker_bundle
    monkeypatch.setattr(worker_bundle, "MANIFEST_LIMIT", 1)
    with pytest.raises(Fault, match="WORKER_BUNDLE_MANIFEST"):
        bundle_tests.prepare(inputs)
    assert inputs[3].is_dir() and not inputs[3].with_suffix(".manifest.json").exists()


@pytest.mark.parametrize("change", [None, "legacy", "identity", "bytes", "receipt", "stop"])
def test_pinned_recovery_requires_the_same_recorded_runtime(change):
    from types import SimpleNamespace
    from native_game_recovery import GameRecovery
    recovery = GameRecovery.__new__(GameRecovery)
    plan = {"schema": "strata/M0NativeGameSmoke/3", "worker_runtime": {"sha256": "a" * 64}}
    entry = SimpleNamespace(sha256="a" * 64)
    recovery.bundle = SimpleNamespace(json=lambda _: {"plan": plan}, files={"run/worker-runtime.json": entry})
    recovery.result = {"worker_runtime": {"manifest_sha256": "a" * 64, "held_through_owned_stop": True}}
    if change == "legacy":
        plan["schema"] = "strata/M0NativeGameSmoke/2"
    elif change == "identity":
        plan["worker_runtime"]["sha256"] = "b" * 64
    elif change == "bytes":
        entry.sha256 = "b" * 64
    elif change == "receipt":
        recovery.result["worker_runtime"]["manifest_sha256"] = "b" * 64
    elif change == "stop":
        recovery.result["worker_runtime"]["held_through_owned_stop"] = False
    if change:
        with pytest.raises(Fault, match="GAME_RECOVERY_WORKER_CHANGED"):
            recovery.check_worker_runtime({"sha256": "a" * 64})
    else:
        recovery.check_worker_runtime({"sha256": "a" * 64})


@pytest.mark.parametrize("fail", [False, True])
def test_runner_keeps_runtime_held_during_owned_cleanup_even_on_error(prepared, tmp_path, monkeypatch, fail):
    import m0_native_game as runner
    plan = {"schema": "strata/M0NativeGameSmoke/3", "output": str(tmp_path / "output"),
        "worker_runtime": prepared, "server_plan": "unused", "worker_config": "unused", "codex": "unused",
        "tool_projections": "unused", "model_catalog": "unused", "retention_source": {"path": "unused"}}
    path = tmp_path / "plan.json"
    path.write_bytes(canonical(plan))
    cleaned = []

    def body(value, resources, runtime):
        assert value == plan and runtime.receipt()["manifest_held"]
        def cleanup():
            with pytest.raises(PermissionError):
                with open(runtime.body["worker"], "r+b"):
                    pytest.fail("runtime released before owned cleanup")
            cleaned.append(True)
        resources.callback(cleanup)
        if fail:
            raise RuntimeError("synthetic native failure")
        return {"status": "synthetic"}

    # Isolate worker lease lifetime from the separately tested native preflight.
    monkeypatch.setattr(runner, "file_hash", lambda _path: runner.BINARY_SHA256)
    monkeypatch.setattr(runner, "native_companion_paths", lambda _path: [])
    monkeypatch.setattr(runner, "run_plan", body)
    if fail:
        with pytest.raises(RuntimeError, match="synthetic native failure"):
            runner.run(path)
    else:
        assert runner.run(path) == {"status": "synthetic"}
    assert cleaned == [True]
    with open(prepared["path"], "r+b"):
        pass


def test_pinned_runner_rejects_node_override_before_any_launch(prepared, tmp_path, monkeypatch):
    import m0_native_game as runner
    path = tmp_path / "plan.json"
    path.write_bytes(canonical({"schema": "strata/M0NativeGameSmoke/3", "node": "substitute",
        "worker_runtime": prepared, "output": str(tmp_path / "output"), "server_plan": "unused",
        "worker_config": "unused", "codex": "unused", "tool_projections": "unused", "model_catalog": "unused",
        "retention_source": {"path": "unused"}}))
    monkeypatch.setattr(runner, "run_plan", lambda *_: pytest.fail("unexpected launch"))
    with pytest.raises(Fault, match="M0_PLAN_INVALID"):
        runner.run(path)
    with pytest.raises(Fault, match="PRIVATE_PATH_REQUIRED"):
        runner.private(str(safe(runner.ROOT / "private.json")))


def runtime_archive(prepared):
    from pathlib import Path, PureWindowsPath
    from mcbench.storage import digest

    raw = Path(prepared["path"]).read_bytes()
    body = json.loads(raw)
    with HeldWorkerBundle(prepared) as runtime:
        receipt = runtime.receipt() | {"owned_processes": {name: {"parent_returncode": 0, "active_processes": 0}
            for name in ("worker-preflight", "worker-driver", "server-driver")},
            "held_through_owned_stop": True, "root": body["root"],
            "preflight_argv": runtime.command("--check-vanilla-runtime"),
            "worker_argv": runtime.command(r"C:\private\run\worker-config.json")}
    root = PureWindowsPath(body["root"])
    entries = {PureWindowsPath(e["path"].removeprefix("\\\\?\\")).relative_to(root).as_posix(): e
               for e in body["inventory"]["files"]}
    modules = {PureWindowsPath(name).name: e["sha256"] for name, e in entries.items()
               if name.startswith("backends/mineflayer/dist/src/")}
    cap = {"implementation_digest": digest(modules),
        "schema_digest": digest({name: entries[f"schemas/v1/public/{name}.json"]["sha256"]
                                for name in ("ActionBatch", "ActionAck", "Observation", "RpcRequest")}),
        "dependency_lock_digest": entries["backends/mineflayer/package-lock.json"]["sha256"]}
    intent = {"plan": {"schema": "strata/M0NativeGameSmoke/3", "worker_runtime": dict(prepared),
                       "output": r"C:\private\run"}}
    return raw, receipt, cap, intent


@pytest.mark.parametrize("change", [None, "manifest", "capability", "stop", "argv", "legacy", "count"])
def test_archived_runtime_receipt_is_bound_to_manifest_capability_and_stop(prepared, change):
    from types import SimpleNamespace
    from strata_evaluator.native_game_evidence import worker_runtime_evidence
    raw, receipt, cap, intent = runtime_archive(prepared)
    if change == "manifest":
        intent["plan"]["worker_runtime"]["sha256"] = "a" * 64
    elif change == "capability":
        cap["implementation_digest"] = "a" * 64
    elif change == "stop":
        receipt["owned_processes"]["worker-driver"]["active_processes"] = 1
    elif change == "argv":
        receipt["worker_argv"][0] = "other-node.exe"
    elif change == "legacy":
        intent["plan"]["schema"] = "strata/M0NativeGameSmoke/2"
    elif change == "count":
        receipt["files"] -= 1
    bundle = SimpleNamespace(json=lambda _: {"worker_runtime": receipt}, files={"run/worker-runtime.json": True},
                             read=lambda *_, **__: raw)
    if change:
        with pytest.raises(Fault):
            worker_runtime_evidence(bundle, intent, cap)
    else:
        result = worker_runtime_evidence(bundle, intent, cap)
        assert result["pinned"] and result["held_through_owned_stop"]
        assert not result["external_runtime_bytes_archived"] and not result["isolation_qualified"]


@pytest.mark.parametrize("change", [None, "no-intent", "policy", "downgrade", "argument", "stop-reference", "module"])
def test_controlled_runtime_requires_its_pinned_policy_command_and_stop_evidence(inputs, stop_archive, change):
    import hashlib
    from types import SimpleNamespace
    from strata_evaluator.native_game_evidence import worker_runtime_evidence
    (inputs[0] / "backends/mineflayer/dist/src/worker_control.js").write_bytes(b"synthetic operator control")
    prepared = bundle_tests.prepare(inputs, operator_stop=True)
    raw, runtime, cap, intent = runtime_archive({"path": prepared["manifest"], "sha256": prepared["sha256"]})
    _, values, result = stop_archive
    result["worker_runtime"] = runtime
    if change == "no-intent":
        del values["run/worker-stop-intent.json"]
    elif change in {"policy", "downgrade", "module"}:
        body = json.loads(raw)
        if change == "policy":
            body["operator_stop_policy"] = "unreviewed"
        elif change == "downgrade":
            body["schema"] = "strata/WorkerRuntimeBundle/1"
        else:
            body["inventory"]["files"] = [e for e in body["inventory"]["files"]
                                          if not e["path"].endswith("worker_control.js")]
        raw = canonical(body)
        intent["plan"]["worker_runtime"]["sha256"] = hashlib.sha256(raw).hexdigest()
    elif change == "argument":
        runtime["worker_argv"].pop()
    elif change == "stop-reference":
        result["worker_stop"]["receipt"] = deepcopy(result["worker_stop"]["receipt"])
        result["worker_stop"]["receipt"]["request"]["request_id"] = "different"
    values["run/result.json"] = result
    bundle = SimpleNamespace(json=lambda name: deepcopy(values[name]),
        read=lambda *_, **__: raw, files={"run/worker-runtime.json": True, **{name: True for name in values}})
    if change:
        with pytest.raises((Fault, KeyError), match="NATIVE_GAME_WORKER_MANIFEST" if change == "module" else None):
            worker_runtime_evidence(bundle, intent, cap)
    else:
        result = worker_runtime_evidence(bundle, intent, cap)
        assert result["normal_worker_stop_reconciled"] and not result["isolation_qualified"]
