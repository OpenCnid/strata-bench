"""Synthetic profile/owned-process checks; not Forge qualification."""

import json
import sys
from types import SimpleNamespace

import pytest

import e9e_cold_start as cold
from mcbench.inventory import file_hash
from mcbench.processes import ManagedProcess
from mcbench.storage import Fault


@pytest.mark.parametrize("change", [None, "prefix", "missing_class", "missing_read", "wrong_index", "refused"])
def test_runtime_data_requires_actual_pinned_class_and_read_evidence(change):
    report = {"policy": "synthetic", "jar_sha256": "a" * 64, "index_sha256": "b" * 64,
              "inputs": [{"name": n, "sha256": "c" * 64} for n in ("whitelist.txt", "blacklist.txt", "contributorRevolvers.json")]}
    lines = ["STRATA_FIXED_DATA_READY/1 " + report["index_sha256"],
        "STRATA_FIXED_DATA_BOUND/1 com/portingdeadmods/cable_facades/CFConfig 601b70c83a14debbb5e4679196a319c1a31eab4d4b008cd33b1feca2551bda0d",
        "STRATA_FIXED_DATA_BOUND/1 blusunrize/immersiveengineering/ImmersiveEngineering$ThreadContributorSpecialsDownloader b47bfd98a885800760e9e7d7c24d60ec2d4e89da6cbc1ed9ad1e82a46283e2fb",
        *("STRATA_FIXED_DATA_READ/1 " + r["name"] + " " + r["sha256"] for r in report["inputs"])]
    if change == "prefix":
        lines = ["[thread/INFO] [STDERR]: " + line for line in lines]
    elif change == "missing_class":
        del lines[1]
    elif change == "missing_read":
        lines.pop()
    elif change == "wrong_index":
        lines[0] += "changed"
    elif change == "refused":
        lines.append("STRATA_FIXED_DATA_REFUSED/1")
    raw = ("\n".join(lines) + "\n").encode()
    if change in {None, "prefix"}:
        result = cold.inspect_runtime_data_log(raw, report)
        assert len(result["bound_classes"]) == 2 and len(result["read_inputs"]) == 3
        assert result["all_runtime_downloads_qualified"] is False
    else:
        with pytest.raises(Fault, match="RUNTIME_DATA_EXECUTION"):
            cold.inspect_runtime_data_log(raw, report)


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    root, output = tmp_path / "game", tmp_path / "evidence"
    for name in cold.PINS:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic byte pin")
    for folder in ("kubejs/startup_scripts", "kubejs/server_scripts"):
        (root / folder).mkdir(parents=True)
        (root / folder / "fixture.js").write_bytes(b"synthetic script")
    monkeypatch.setattr(cold, "PINS", {p: file_hash(root / p) for p in cold.PINS})
    (root / "eula.txt").write_text("eula=true\n")  # Synthetic bytes, no terms acceptance.
    (root / "server.properties").write_text(
        "server-ip=127.0.0.1\nserver-port=25603\nonline-mode=true\n"
        "level-name=world\nenable-rcon=false\nrcon.password=\nenable-query=false\nenable-command-block=false\n"
    )
    monkeypatch.setattr(cold, "inspect_e9e_mode", lambda *a, **k: {"file_result": "pass"})

    class Socket:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def setsockopt(self, *args):
            pass

        def bind(self, address):
            assert address == ("127.0.0.1", 25603)

    monkeypatch.setattr(cold.socket, "socket", Socket)
    return root, output


@pytest.mark.parametrize(
    "change",
    [None, "pin", "world", "occupied", "overlap", "eula", "online", "rcon", "duplicate", "mode"],
)
def test_preflight_exact_profile_or_no_output(inputs, monkeypatch, change):
    root, output = inputs
    if change == "pin":
        (root / cold.ARGS).write_bytes(b"different launch")
    elif change == "world":
        (root / "world").mkdir()
    elif change == "occupied":
        output.mkdir()
    elif change == "overlap":
        output = root / "evidence"
    elif change == "eula":
        (root / "eula.txt").write_text("eula=false\n")
    elif change in {"online", "rcon", "duplicate"}:
        p = root / "server.properties"
        text = p.read_text()
        text = (
            text.replace("online-mode=true", "online-mode=false")
            if change == "online"
            else text.replace("enable-rcon=false", "enable-rcon=true")
            if change == "rcon"
            else text + "server-port=25603\n"
        )
        p.write_text(text)
    elif change == "mode":
        monkeypatch.setattr(cold, "inspect_e9e_mode", lambda *a: {"file_result": "fail"})
    if change:
        with pytest.raises(Fault):
            cold.validate(root, output, initial=True)
    else:
        assert cold.validate(root, output, initial=True) == (root, output)
        (root / "world").mkdir()
        assert cold.validate(root, output, initial=False) == (root, output)
    if change != "occupied":
        assert not output.exists()


@pytest.mark.parametrize("failure", [False, True, "watchdog"])
def test_owned_process_stop_and_failed_start_retained(inputs, monkeypatch, failure):
    root, output = inputs
    process = []
    if failure == "watchdog":
        timer = cold.threading.Timer
        monkeypatch.setattr(cold.threading, "Timer", lambda seconds, callback: timer(0.5, callback))

    def factory(argv, cwd, environment, prompt, **kwargs):
        assert argv[1:] == [
            "-XX:ActiveProcessorCount=4",
            "-Xms2G",
            "-Xmx5G",
            "@" + cold.ARGS,
            "nogui",
        ]
        assert "OPENAI_API_KEY" not in environment
        assert (output / "spool").is_dir()
        code = (
            "raise SystemExit(1)"
            if failure
            else 'import sys; print(\'Done (0.1s)! For help, type "help"\',flush=True); assert sys.stdin.readline()=="stop\\n"'
        )
        if failure == "watchdog":
            code = "import time; time.sleep(60)"
        p = ManagedProcess([sys.executable, "-I", "-S", "-c", code], cwd, {}, prompt, **kwargs)
        process.append(p)
        return p

    monkeypatch.setattr(cold, "ManagedProcess", factory)
    monkeypatch.setattr(
        cold,
        "first_start",
        lambda *a: None
        if failure
        else (
            None,
            SimpleNamespace(server_boot_id="synthetic-boot"),
            SimpleNamespace(launch_identity=SimpleNamespace(pid=process[0].process.pid)),
        ),
    )
    monkeypatch.setattr(cold, "bind_identity", lambda *a: {"synthetic": True})

    def inspect(*args):
        return {"synthetic": True}

    monkeypatch.setattr(cold, "inspect_authenticated_spool", inspect)
    # A synthetic producer file only; authenticated-spool behavior has its own
    # real Java/Python conformance suite. It is not simulated as authenticated.
    original_write = cold.write

    def write(path, body):
        original_write(path, body)
        if path.name == "launch.json":
            (output / "spool/fixture.authenticated.jsonl").write_bytes(b"fixture\n")

    monkeypatch.setattr(cold, "write", write)
    if failure:
        with pytest.raises(Fault):
            cold.run(root, output, campaign="fixture", epoch=1, initial=True)
    else:
        assert cold.run(root, output, campaign="fixture", epoch=1, initial=True)["status"] == "pass"
    result = json.loads((output / "result.json").read_bytes())
    assert result["status"] == ("fail" if failure else "pass")
    assert result["terminal_job"]["active_processes"] == 0
    assert result["forced_stop"] is (failure == "watchdog")
    assert ("error_code" in result) is bool(failure)
    assert process[0].poll() is not None
