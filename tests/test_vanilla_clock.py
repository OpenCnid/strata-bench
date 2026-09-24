"""Clock rejection cases and opt-in actual pinned JVM/class instrumentation."""

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault
from mcbench.vanilla_clock import CLASS_PINS, POLICY, ClockLaunch, inspect_vanilla_clock, prepare_vanilla_clock

SCOPE = {"campaign_id": "c1", "agent_id": "a1", "epoch": 1, "run_id": "clock-1"}
UUID = "12345678-1234-1234-1234-123456789abc"
MODULE = "1" * 64


def records():
    return [
        {"schema": "strata/VanillaClockStart/1", "policy": POLICY, **SCOPE, "module_sha256": MODULE,
         "pid": 12, "origin": "runServer-entry", "terminal": "stopServer-return", "period_ns": 1_000_000_000},
        *[{"schema": "strata/VanillaClockBinding/1", "class": name, "original_sha256": sha,
           "transformed_sha256": "a" * 64} for name, sha in CLASS_PINS.items()],
        {"schema": "strata/VanillaClockRunning/1"},
        {"schema": "strata/VanillaClockSample/1", "terminal": False,
         "run_elapsed_ns": 1_000_000_000, "window_start_ns": 0, "window_end_ns": 1_000_000_000,
         "first_tick_ns": 100, "last_tick_ns": 950_000_000, "completed_server_ticks": 2,
         "observed_tick_work_ns": 120, "window_ticks": 2, "window_work_ns": 120,
         "tick_work_ns": [50, 70], "avatar_tick_events": {UUID: 1}},
        {"schema": "strata/VanillaClockSample/1", "terminal": True,
         "run_elapsed_ns": 1_100_000_000, "window_start_ns": 1_000_000_000, "window_end_ns": 1_100_000_000,
         "first_tick_ns": 100, "last_tick_ns": 1_050_000_000, "completed_server_ticks": 3,
         "observed_tick_work_ns": 210, "window_ticks": 1, "window_work_ns": 90,
         "tick_work_ns": [90], "avatar_tick_events": {UUID: 2}},
    ]


def write(path, values):
    path.write_text("".join(json.dumps({"seq": i, "body": b}) + "\n" for i, b in enumerate(values, 1)), encoding="utf-8")


def inspect(path):
    return inspect_vanilla_clock(path, scope=SCOPE, module_sha256=MODULE, pid=12)


def test_counts_work_and_terminal_tail_are_exact(tmp_path):
    path = tmp_path / "clock.jsonl"
    write(path, records())
    report = inspect(path)
    assert report["completed_server_ticks"] == 3
    assert report["avatar_tick_events"] == {UUID: 2}
    assert report["observed_tick_work_ns"] == 210 and report["completed_tick_work_p95_ns"] == 90
    assert report["run_elapsed_ns"] == 1_100_000_000 and report["active_wall_s"] is None
    assert report["source_process_bound"] and not report["capacity_qualified"]


@pytest.mark.parametrize("change", [
    lambda r: r.pop(), lambda r: r.append(copy.deepcopy(r[-1])),
    lambda r: r.pop(3), lambda r: r.insert(4, copy.deepcopy(r[3])),
    lambda r: r.insert(2, copy.deepcopy(r[1])),
    lambda r: r[1].update(original_sha256="f"*64),
    lambda r: r[0].update(pid=13), lambda r: r[0].update(module_sha256="f"*64),
    lambda r: r[0].update(agent_id="foreign"), lambda r: r[0].update(epoch=True),
    lambda r: r[0].update(policy="wrong"), lambda r: r[0].update(extra="x"),
    lambda r: r[4].update(terminal=True), lambda r: r[5].update(terminal=False),
    lambda r: r[5].update(completed_server_ticks=1), lambda r: r[5].update(window_start_ns=0),
    lambda r: r[5].update(window_ticks=2), lambda r: r[5].update(window_work_ns=1),
    lambda r: r[4].update(tick_work_ns=[50]), lambda r: r[4].update(tick_work_ns=[50, 80]),
    lambda r: r[4].update(tick_work_ns=[False, 120]),
    lambda r: r[5].update(first_tick_ns=101), lambda r: r[5].update(last_tick_ns=1_100_000_001),
    lambda r: r[5].update(last_tick_ns=1), lambda r: r[5].update(avatar_tick_events={}),
    lambda r: r[5].update(avatar_tick_events={UUID: 0}),
    lambda r: r[5].update(avatar_tick_events={UUID: 4}),
    lambda r: r[4].update(avatar_tick_events={UUID: 0}),
    lambda r: r[5].update(run_elapsed_ns=1_000_000_010, window_end_ns=1_000_000_010,
                           last_tick_ns=1_000_000_005),
    lambda r: r[5].update(completed_server_ticks=2, window_ticks=0, window_work_ns=0,
                           tick_work_ns=[], observed_tick_work_ns=120, avatar_tick_events={UUID: 1}),
    lambda r: r[4].update(avatar_tick_events={"not-a-uuid": 1}),
    lambda r: r.pop(2), lambda r: r[5].update(run_elapsed_ns=float("nan")),
])
def test_invalid_or_incomplete_clock_cannot_qualify(tmp_path, change):
    values = records()
    change(values)
    path = tmp_path / "clock.jsonl"
    write(path, values)
    with pytest.raises((Fault, ValueError)):
        inspect(path)


def test_truncation_and_external_pin_reject(tmp_path):
    path = tmp_path / "clock.jsonl"
    write(path, records())
    with pytest.raises(Fault, match="VANILLA_CLOCK_CHANGED"):
        inspect_vanilla_clock(path, scope=SCOPE, module_sha256=MODULE, expected_sha256="f"*64)
    path.write_bytes(path.read_bytes().rstrip(b"\n"))
    with pytest.raises(Fault, match="VANILLA_CLOCK_INCOMPLETE"):
        inspect(path)


@pytest.fixture(scope="module")
def compiled(tmp_path_factory):
    asm = os.environ.get("STRATA_VANILLA_ASM")
    server = os.environ.get("STRATA_VANILLA_SERVER_JAR")
    if not asm or not server:
        pytest.skip("explicit pinned installed ASM and official server required")
    directory = tmp_path_factory.mktemp("vanilla-clock")
    javac = Path(shutil.which("javac"))
    receipt = prepare_vanilla_clock(javac, Path(asm), directory / "agent")
    sources = Path(__file__).parent / "java/vanillaclock"
    jar = directory / "agent/strata-vanilla-clock-0.1.0.jar"
    classes = directory / "fixtures"
    classes.mkdir()
    classpath = str(jar) + os.pathsep + str(directory / "agent/classes")
    result = subprocess.run([str(javac), "--release", "17", "-classpath", classpath,
        "-d", str(classes), *(str(p) for p in sources.glob("*.java"))], capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    return directory, jar, receipt, Path(server), classes


def test_real_java_clock_state_machine_and_pinned_class_patch(compiled):
    directory, jar, _, server, classes = compiled
    result = subprocess.run([shutil.which("java"), "-cp", os.pathsep.join(map(str,
        (classes, jar, directory / "agent/classes"))), "ClockTest", str(server)], capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout.strip() == b"clock-and-patches-pass"


def test_actual_agent_bootstrap_callback_visibility_and_terminal_reader(compiled, tmp_path):
    _, jar, receipt, _, classes = compiled
    output, config = tmp_path / "clock.jsonl", tmp_path / "clock.config"
    config.write_text("".join(f"{k}={v}\n" for k, v in (SCOPE | {"output": str(output)}).items()), encoding="utf-8")
    result = subprocess.run([shutil.which("java"), f"-javaagent:{jar}={config}", "-cp", str(classes),
                             "CallbackTest"], capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr.decode()
    report = inspect_vanilla_clock(output, scope=SCOPE, module_sha256=receipt["jar_sha256"])
    assert report["completed_server_ticks"] == 1 and report["avatar_tick_events"] == {UUID: 1}
    assert (tmp_path / "vanilla-clock-callbacks.jar").exists()
    assert report["samples"][-1]["terminal"] and not report["source_process_bound"]


def test_actual_transformer_drift_halts_before_game_class_main(compiled, tmp_path):
    _, jar, receipt, _, _ = compiled
    source = tmp_path / "MinecraftServer.java"
    source.write_text('package net.minecraft.server; public class MinecraftServer {'
                      'public static void main(String[] args) { System.out.println("UNMEASURED_GAME_RAN"); }}', encoding="utf-8")
    result = subprocess.run([shutil.which("javac"), "--release", "17", "-d", str(tmp_path), str(source)],
                            capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr.decode()
    output, config = tmp_path / "clock.jsonl", tmp_path / "clock.config"
    config.write_text("".join(f"{k}={v}\n" for k, v in (SCOPE | {"output": str(output)}).items()), encoding="utf-8")
    result = subprocess.run([shutil.which("java"), f"-javaagent:{jar}={config}", "-cp", str(tmp_path),
                             "net.minecraft.server.MinecraftServer"], capture_output=True, timeout=15)
    assert result.returncode == 126 and b"UNMEASURED_GAME_RAN" not in result.stdout
    with pytest.raises(Fault, match="VANILLA_CLOCK_INCOMPLETE"):
        inspect_vanilla_clock(output, scope=SCOPE, module_sha256=receipt["jar_sha256"])


@pytest.mark.skipif(os.name != "nt", reason="Windows held-handle launch qualification")
def test_held_extended_paths_launch_and_bind_actual_jvm(compiled, tmp_path):
    from mcbench.processes import ManagedProcess
    _, jar, receipt, _, classes = compiled
    evidence, game = tmp_path / "private", tmp_path / "game"
    evidence.mkdir()
    game.mkdir()
    java = str(Path(shutil.which("java")).resolve())
    args = ["-cp", str(classes), "CallbackTest"]
    launch = SimpleNamespace(executable_path=java, arguments=args,
                             model_dump=lambda: {"executable_path": java, "arguments": args})
    clock = ClockLaunch(SCOPE | {"agent_path": str(jar), "agent_sha256": receipt["jar_sha256"]},
                        evidence, game, launch)
    assert "\\\\?\\" not in clock.arguments[0]
    proc = ManagedProcess([java, *clock.arguments], game,
        {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}, "",
        bootstrap_python=Path(sys._base_executable))
    try:
        until = time.monotonic()+15
        while proc.poll() is None:
            assert time.monotonic() < until
            proc.job.observe_members()
            clock.observe(proc)
            time.sleep(.005)
        assert proc.process.wait(timeout=1) == 0, proc.process.stderr.read().decode()
        report = clock.finish(proc)
        assert report["completed_server_ticks"] == 1 and report["source_process_bound"]
        assert report["owned_processes"]["job"]["active_processes"] == 0
        assert report["launch_binding"]["original_pack_profile_unchanged_claim"] is False
        assert not report["capacity_qualified"]
    finally:
        if proc.poll() is None:
            proc.stop()
        proc.close()
        clock.close()
