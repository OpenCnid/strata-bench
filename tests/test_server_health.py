"""Synthetic logs and real disposable Python processes, not Minecraft proof."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mcbench import server_health
from mcbench.server_health import critical_signal, inspect_server_log
from mcbench.storage import Fault


@pytest.mark.parametrize(("line", "code"), [
    (b"[06:27:35] [Server thread/ERROR] [minecraft/MinecraftServer]: Encountered an unexpected exception\n", "SERVER_CRASH"),
    (b"[06:27:35] [Server thread/ERROR]: Exception in server tick loop\n", "SERVER_CRASH"),
    (b"[06:27:35] [Server thread/FATAL] [ne.mi.co.ForgeMod/]: Preparing crash report with UUID synthetic\n", "SERVER_CRASH"),
    (b"[06:27:35] [Server thread/ERROR] [minecraft/MinecraftServer]: This crash report has been saved to: private-canary\n", "SERVER_CRASH"),
    (b"[06:28:53] [Server Watchdog/ERROR] [minecraft/ServerWatchdog]: Considering it to be crashed, server will forcibly shutdown.\n", "SERVER_WATCHDOG_FAILURE"),
    (b"[06:27:53] [Server thread/ERROR] [minecraft/LevelChunk]: A BlockEntity type fixture has thrown an exception trying to write state. It will not persist, Report this to the mod author\n", "BLOCK_ENTITY_SAVE_FAILED"),
    (b"[06:27:53] [IO thread/ERROR] [minecraft/IOWorker]: Failed to store chunk\n", "WORLD_SAVE_FAILED"),
    (b"[06:27:53] [IO thread/ERROR] [minecraft/IOWorker]: Failed to save chunk\n", "WORLD_SAVE_FAILED"),
])
def test_pinned_failure_signatures(line, code):
    assert critical_signal(line) == code
    assert critical_signal(b"\x1b[31m" + line.rstrip(b"\n") + b"\x1b[0m\r\n") == code


@pytest.mark.parametrize("line", [
    b'[06:00:00] [Server thread/INFO]: Done (1.234s)! For help, type "help"\n',
    b"[06:00:00] [Server thread/INFO]: [Player] Encountered an unexpected exception\n",
    b"[06:00:00] [Server thread/INFO]: [Player] [Server thread/ERROR]: Exception in server tick loop\n",
    b"[06:00:00] [Server thread/INFO]: Saving worlds\n",
    b"[06:00:00] [Server thread/ERROR] [fixture/plugin]: Optional integration absent\n",
    b"previous stack trace mentions Preparing crash report\n",
])
def test_chat_and_noncritical_messages_do_not_become_crash_evidence(line, tmp_path):
    path = tmp_path / "log"
    path.write_bytes(line)
    report = inspect_server_log(path)
    assert report["result"] == "pass"
    assert report["scope"] == "recognized_log_signatures_only"
    assert not report["clean_save_proven"] and not report["snapshot_integrity_proven"]
    assert report["gate_result"] == "not_run"


def test_raw_byte_offsets_hashes_and_no_private_log_text_in_summary(tmp_path):
    first = b"non-UTF8 private bytes \x81\r\n"
    crash = b"[06:27:35] [Server thread/ERROR]: This crash report has been saved to: PRIVATE-CANARY\n"
    data = first + crash
    path = tmp_path / "log"
    path.write_bytes(data)
    report = inspect_server_log(path)
    assert report["sha256"] == hashlib.sha256(data).hexdigest()
    assert report["bytes"] == len(data) and report["lines"] == 2
    assert report["critical_signals"] == [{"code": "SERVER_CRASH", "line": 2,
        "byte_offset": len(first), "line_sha256": hashlib.sha256(crash).hexdigest()}]
    assert "PRIVATE-CANARY" not in json.dumps(report)
    assert report["result"] == "fail"


@pytest.mark.parametrize("data", [b"truncated final record", b"x" * 65536 + b"\n"],
                         ids=["truncated", "overlong"])
def test_truncated_or_overlong_log_cannot_claim_complete_scan(data, tmp_path):
    path = tmp_path / "log"
    path.write_bytes(data)
    with pytest.raises(Fault, match="SERVER_LOG_INCOMPLETE"):
        inspect_server_log(path)


def test_missing_oversized_and_signal_overflow_fail_closed(tmp_path, monkeypatch):
    path = tmp_path / "log"
    with pytest.raises(Fault, match="SERVER_LOG_UNAVAILABLE"):
        inspect_server_log(path)
    path.write_bytes(b"x" * 17)
    monkeypatch.setattr(server_health, "MAX_BYTES", 16)
    with pytest.raises(Fault, match="SERVER_LOG_UNAVAILABLE"):
        inspect_server_log(path)
    monkeypatch.setattr(server_health, "MAX_BYTES", 1024)
    monkeypatch.setattr(server_health, "MAX_SIGNALS", 1)
    path.write_bytes(b"[06:00:00] [Server thread/ERROR]: Exception in server tick loop\n" * 2)
    with pytest.raises(Fault, match="SERVER_LOG_QUOTA"):
        inspect_server_log(path)


@pytest.mark.parametrize("failure", [None, "crash", "partial"])
def test_actual_zero_exit_launcher_cannot_hide_crash_or_incomplete_log(tmp_path, failure):
    root = Path(__file__).resolve().parents[1]
    script = tmp_path / "synthetic-server.py"
    script.write_text('import sys\nprint(\'[06:00:00] [Server thread/INFO]: '
                      'Done (0.1s)! For help, type "help"\',flush=True)\n'
                      'assert sys.stdin.readline()=="stop\\n"\n'
                      + ('print("[06:00:01] [Server thread/ERROR]: Exception in server tick loop")\n'
                         if failure == "crash" else 'sys.stdout.write("partial")\n'
                         if failure == "partial" else 'print("[06:00:01] [Server thread/INFO]: Saving worlds")\n'),
                      encoding="utf-8")
    (tmp_path / "eula.txt").write_text("eula=true\n")  # Synthetic fixture only, no game.
    (tmp_path / "server.properties").write_text("server-ip=127.0.0.1\nonline-mode=true\n")
    executable = Path(sys.executable)
    environment = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
    plan = {"schema": "strata/DevelopmentServer/1", "target": "vanilla", "max_wall_s": 1,
            "evidence": str(tmp_path / "evidence"), "launch": {
                "executable": {"version": "synthetic-python", "digest": hashlib.sha256(executable.read_bytes()).hexdigest()},
                "executable_path": str(executable), "arguments": ["-I", str(script)],
                "working_directory": str(tmp_path), "environment": environment,
                "reviewed_bootstrap": "cas:sha256:" + "a" * 64}}
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    run = subprocess.run([sys.executable, str(root / "tools/development_server.py"), str(plan_path)],
                         cwd=root, capture_output=True, timeout=20)
    result = json.loads((tmp_path / "evidence/result.json").read_bytes())
    assert result["exit_code"] == 0 and result["stop_sent"] and not result["forced_stop"]
    assert not result["clean_save_proven"] and result["gate_result"] == "not_run"
    if failure is None:
        assert run.returncode == 0, run.stderr
        assert result["status"] == "stopped_unqualified"
    else:
        assert run.returncode == 1 and result["status"] == "fail"
        assert result["error"] == ("SERVER_RUNTIME_FAILURE" if failure == "crash" else "SERVER_LOG_INCOMPLETE")
