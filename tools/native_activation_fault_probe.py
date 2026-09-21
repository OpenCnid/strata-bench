"""Owned-process termination at synthetic activation publication boundaries.

No model, game, production store or recovery authority. The diagnostic pauses
the ordinary implementation at named boundaries; the parent kills that exact
process, then observes durable state independently. It never deletes an orphan.
"""

import argparse
import json
import os
from pathlib import Path
import queue
import sqlite3
import subprocess
import sys
import threading
import time

from mcbench.native import NativeExec
from mcbench.native_skill_activation import NativeSkillSets
from mcbench.storage import CAS, Database, extended_path, require

PHASES = ("before_set_commit", "mid_view_copy", "after_view_rename", "before_view_commit")


def _runtime(database, objects):
    with sqlite3.connect(Path(database).absolute().as_uri() + "?mode=ro", uri=True) as read:
        row = read.execute("SELECT simulation FROM native_profile").fetchone()
        require(row is not None and row[0] == 1, "SYNTHETIC_STORE_REQUIRED")
    db = Database(Path(database))
    row = db.connection.execute("SELECT simulation FROM native_profile").fetchone()
    require(row is not None and row[0] == 1, "SYNTHETIC_STORE_REQUIRED")
    return NativeExec(db, CAS(db, Path(objects)), simulation=True)


def child(database, objects, checkpoint, target, phase):
    runtime = _runtime(database, objects)
    service = NativeSkillSets(runtime)
    target = extended_path(Path(target))
    def pause():
        print(json.dumps({"phase": phase, "pid": os.getpid(), "in_transaction": runtime.db.connection.in_transaction}), flush=True)
        # Only the owner may end the pause. EOF is a failure, never continuation.
        sys.stdin.readline()
        raise RuntimeError("FAULT_PROBE_NOT_TERMINATED")
    if phase == "before_set_commit":
        original = runtime.db.event
        def event(db, kind, body):
            result = original(db, kind, body)
            if kind == "native.skills_activated":
                pause()
            return result
        runtime.db.event = event
        service.create(checkpoint)
    else:
        ref = service.create(checkpoint)
        if phase == "mid_view_copy":
            original = runtime.cas.copy_to
            copies = 0
            def copy(*args, **kwargs):
                nonlocal copies
                result = original(*args, **kwargs)
                copies += 1
                if copies == 2:
                    pause()
                return result
            runtime.cas.copy_to = copy
        elif phase == "after_view_rename":
            original = os.rename
            def rename(source, dest):
                result = original(source, dest)
                if Path(dest) == target:
                    pause()
                return result
            os.rename = rename
        elif phase == "before_view_commit":
            connection = runtime.db.connection
            class ObservedConnection:
                def __getattr__(self, name):
                    return getattr(connection, name)

                def execute(self, sql, *args):
                    result = connection.execute(sql, *args)
                    if sql.startswith("INSERT INTO native_skill_views"):
                        pause()
                    return result
            runtime.db.connection = ObservedConnection()
        service.materialize(ref, target)
    raise RuntimeError("FAULT_BOUNDARY_NOT_REACHED")


def run_fault(database, objects, checkpoint, target, phase):
    require(phase in PHASES and not Path(target).exists(), "FAULT_PROBE_SCOPE")
    runtime = _runtime(database, objects)
    service = NativeSkillSets(runtime)
    before = runtime.budgets.status("a1")
    old_sets = runtime.db.connection.execute("SELECT count(*) FROM native_skill_sets").fetchone()[0]
    if phase != "before_set_commit":
        service.create(checkpoint)
        old_sets = runtime.db.connection.execute("SELECT count(*) FROM native_skill_sets").fetchone()[0]
    # Windows venv python.exe is a forwarding launcher. Own the interpreter
    # directly so the observed PID and retained Popen handle identify one process.
    interpreter = sys._base_executable if os.name == "nt" else sys.executable
    argv = [interpreter, str(Path(__file__).resolve()), "--child", "--database", str(database),
            "--objects", str(objects), "--checkpoint", checkpoint, "--target", str(target), "--phase", phase]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(Path(__file__).resolve().parents[1] / "src"),
                                       *(p for p in sys.path if Path(p).name == "site-packages")])
    started = time.monotonic()
    try:
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    except BaseException:
        runtime.db.close()
        raise
    messages = queue.Queue()
    reader = threading.Thread(target=lambda: messages.put(process.stdout.readline()), daemon=True)
    reader.start()
    try:
        raw = messages.get(timeout=20)
        require(raw and process.poll() is None, "FAULT_BOUNDARY_NOT_REACHED")
        signal = json.loads(raw)
        require(signal["phase"] == phase and signal["pid"] == process.pid, "FAULT_PROBE_IDENTITY")
        db = runtime.db.connection
        observed = {"sets": db.execute("SELECT count(*) FROM native_skill_sets").fetchone()[0],
            "view_registered": db.execute("SELECT 1 FROM native_skill_views WHERE path=?",
                (str(extended_path(Path(target))),)).fetchone() is not None,
            "target_exists": Path(target).exists()}
        require(observed["sets"] == old_sets and not observed["view_registered"], "PARTIAL_ACTIVATION_VISIBLE")
        process.kill()
        returncode = process.wait(timeout=5)
        require(returncode != 0 and process.poll() is not None, "FAULT_PROCESS_NOT_TERMINAL")
        after = {"sets": db.execute("SELECT count(*) FROM native_skill_sets").fetchone()[0],
            "view_registered": db.execute("SELECT 1 FROM native_skill_views WHERE path=?",
                (str(extended_path(Path(target))),)).fetchone() is not None,
            "target_exists": Path(target).exists()}
        require(after == observed and runtime.budgets.status("a1") == before, "FAULT_RECOVERY_CHANGED")
        return {"is_example": True, "phase": phase, "pid": process.pid, "returncode": returncode,
            "elapsed_s": time.monotonic() - started, "signal": signal, "observed_before_kill": observed,
            "observed_after_kill": after, "costs_unchanged": True, "native_runtime_qualified": False}
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        reader.join(1)
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
        runtime.db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true", required=True)
    for name in ("database", "objects", "checkpoint", "target"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--phase", choices=PHASES, required=True)
    args = parser.parse_args()
    child(args.database, args.objects, args.checkpoint, args.target, args.phase)
