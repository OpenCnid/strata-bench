"""Real owned synthetic console records lifecycle without Minecraft or save claims."""

import json
import os
from pathlib import Path
import sys
import threading
import time

import pytest

from mcbench.inventory import file_hash
from mcbench.storage import canonical
from development_server import main


@pytest.mark.parametrize("operator", [True, False])
def test_owned_console_lifecycle_records_actual_stop_source_and_exit(tmp_path, operator):
    instance = tmp_path / "instance"
    instance.mkdir()
    (instance / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    (instance / "server.properties").write_text("server-ip=127.0.0.1\nonline-mode=true\n", encoding="utf-8")
    script = instance / "console.py"
    script.write_text("import sys\nprint('Done (0.1s)! For help, type \"help\"',flush=True)\n"
                      "assert sys.stdin.readline()=='stop\\n'\n", encoding="utf-8")
    executable = Path(sys._base_executable)
    output = tmp_path / "evidence"
    plan = {"schema": "strata/DevelopmentServer/1", "target": "vanilla", "max_wall_s": 2,
        "evidence": str(output), "launch": {"executable_path": str(executable),
            "executable": {"version": "synthetic-python-console", "digest": file_hash(executable)},
            "arguments": ["-I", "-S", "-B", str(script)], "working_directory": str(instance),
            "environment": {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ},
            "reviewed_bootstrap": "cas:sha256:" + "a" * 64}}
    path = tmp_path / "plan.json"
    path.write_bytes(canonical(plan))
    done = threading.Event()
    def request():
        while not done.is_set():
            if (output / "ready.json").exists():
                (output / "stop.request").write_bytes(b"synthetic operator request")
                return
            time.sleep(.01)
    thread = threading.Thread(target=request, daemon=True) if operator else None
    if thread:
        thread.start()
    try:
        assert main([str(path)]) == 0
    finally:
        done.set()
        if thread:
            thread.join(1)
    result = json.loads((output / "result.json").read_bytes())
    events = [json.loads(line) for line in (output / "lifecycle.jsonl").read_bytes().splitlines()]
    assert result["lifecycle"]["events"] == events
    assert [e["kind"] for e in events] == ["spawn_requested", "spawned", "ready", "stop_command_attempted",
                                          "stop_command_written", "process_exited"]
    assert [e["seq"] for e in events] == list(range(1, 7))
    assert all(a["mono_ns"] <= b["mono_ns"] for a, b in zip(events, events[1:]))
    assert events[3]["trigger"] == ("operator_file" if operator else "wall_deadline")
    assert not result["lifecycle"]["clean_save_proven"] and not result["lifecycle"]["authoritative_ticks"]
    assert result["exit_code"] == 0 and not result["forced_stop"]
