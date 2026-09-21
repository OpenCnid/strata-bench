"""Operator native graphics/heap shutdown discrimination on fresh non-input desktops.

At most three distinct finite profiles per invocation; no Minecraft, inference,
desktop switching or input injection. Measures the unchanged production guardian.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import time

from mcbench import desktop_process, process_guard, processes, process_observer, process_resources
from mcbench.desktop_process import DesktopApi, DesktopProcess
from mcbench.native_settings import strict_json
from mcbench.process_guard import AttachedJava, inspect_process
from mcbench.storage import Fault, reject_links, require
import probe_guard_memory as memory

PROFILES = {"context": (0, 0, False, "none"), "textures": (0, 256, False, "none"),
            "combined": (3072, 256, False, "none"), "combined-large": (3072, 1024, False, "none"),
            "context-audio": (0, 0, True, "none"), "combined-large-audio": (3072, 1024, True, "none"),
            "combined-file-handles": (3072, 1024, True, "channels-2048"),
            "combined-file-mappings": (3072, 1024, True, "maps-2048")}


def selected_profiles(names):
    require(1 <= len(names) <= 3 and len(set(names)) == len(names)
            and all(name in PROFILES for name in names), "GRAPHICS_PROFILE_INVALID")
    return [(name, *PROFILES[name]) for name in names]


def validate(value, *, scope, pid, heap, texture, ready, audio=False, file_mode="none"):
    require(type(value) is dict and value.get("schema") == "strata/GuardianRenderFixture/3"
            and value.get("scope") == scope and type(value.get("pid")) is int
            and value["pid"] == pid and value.get("minecraft") is False
            and value.get("visible") is False and type(value.get("heap_mib")) is int
            and value["heap_mib"] == heap and type(value.get("texture_mib")) is int
            and value["texture_mib"] == texture and value.get("audio") is audio
            and file_mode in ("none", "channels-2048", "maps-2048")
            and value.get("file_mode") == file_mode,
            "GRAPHICS_FIXTURE_BINDING")
    if ready:
        require(value.get("status") == "ready" and value.get("resources_held") is True
                and type(value.get("frames")) is int and value["frames"] == 20
                and value.get("red_samples") == [64, 191] * 10
                and all(type(value.get(key)) is str and 0 < len(value[key]) < 512
                        for key in ("gl_version", "gl_vendor", "gl_renderer")),
                "GRAPHICS_FIXTURE_NOT_READY")
        if texture:
            require(type(value.get("gpu_free_kib_before")) is int
                    and value["gpu_free_kib_before"] >= (2048 + texture) * 1024
                    and type(value.get("gpu_free_kib_loaded")) is int
                    and value["gpu_free_kib_loaded"] >= 2048 * 1024,
                    "GRAPHICS_MEMORY_HEADROOM")
        if audio:
            require(value.get("audio_state") == "playing" and value.get("silent_pcm") is True
                    and type(value.get("source_gain")) is int and value["source_gain"] == 0
                    and all(type(value.get(key)) is str and 0 < len(value[key]) < 512
                            for key in ("al_version", "al_renderer", "al_device")),
                    "SILENT_AUDIO_NOT_READY")
        if file_mode != "none":
            expected = {"file_resources_checked": 2048, "fixture_file_bytes": 65536,
                        "mapped_view_bytes": 2048 * 65536 if file_mode == "maps-2048" else 0}
            require(all(type(value.get(key)) is int and value[key] == count
                        for key, count in expected.items()) and value.get("file_access") == "read-only",
                    "FILE_RESOURCES_NOT_READY")


def wait_report(path, child, deadline):
    while time.monotonic() < deadline:
        require(child.poll() is None and child.reason is None, "GRAPHICS_FIXTURE_EXITED")
        child.job.observe_members()
        require(min(memory.memory_status().values()) >= memory.HEADROOM, "DESKTOP_MEMORY_HEADROOM")
        require(not (path.parent / "terminal.json").exists(), "GRAPHICS_FIXTURE_FAILED")
        if path.exists():
            require(path.is_file() and path.stat().st_size <= 32768, "GRAPHICS_FIXTURE_QUOTA")
            return strict_json(path.read_bytes())
        time.sleep(.01)
    raise Fault("GRAPHICS_FIXTURE_DEADLINE")


def sample(java, classpath, root, name, heap, texture, audio=False, file_mode="none", *,
           resource_observer=False, hold_seconds=0):
    started, parent_cpu = time.perf_counter_ns(), time.process_time_ns()
    require(type(hold_seconds) is int and hold_seconds in (0, 5), "FIXTURE_HOLD_INVALID")
    require(PROFILES.get(name) == (heap, texture, audio, file_mode), "GRAPHICS_PROFILE_INVALID")
    memory.admit([max(16, heap)], memory.memory_status())
    root.mkdir()
    scope = secrets.token_hex(16)
    arguments = ["-Xms64m", f"-Xmx{heap + 512}m", "-XX:+UseG1GC", "-cp", classpath,
                 "GuardianRenderFixture", str(root), str(heap), str(texture), scope,
                 str(audio).lower(), file_mode]
    argfile = root / "arguments.txt"
    argfile.write_text("\n".join('"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'
                                 for x in arguments), encoding="utf-8")
    result = {"profile": name, "heap_mib": heap, "texture_mib": texture,
              "status": "incomplete", "stop_result": "not_run", "cleanup_confirmed": False,
              "scope": scope, "audio": audio, "file_mode": file_mode,
              "max_wall_ms": 45000, "guardian_wait_bound_ms": 500,
              "resource_observer": resource_observer, "hold_seconds": hold_seconds}
    memory.publish(root / "intent.json", result)
    before = DesktopApi().input_name()
    environment = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
    # Native extraction uses a private per-case TEMP, not any shared game/profile directory.
    temp = root / "temp"
    temp.mkdir()
    environment.update(TEMP=str(temp), TMP=str(temp))
    if audio:
        environment.update(ALSOFT_LOGLEVEL="3", ALSOFT_LOGFILE=str(root / "openal.log"))
    child = guard = observer = None
    try:
        child = DesktopProcess([str(java), "@" + str(argfile)], root, environment, max_wall_ms=45000)
        boot = wait_report(root / "boot.json", child, child.deadline)
        validate(boot, scope=scope, pid=child.pid, heap=heap, texture=texture, audio=audio,
                 file_mode=file_mode, ready=False)
        guard = AttachedJava(inspect_process(child.pid), deadline=child.deadline)
        armed = root / "armed.pending"
        with armed.open("xb") as stream:
            stream.write(scope.encode("ascii"))
            stream.flush()
            os.fsync(stream.fileno())
        armed.rename(root / "armed")
        ready = wait_report(root / "ready.json", child, child.deadline)
        validate(ready, scope=scope, pid=child.pid, heap=heap, texture=texture, audio=audio,
                 file_mode=file_mode, ready=True)
        result["fixture"] = ready
        if resource_observer:
            observer = process_observer.ExitObserver(child.pid, root / "absent-supervisor.jsonl",
                root / "exit-observer.jsonl", expected_identity=guard.process.identity)
        until = time.monotonic() + hold_seconds
        while time.monotonic() < until:
            require(child.poll() is None and child.reason is None
                    and not (root / "terminal.json").exists(), "GRAPHICS_FIXTURE_EXITED")
            time.sleep(.02)
        result["memory_loaded"] = memory.process_memory(guard.process)
        require(result["memory_loaded"]["private_bytes"] >= heap * memory.MIB,
                "FIXTURE_ALLOCATION_MISSING")
        require(child.reason is None and child.poll() is None
                and not (root / "terminal.json").exists(), "GRAPHICS_FIXTURE_EXITED")
        try:
            guard.terminate()
            result["stop_result"] = "pass"
        except Fault as error:
            result["stop_result"] = "fail"
            result["stop_error_code"] = error.code
        result["termination_timing"] = guard.termination_timing
        # Late terminal observation is cleanup only; preserve any original failure.
        require(guard.process.exited(5000), "FIXTURE_CLEANUP_UNCONFIRMED")
        result["status"] = "measured"
    except Exception as error:
        result["error_code"] = error.code if isinstance(error, Fault) else type(error).__name__
    finally:
        result["cleanup_errors"] = []
        def cleanup(operation):
            try:
                operation()
            except Exception as error:
                result["cleanup_errors"].append(error.code if isinstance(error, Fault) else type(error).__name__)
        if child:
            cleanup(child.stop)
            def terminal():
                until = time.monotonic() + 5
                while time.monotonic() < until:
                    counts, handles = child.job.accounting(), child.job.member_status()
                    result["outer_job"], result["outer_handles"] = counts, handles
                    if (counts["active_processes"] == 0 and counts["total_processes"] > 0
                            and counts["total_processes"] == handles["held_processes"]
                            == handles["signaled_processes"]):
                        result["cleanup_confirmed"] = True
                        return
                    time.sleep(.01)
                raise Fault("FIXTURE_CLEANUP_UNCONFIRMED")
            cleanup(terminal)
        if guard:
            cleanup(guard.close)
        if child:
            result["outer_stop_reason"] = child.reason
            cleanup(child.close)
        if observer:
            # The guardian stop has already finished; never join before termination.
            observer.thread.join(.3)
            result["observer"] = observer.finish()
            if result["observer"]["status"] != "pass":
                result["status"] = "incomplete"
        try:
            result["input_desktop_unchanged"] = DesktopApi().input_name() == before
        except Fault:
            result["input_desktop_unchanged"] = False
        if (not result["input_desktop_unchanged"] or result["cleanup_errors"]
                or not result["cleanup_confirmed"] or result.get("outer_stop_reason") is not None):
            result["status"] = "incomplete"
        result["sample_elapsed_ns"] = time.perf_counter_ns() - started
        result["sample_parent_cpu_ns"] = time.process_time_ns() - parent_cpu
        memory.publish(root / "result.json", result)
    return result


def run(java, classpath_file, output, names, *, resource_observer=False, hold_seconds=0):
    profiles = selected_profiles(names)
    require(os.name == "nt", "WINDOWS_REQUIRED")
    repository = Path(__file__).resolve().parents[1]
    for path in (java, classpath_file, output):
        require(path.is_absolute(), "UNSAFE_PATH")
        reject_links(path)
    require(not output.exists() and not output.is_relative_to(repository), "PRIVATE_FRESH_OUTPUT_REQUIRED")
    require(java.name.casefold() == "java.exe" and java.is_file()
            and classpath_file.is_file() and classpath_file.stat().st_size <= 131072,
            "PREREQUISITE_MISSING")
    classpath = classpath_file.read_text(encoding="utf-8").strip()
    require(classpath and "\n" not in classpath and "\r" not in classpath, "CLASSPATH_INVALID")
    artifacts = []
    for i, raw in enumerate(classpath.split(os.pathsep)):
        path = Path(raw)
        require(path.is_absolute(), "CLASSPATH_INVALID")
        reject_links(path)
        if i == 0:
            require(path.is_dir(), "CLASSPATH_INVALID")
            path /= "GuardianRenderFixture.class"
            reject_links(path)
        else:
            require(path.suffix == ".jar", "CLASSPATH_INVALID")
        require(path.is_file(), "CLASSPATH_INVALID")
        artifacts.append(path)
    memory.admit([3072], memory.memory_status())
    paths = [*artifacts, java, java.parent.parent / "bin/server/jvm.dll",
             java.parent.parent / "lib/modules", classpath_file, Path(__file__),
             Path(memory.__file__), Path(process_guard.__file__), Path(processes.__file__),
             Path(process_observer.__file__), Path(process_resources.__file__),
             Path(desktop_process.__file__), repository / "tests/fixtures/GuardianRenderFixture.java"]
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    plan = {"schema": "strata/PrivateGuardianGraphicsProbe/1", "policy": "held-native-file-resources/6",
            "classification": "synthetic-workload-native-process", "minecraft": False,
            "model_calls": 0, "physical_input": False, "scoring_eligible": False,
            "source_sha256": pins, "profiles": profiles, "resource_observer": resource_observer,
            "hold_seconds": hold_seconds}
    output.mkdir()
    memory.publish(output / "plan.json", plan)
    results = []
    for name, heap, texture, audio, file_mode in profiles:
        result = sample(java, classpath, output / name, name, heap, texture, audio, file_mode,
                        resource_observer=resource_observer, hold_seconds=hold_seconds)
        results.append(result)
        if result["status"] != "measured":
            break
    unchanged = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha for p, sha in pins.items())
    summary = {**plan, "results": results, "sources_unchanged": unchanged,
               "status": "measured" if unchanged and len(results) == len(profiles)
               and all(r["status"] == "measured" for r in results) else "incomplete"}
    memory.publish(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", type=Path, required=True)
    parser.add_argument("--classpath-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profiles", nargs="+", choices=list(PROFILES), required=True)
    parser.add_argument("--resource-observer", action="store_true")
    parser.add_argument("--hold-five-seconds", action="store_true")
    args = parser.parse_args()
    result = run(args.java, args.classpath_file, args.output, args.profiles,
                 resource_observer=args.resource_observer, hold_seconds=5 if args.hold_five_seconds else 0)
    print(json.dumps({"status": result["status"], "scoring_eligible": False,
                     "samples": [{k: r.get(k) for k in ("profile", "status", "stop_result",
                        "cleanup_confirmed", "input_desktop_unchanged", "error_code")}
                                 for r in result["results"]]}))
    return 0 if result["status"] == "measured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
