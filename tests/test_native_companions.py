"""Pinned native execution dependencies: synthetic files, no inference or game."""

from copy import deepcopy
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.inventory import file_hash
from mcbench.launch_integrity import IntegrityError, encode, native_companion_inventory, snapshot
from mcbench.native_bootstrap import acquire_native_bootstrap, prepare_bundle
from mcbench.native_broker_policy import BROKER_TOOLS, restricted_settings
from mcbench.runtime import CODEX_COMPANION_PINS, native_companion_paths
from mcbench.storage import Fault, canonical


@pytest.fixture
def companions(tmp_path, monkeypatch):
    import mcbench.runtime as runtime
    binary = tmp_path / "codex.exe"
    binary.write_bytes(b"synthetic executable")
    pins = {}
    for name in CODEX_COMPANION_PINS:
        path = tmp_path / name
        path.write_bytes(name.encode())
        pins[name] = file_hash(path)
    monkeypatch.setattr(runtime, "CODEX_COMPANION_PINS", pins)
    return binary, pins


@pytest.mark.parametrize("change", [None, "missing", "changed"])
def test_native_dependencies_checked_before_bootstrap_creation(companions, tmp_path, change):
    binary, pins = companions
    path = binary.parent / next(iter(pins))
    if change == "missing":
        path.unlink()
    elif change == "changed":
        path.write_bytes(b"different release")
    if change is None:
        assert {p.name for p in native_companion_paths(binary)} == set(pins)
        return
    target = tmp_path / "must-not-be-created"
    with pytest.raises(Fault, match="NATIVE_COMPANION_MISSING|NATIVE_COMPANION_CHANGED"):
        prepare_bundle(target, native_executable=binary, plugin_root=tmp_path / "unused",
                       broker_config=tmp_path / "unused.json")
    assert not target.exists()


@pytest.mark.parametrize("change", [None, "omitted", "extra", "changed-pin", "unlisted", "foreign-path",
                                  "duplicate", "downgrade", "empty-file"])
@pytest.mark.skipif(os.name != "nt", reason="Windows held-file boundary")
def test_companions_bound_to_adjacent_inventory_and_held(companions, tmp_path, change):
    binary, pins = companions
    names = ("python", "broker_bootstrap", "process_bootstrap", "broker_config")
    files = {name: str(tmp_path / name) for name in names}
    for name, path in files.items():
        Path(path).write_text(name, encoding="utf-8")
    Path(files["broker_config"]).write_bytes(canonical({"schema": "strata/SealedBrokerConfig/1",
        "runtime_id": "job", "database": str(tmp_path / "operator.sqlite"),
        "objects": str(tmp_path / "objects"), "worker_grant": None}))
    inventory = snapshot([binary, *native_companion_paths(binary), *map(Path, files.values())], [])
    manifest = {"schema": "strata/NativeBootstrap/2", "native_executable": str(binary),
                "native_companions": deepcopy(pins), "inventory": inventory,
                "python_paths": [str(tmp_path / "imports")], **files}
    host = next(e for e in inventory["files"] if e["path"].endswith("codex-code-mode-host.exe"))
    if change == "omitted":
        del manifest["native_companions"]["codex-code-mode-host.exe"]
    elif change == "extra":
        manifest["native_companions"]["extra.exe"] = "a" * 64
    elif change == "changed-pin":
        manifest["native_companions"]["codex-code-mode-host.exe"] = "a" * 64
    elif change == "unlisted":
        inventory["files"].remove(host)
    elif change == "foreign-path":
        host["path"] = str(tmp_path / "foreign" / "codex-code-mode-host.exe")
    elif change == "duplicate":
        inventory["files"].append(deepcopy(host))
    elif change == "downgrade":
        manifest["schema"] = "strata/NativeBootstrap/1"
    elif change == "empty-file":
        host["bytes"] = 0
    path = tmp_path / "manifest.json"
    path.write_bytes(encode(manifest))
    sha = file_hash(path)
    server = {"command": files["python"], "args": ["-I", "-S", "-B", files["broker_bootstrap"],
        "--manifest", str(path), "--sha256", sha], "env": {}, "required": True,
        "enabled_tools": list(BROKER_TOOLS), "tools": {"artifact_write": {"approval_mode": "approve"},
                                                       "game": {"approval_mode": "approve"}}}
    plan = SimpleNamespace(bootstrap_manifest=str(path), bootstrap_digest=sha, executable=str(binary),
        workspace=str(tmp_path / "gameplay"), job_id="job",
        config_overrides=restricted_settings() | {"mcp_servers.strata_broker": server})
    if change:
        with pytest.raises(IntegrityError, match="BOOTSTRAP_COMPANION"):
            acquire_native_bootstrap(plan)
    else:
        assert native_companion_inventory(manifest) == pins
        with acquire_native_bootstrap(plan) as held:
            for name in pins:
                with pytest.raises(OSError):
                    (binary.parent / name).write_bytes(b"replace while running")
            held.recheck()
        (binary.parent / next(iter(pins))).write_bytes(b"released")


def test_legacy_manifest_has_no_retroactive_companion_evidence():
    assert native_companion_inventory({"schema": "strata/NativeBootstrap/1"}) is None


@pytest.mark.parametrize("change", [None, "missing", "duplicate", "extra", "changed", "legacy"])
def test_offline_source_reconstruction_binds_external_companions(monkeypatch, change):
    from mcbench.storage import digest
    from strata_evaluator import native_game_evidence as evidence
    binary = "C:/private/bin/codex.exe"
    entries = [{"path": binary, "sha256": "a" * 64, "bytes": 1}]
    pins = dict(CODEX_COMPANION_PINS)
    manifest = {"schema": "strata/NativeBootstrap/2", "native_executable": binary,
                "native_companions": pins, "inventory": {"files": entries}}
    entries.extend({"path": "C:/private/bin/" + name, "sha256": sha, "bytes": 1}
                   for name, sha in pins.items())
    if change == "missing":
        entries.pop()
    elif change == "duplicate":
        entries.append(deepcopy(entries[1]))
    elif change == "extra":
        entries.append({"path": "C:/private/extra.exe", "sha256": "b" * 64, "bytes": 1})
    elif change == "changed":
        entries[1]["sha256"] = "b" * 64
    elif change == "legacy":
        manifest["schema"] = "strata/NativeBootstrap/1"
        del manifest["native_companions"]
        del entries[1:]
    source = {"backends/mineflayer/dist/src/worker.js": "c" * 64}
    bootstrap_name = "run/native/broker-runtime.manifest.json"
    bundle = SimpleNamespace(json=lambda name: {"source-pins.json": source,
        bootstrap_name: manifest}[name], files={"source/" + next(iter(source)): SimpleNamespace(sha256="c" * 64),
        "source-pins.json": SimpleNamespace(sha256=digest(source)),
        bootstrap_name: SimpleNamespace(sha256="d" * 64)})
    native = SimpleNamespace(executable=binary, binary_digest="a" * 64, bootstrap_digest="d" * 64,
                             profile_digest=lambda: "e" * 64, dovetail_commit="f" * 40)
    cap = {"implementation_digest": digest({"worker.js": "c" * 64}),
           "dependency_lock_digest": "1" * 64, "schema_digest": "2" * 64}
    monkeypatch.setattr(evidence, "worker_runtime_evidence", lambda *_: {})
    intent = {"source_pins": source, "plan": {"schema": "strata/M0NativeGameSmoke/5", "output": "C:/run"}}
    if change in {"missing", "duplicate", "extra", "changed"}:
        with pytest.raises((Fault, IntegrityError), match="BOOTSTRAP_COMPANION|NATIVE_GAME_EXTERNAL_PIN"):
            evidence.source_evidence(bundle, native, intent, cap)
    else:
        result = evidence.source_evidence(bundle, native, intent, cap)
        assert result.get("native_companions") == (None if change == "legacy" else pins)


def test_missing_companion_rejects_game_before_output_or_composition(companions, tmp_path, monkeypatch):
    import m0_native_game as runner
    binary, pins = companions
    (binary.parent / next(iter(pins))).unlink()
    monkeypatch.setattr(runner, "BINARY_SHA256", file_hash(binary))
    monkeypatch.setattr(runner, "run_plan", lambda *_: pytest.fail("game composition started"))
    output = tmp_path / "run"
    plan = tmp_path / "plan.json"
    plan.write_bytes(canonical({"schema": "strata/M0NativeGameSmoke/5", "output": str(output),
        "pack": {}, "worker_invocation": {}, "worker_runtime": {}, "codex": str(binary),
        "tool_projections": "unused", "model_catalog": "unused", "retention_source": {}}))
    with pytest.raises(Fault, match="NATIVE_COMPANION_MISSING"):
        runner.run(plan)
    assert not output.exists()
