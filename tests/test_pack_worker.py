"""Synthetic packs/runtime bytes and controlled processes; never authentic game evidence."""

import io
import json
from pathlib import Path
import threading
from types import SimpleNamespace

from pydantic import ValidationError
import pytest

from mcbench.inventory import file_hash, scan_tree
from mcbench.launch_integrity import IntegrityError
from mcbench.pack_launch import PackLaunchBinding, resolve_pack_launch
from mcbench.pack_worker import HeldPackWorker, run_pack_worker, validate_server_settings
from mcbench.provisioning import (
    PROVISION_CHECKS, ProvisioningEvidence, VanillaLaunchProfile, WORKER_CONFIG_ARGUMENT,
    parse_launch_profile,
)
from mcbench.records import FileEntry
from mcbench.storage import CAS, Database, Fault, digest
from test_provisioning import prepare_fixture
import test_worker_bundle as bundle_tests

inputs = bundle_tests.inputs
PROPERTIES = ("server-ip=127.0.0.1\nserver-port=25565\nonline-mode=true\nenable-rcon=false\n"
              "rcon.password=\nenable-command-block=false\n")


@pytest.fixture
def candidate(inputs, tmp_path):
    db = Database(tmp_path / "store/controller.sqlite")
    service, receipt, roles, old, evidence = prepare_fixture(db, CAS(db, tmp_path / "store/objects"),
                                                           tmp_path, simulation=False)
    # Fictional vanilla intake; this cannot qualify a real acquisition or source.
    db.connection.execute("UPDATE provisioning SET target='vanilla'")
    receipt.target = "vanilla"
    for item in receipt.distributions:
        item.file_id = None
        item.origin = "https://piston-data.mojang.com/fixture"
    server = Path(roles[1].root)
    (server / "server.properties").write_text(PROPERTIES)
    (server / "eula.txt").write_text("eula=true\n")
    roles[1].files = [FileEntry.model_validate(item | {"role": "server", "origin": "fixture",
        "project_id": None, "file_id": None, "license_ref": "fixture", "layer": "resolved"})
        for item in scan_tree(server)]
    bundle = bundle_tests.prepare(inputs)
    body = json.loads(Path(bundle["manifest"]).read_bytes())
    cache = tmp_path / "private-cache"
    cache.mkdir()
    (cache / "token.fixture").write_bytes(b"SYNTHETIC-SECRET-CANARY")
    profile = VanillaLaunchProfile.model_validate(old.model_dump() | {
        "schema": "strata/LaunchProfile/2", "worker_runtime": {"path": bundle["manifest"], "sha256": bundle["sha256"]},
        "worker_settings": {"host": "127.0.0.1", "port": 25565, "username": "synthetic-avatar",
            "auth_cache": str(cache), "max_wall_ms": 1000, "primitive_limit": 32},
        "update_policy": "sealed-local-bytes/no-installer/1",
        "client": old.client.model_dump() | {"executable_path": body["node"],
            "executable": {"version": "synthetic-node", "digest": file_hash(Path(body["node"]))},
            "arguments": [body["worker"], WORKER_CONFIG_ARGUMENT]}})
    imported = service.import_acquisition_receipt(receipt)
    inventory = service.verify_inventory("pack1", roles)
    yield service, profile, evidence, imported, inventory
    db.close()


def seal(candidate):
    service, profile, evidence, imported, inventory = candidate
    identity = {"is_example": False, "request_id": "pack1", "inventory_digest": inventory[11:],
                "receipt_digest": imported[11:], "launch_profile_digest": digest(profile.model_dump())}
    checks = {key: service._put("pack1", {"schema": "strata/ProvisioningCheck/1", **identity,
              "check_id": key, "result": "pass", "evidence_refs": [evidence]}) for key in PROVISION_CHECKS}
    proof = ProvisioningEvidence.model_validate({"schema": "strata/ProvisioningEvidence/1", **identity,
                                                 "checks": checks})
    return service.seal_template("pack1", profile, proof)


@pytest.fixture
def pack(candidate, tmp_path):
    lock = seal(candidate)
    candidate[0].materialize("pack1", tmp_path / "instance")
    binding = PackLaunchBinding(store=str(tmp_path / "store"), request_id="pack1", lock=lock,
                               instance=str(tmp_path / "instance"))
    (tmp_path / "state").mkdir()
    invocation = {"campaign_id": "campaign-1", "agent_id": "avatar-1", "epoch": 1, "lease_id": "lease-1",
                  "state_directory": str(tmp_path / "state"), "configuration_path": str(tmp_path / "worker.json")}
    return binding, invocation, candidate[1]


def test_two_fresh_invocations_keep_the_same_sealed_settings_and_different_scopes(pack, tmp_path):
    binding, invocation, profile = pack
    assert isinstance(parse_launch_profile(profile.model_dump()), VanillaLaunchProfile)
    first = resolve_pack_launch(binding, "client", worker_invocation=invocation)
    (tmp_path / "state-2").mkdir()
    second = resolve_pack_launch(binding, "client", worker_invocation=invocation | {"epoch": 2,
        "lease_id": "lease-2", "state_directory": str(tmp_path / "state-2"),
        "configuration_path": str(tmp_path / "worker-2.json")})
    for result in (first, second):
        config = result["worker_configuration"]
        assert all(config[key] == value for key, value in profile.worker_settings.model_dump().items())
        assert config["schema"] == "strata/DevelopmentWorker/1"
        assert config["purpose"] == "manual-conformance"
        assert result["worker_configuration_sha256"] == digest(config)
        assert result["launch"]["arguments"][1] == result["worker_configuration_path"]
        assert not result["campaign_admission"] and not result["writer_custody_qualified"]
        assert "SYNTHETIC-SECRET-CANARY" not in json.dumps(result)
    assert first["lock"] == second["lock"] == binding.lock
    assert first["worker_configuration_sha256"] != second["worker_configuration_sha256"]
    assert not Path(invocation["configuration_path"]).exists()  # Resolver is read-only.
    assert resolve_pack_launch(binding, "server")["schema"] == "strata/ResolvedPackLaunch/1"


@pytest.mark.parametrize("change", ["argv", "node", "cwd", "pin", "runtime", "port", "missing_slot"])
def test_unbound_or_changed_profile_cannot_seal(candidate, change):
    service, profile, *_ = candidate
    if change == "argv":
        profile.client.arguments.append("--unreviewed")
    elif change == "node":
        profile.client.executable_path = profile.server.executable_path
    elif change == "cwd":
        profile.client.working_directory = "mods"
    elif change == "pin":
        profile.client.executable.digest = "a" * 64
    elif change == "runtime":
        profile.worker_runtime.sha256 = "a" * 64
    elif change == "port":
        profile.worker_settings.port = 25566
    else:
        profile.client.arguments[-1] = "stale-run-config.json"
    with pytest.raises((Fault, IntegrityError)):
        seal(candidate)
    assert service.status("pack1")["state"] == "VERIFIED"


@pytest.mark.parametrize("change", ["settings_override", "epoch_bool", "epoch_zero", "missing", "server_role",
    "config_exists", "state_not_empty", "state_cache", "config_state", "config_instance", "path_traversal",
    "config_stream", "config_trailing_dot"])
def test_invalid_or_reused_invocation_refuses_before_config_or_process(pack, change):
    binding, invocation, profile = pack
    role = "client"
    if change == "settings_override":
        invocation["primitive_limit"] = 100000
    elif change in {"epoch_bool", "epoch_zero"}:
        invocation["epoch"] = True if change == "epoch_bool" else 0
    elif change == "missing":
        invocation = None
    elif change == "server_role":
        role = "server"
    elif change == "config_exists":
        Path(invocation["configuration_path"]).write_text("preserve")
    elif change == "state_not_empty":
        (Path(invocation["state_directory"]) / "old-journal").write_text("preserve")
    elif change == "state_cache":
        invocation["state_directory"] = profile.worker_settings.auth_cache
    elif change == "config_state":
        invocation["configuration_path"] = str(Path(invocation["state_directory"]) / "config.json")
    elif change == "config_instance":
        invocation["configuration_path"] = str(Path(binding.instance) / "config.json")
    elif change in {"config_stream", "config_trailing_dot"}:
        invocation["configuration_path"] += ":stream" if change == "config_stream" else "."
    else:
        invocation["state_directory"] += "/../state"
    with pytest.raises((Fault, IntegrityError, ValidationError)):
        resolve_pack_launch(binding, role, worker_invocation=invocation)


@pytest.mark.parametrize("suffix", ["server-port=25565\n", "server-port : 25565\n", "server\\u002dport=25566\n",
                                   "server-port=25565\\\n", " server-port=25566\n"])
def test_ambiguous_java_property_forms_do_not_fake_an_endpoint_match(candidate, suffix):
    with pytest.raises(Fault, match="WORKER_SERVER_SETTINGS_MISMATCH"):
        validate_server_settings((PROPERTIES + suffix).encode(), candidate[1].worker_settings)


def test_actual_vanilla_separator_escaping_is_decoded_without_key_aliases(candidate):
    raw = (PROPERTIES + r"level-type=minecraft\:normal" + "\n" + r"motd=equals\=colon\:space\ here" + "\n").encode()
    properties = validate_server_settings(raw, candidate[1].worker_settings)
    assert properties["level-type"] == "minecraft:normal" and properties["motd"] == "equals=colon:space here"


def fake_process_factory(calls, *, exit_code=0, server_ready=True, server_fatal=False, worker_error=False):
    class Process:
        def __init__(self, argv, cwd, environment, prompt, *, interactive=False, bootstrap_python=None):
            assert bootstrap_python is not None and bootstrap_python.name == "python.exe"
            if worker_error and len(calls) == 2:
                if worker_error == "interrupt":
                    raise KeyboardInterrupt("synthetic operator interruption")
                raise OSError("synthetic worker construction failure")
            self.argv, self.closed = argv, False
            self.code = None if interactive else exit_code
            output = (b'[00:00:00] [Server thread/INFO]: Done (1.0s)! For help, type "help"\n'
                      if interactive and server_ready else b"synthetic output\n")
            error = (b"[00:00:00] [Server thread/ERROR]: Exception in server tick loop\n"
                     if interactive and server_fatal else b"")
            self.process = SimpleNamespace(stdout=io.BytesIO(output), stderr=io.BytesIO(error))
            self.job = SimpleNamespace(accounting=lambda: {"active_processes": int(self.code is None), "total_processes": 1,
                                                           "terminated_processes": 0})
            if interactive:
                # This would break the previous full command's second fresh
                # materialization check after server startup.
                (Path(cwd) / "world").mkdir()
                (Path(cwd) / "world/level.dat").write_bytes(b"synthetic generated state")
            calls.append((self, str(cwd), environment, prompt))

        def poll(self):
            return self.code

        def send_input(self, value):
            assert value == "stop\n" and self.code is None
            self.code = 0

        def stop(self):
            self.code = 125

        def close(self):
            # The complete runtime must still be held at owned cleanup.
            with pytest.raises(PermissionError):
                with open(self.argv[0], "r+b"):
                    pytest.fail("released runtime before process closure")
            self.closed = True
    return Process


@pytest.mark.parametrize("fail", [False, True])
def test_held_configuration_and_runtime_outlive_owned_cleanup(pack, monkeypatch, fail):
    import mcbench.pack_worker as module
    binding, invocation, _ = pack
    calls = []
    monkeypatch.setattr(module, "ManagedProcess", fake_process_factory(calls))
    try:
        with HeldPackWorker(binding, invocation) as worker:
            with pytest.raises(PermissionError):
                Path(invocation["configuration_path"]).write_text("replace")
            worker.start(preflight=True)
            exposed = worker.resolved
            exposed["launch"]["arguments"] = ["substitute"]
            worker.start()
            assert calls[-1][0].argv[1:] == worker.resolved["launch"]["arguments"]
            assert worker.receipt()["held_through_owned_stop"]
            with pytest.raises(Fault, match="WORKER_LAUNCH_ALREADY_STARTED"):
                worker.start()
            if fail:
                raise RuntimeError("synthetic body failure")
    except RuntimeError:
        assert fail
    assert len(calls) == 2 and all(item[0].closed for item in calls)
    Path(invocation["configuration_path"]).write_text("released after owned close")


@pytest.mark.parametrize("exit_code,import_only", [(0, True), (1, True), (0, False)])
def test_operator_command_retains_result_and_uses_only_selected_launch_mode(pack, tmp_path, monkeypatch, exit_code, import_only):
    import mcbench.pack_worker as module
    binding, invocation, _ = pack
    calls = []
    monkeypatch.setattr(module, "ManagedProcess", fake_process_factory(calls, exit_code=exit_code))
    output = tmp_path / "evidence"
    if exit_code:
        with pytest.raises(Fault, match="WORKER_PROCESS_FAILED"):
            run_pack_worker(binding, invocation, output, import_only=import_only)
    else:
        assert run_pack_worker(binding, invocation, output, import_only=import_only)["status"] == "stopped_unqualified"
    result = json.loads((output / "result.json").read_bytes())
    assert result["mode"] == ("import-only" if import_only else "owned-server-worker") and not result["campaign_admission"]
    assert len(calls) == (1 if import_only else 3) and calls[0][0].argv[-1] == "--check-vanilla-runtime"
    if not import_only:
        assert calls[2][0].argv[-1] == invocation["configuration_path"]
        assert result["server_stop_sent"] and "server_forced_stop" not in result
        assert set(result["receipt"]["owned_processes"]) == {"preflight", "server", "worker"}
        assert result["receipt"]["server_launch_digest"] == result["server_launch_digest"]
        assert (Path(binding.instance) / "server/world/level.dat").exists()
    assert all(call[0].closed for call in calls)
    assert not any(Path(invocation["state_directory"]).iterdir())


@pytest.mark.parametrize("failure", ["readiness", "worker-construction", "worker-interrupt", "server-log"])
def test_joint_failure_retains_evidence_and_stops_the_owned_server(pack, tmp_path, monkeypatch, failure):
    import mcbench.pack_worker as module
    binding, invocation, _ = pack
    calls = []
    monkeypatch.setattr(module, "ManagedProcess", fake_process_factory(calls,
        server_ready=failure != "readiness", server_fatal=failure == "server-log",
        worker_error="interrupt" if failure == "worker-interrupt" else failure == "worker-construction"))
    if failure == "readiness":
        monkeypatch.setattr(module, "SERVER_READY_SECONDS", 0)
    output = tmp_path / "failed-evidence"
    with pytest.raises((Fault, OSError, KeyboardInterrupt)):
        run_pack_worker(binding, invocation, output)
    result = json.loads((output / "result.json").read_bytes())
    assert result["status"] == "fail" and "receipt" not in result
    assert result["server_stop_sent"] and "server_forced_stop" not in result
    assert len(calls) == (3 if failure == "server-log" else 2)
    assert all(call[0].closed and call[0].poll() == 0 for call in calls)
    assert (output / "server-launch.json").is_file()


def test_server_cannot_start_before_import_or_twice(pack, monkeypatch):
    import mcbench.pack_worker as module
    binding, invocation, _ = pack
    calls = []
    monkeypatch.setattr(module, "ManagedProcess", fake_process_factory(calls))
    with HeldPackWorker(binding, invocation, own_server=True) as worker:
        with pytest.raises(Fault, match="WORKER_PREFLIGHT_INCOMPLETE"):
            worker.start_server()
        worker.start(preflight=True)
        server = worker.start_server()
        with pytest.raises(Fault, match="WORKER_LAUNCH_ALREADY_STARTED"):
            worker.start_server()
        exposed = worker.server_resolved
        exposed["launch"]["arguments"].append("untrusted mutation")
        assert exposed != worker.server_resolved
        server.send_input("stop\n")
        with pytest.raises(Fault, match="SERVER_PROCESS_UNAVAILABLE"):
            worker.start()


def test_server_lifetime_expires_independently_of_a_blocked_owner():
    from mcbench.pack_worker import _ServerDeadline
    stopped = threading.Event()
    deadline = _ServerDeadline(SimpleNamespace(stop=stopped.set), .02)
    assert stopped.wait(2)
    deadline.close()
    assert deadline.expired.is_set()


def test_server_stop_timeout_retains_forced_cleanup_failure(pack, tmp_path, monkeypatch):
    import mcbench.pack_worker as module
    binding, invocation, _ = pack
    calls = []
    factory = fake_process_factory(calls)
    def create(*args, **kwargs):
        process = factory(*args, **kwargs)
        if kwargs.get("interactive"):
            process.send_input = lambda _value: None
        return process
    monkeypatch.setattr(module, "ManagedProcess", create)
    monkeypatch.setattr(module, "SERVER_STOP_SECONDS", 0)
    output = tmp_path / "timeout-evidence"
    with pytest.raises(Fault, match="SERVER_STOP_TIMEOUT"):
        run_pack_worker(binding, invocation, output)
    result = json.loads((output / "result.json").read_bytes())
    assert result["status"] == "fail" and result["server_forced_stop"]
    assert "receipt" not in result and all(call[0].closed for call in calls)
    assert calls[1][0].poll() == 125


def test_process_construction_failure_releases_leases_without_a_stop_receipt(pack, monkeypatch):
    import mcbench.pack_worker as module
    binding, invocation, _ = pack
    def fail(*_, **__):
        raise OSError("synthetic process construction failure")
    monkeypatch.setattr(module, "ManagedProcess", fail)
    with pytest.raises(OSError):
        with HeldPackWorker(binding, invocation) as worker:
            with pytest.raises(Fault, match="WORKER_LAUNCH_NOT_HELD"):
                worker.receipt()
            worker.start()
    with open(invocation["configuration_path"], "r+b"):
        pass


def test_late_state_insertion_and_forced_child_exit_cannot_claim_a_clean_launch(pack, monkeypatch):
    import mcbench.pack_worker as module
    binding, invocation, _ = pack
    calls = []
    monkeypatch.setattr(module, "ManagedProcess", fake_process_factory(calls))
    with HeldPackWorker(binding, invocation) as worker:
        process = worker.start(preflight=True)
        process.job.accounting = lambda: {"active_processes": 0, "total_processes": 2, "terminated_processes": 1}
        with pytest.raises(Fault, match="WORKER_LAUNCH_STOP_UNPROVEN"):
            worker.receipt()
        (Path(invocation["state_directory"]) / "old-journal").write_text("retain")
        with pytest.raises(Fault, match="WORKER_INVOCATION_NOT_FRESH"):
            worker.start()
        assert len(calls) == 1
