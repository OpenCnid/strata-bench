"""Private health negatives plus a real, deliberately stalled Node executor."""

import copy
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from mcbench.worker_health import POLICY, health_required, inspect_worker_health

SCOPE = {"campaign_id": "c1", "agent_id": "a1", "epoch": 1}
START = {"schema": "strata/WorkerHealthStart/1", "policy": POLICY, **SCOPE,
         "pid": 50, "node": "24.19.0", "platform": "win32", "clock": "node-hrtime-ns/process",
         "origin_hrtime_ns": "999999999999999999", "period_ms": 1000, "delay_resolution_ms": 10,
         "interval": "executor-initialization-through-lane-close", "visibility": "evaluator"}
WINDOW = {"schema": "strata/WorkerHealthWindow/1", "policy": POLICY, **SCOPE,
          "seq": 1, "terminal": False, "start_ns": 0, "end_ns": 1_030_000_000,
          "elapsed_ns": 1_030_000_000, "window_ns": 1_030_000_000,
          "cpu_user_us": 150, "cpu_system_us": 20, "rss_bytes": 1000,
          "heap_used_bytes": 500, "heap_total_bytes": 800, "external_bytes": 15, "array_buffers_bytes": 10,
          "delay_samples": 10, "delay_ns": {"min": 10, "p50": 15, "p95": 100, "max": 120, "mean": 19}}


def records():
    return [("worker_health_start", copy.deepcopy(START)), ("worker_health_window", copy.deepcopy(WINDOW)),
            ("worker_health_window", {**copy.deepcopy(WINDOW), "seq": 2, "terminal": True,
                "start_ns": WINDOW["end_ns"], "end_ns": 1_040_000_000, "elapsed_ns": 1_040_000_000,
                "window_ns": 10_000_000, "cpu_user_us": 175, "cpu_system_us": 25,
                "delay_samples": 0, "delay_ns": None})]


def connection(rows):
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE events(cursor INTEGER PRIMARY KEY,kind TEXT,body TEXT)")
    db.executemany("INSERT INTO events(kind,body) VALUES (?,?)", [(k, json.dumps(v)) for k, v in rows])
    return db


def inspect(db, **kwargs):
    return inspect_worker_health(db, **SCOPE, **kwargs)


def test_complete_windows_and_unavailable_legacy_are_distinct():
    with connection(records()) as db:
        report = inspect(db, required=True)
    assert report["cpu_user_us"] == 175  # Cumulative, never sum overlapping counters.
    assert report["elapsed_ns"] == 1_040_000_000
    assert report["period_overruns_ns"] == [30_000_000]
    assert report["delay_samples"] == 10 and report["percentiles_are_not_aggregated"]
    assert report["server_ticks"] is report["avatar_ticks"] is None
    assert not report["capacity_qualified"] and not report["isolation_qualified"]
    with connection([]) as db:
        assert inspect(db) is None
        with pytest.raises(Fault, match="WORKER_HEALTH_REQUIRED"):
            inspect(db, required=True)
    assert health_required([r"C:\runtime\backends\mineflayer\dist\src\worker_health.js"])
    assert not health_required(["backends/mineflayer/dist/src/worker.js"])


@pytest.mark.parametrize("change", [
    lambda r: r.pop(),
    lambda r: r.pop(0),
    lambda r: r.insert(1, copy.deepcopy(r[0])),
    lambda r: r.append(copy.deepcopy(r[-1])),
    lambda r: r[1][1].update(seq=3),
    lambda r: r[1][1].update(start_ns=1),
    lambda r: r[2][1].update(start_ns=0),
    lambda r: r[1][1].update(elapsed_ns=100),
    lambda r: r[1][1].update(window_ns=100),
    lambda r: r[1][1].update(terminal=True),
    lambda r: r[2][1].update(terminal=False),
    lambda r: r[2][1].update(cpu_user_us=149),
    lambda r: r[2][1].update(cpu_system_us=19),
    lambda r: r[1][1].update(cpu_user_us=-1),
    lambda r: r[1][1].update(delay_samples=0),
    lambda r: r[1][1].update(delay_ns=None),
    lambda r: r[1][1]["delay_ns"].update(p95=130),
    lambda r: r[1][1]["delay_ns"].update(mean=float("nan")),
    lambda r: r[1][1].update(heap_used_bytes=801),
    lambda r: r[1][1].update(extra="private injection"),
    lambda r: r[1][1].update(epoch=True),
    lambda r: r[1][1].update(agent_id="sibling"),
    lambda r: r[0][1].update(policy="private-worker-resource-windows/0"),
    lambda r: r[0][1].update(period_ms=100),
    lambda r: r.__setitem__(1, ("worker_health_unknown", r[1][1])),
])
def test_incomplete_conflicting_or_foreign_measurements_reject(change):
    rows = records()
    change(rows)
    with connection(rows) as db, pytest.raises((Fault, ValidationError, ValueError)):
        inspect(db, required=True)


def test_fresh_epoch_uses_its_own_counters_without_refunding_prior_exposure():
    rows = records()
    for kind, body in records():
        rows.append((kind, {**body, "epoch": 2}))
    with connection(rows) as db:
        first = inspect(db, required=True)
        second = inspect_worker_health(db, "c1", "a1", 2, required=True)
    assert first["cpu_user_us"] == second["cpu_user_us"] == 175
    assert first["journal_cursors"] == [1, 3] and second["journal_cursors"] == [4, 6]


def test_real_node_stall_is_read_from_stopped_private_sqlite(tmp_path):
    root = Path(__file__).resolve().parents[1] / "backends/mineflayer/dist/src"
    assert (root / "worker_health.js").is_file(), "Build the worker before this integration test"
    script = tmp_path / "measure.mjs"
    script.write_text(f"""import {{Journal}} from {json.dumps((root / 'journal.js').as_uri())};
import {{WorkerHealth}} from {json.dumps((root / 'worker_health.js').as_uri())};
import {{setTimeout as wait}} from 'node:timers/promises';
const journal = new Journal({json.dumps(str(tmp_path))}, 1);
const health = new WorkerHealth(journal, {json.dumps(SCOPE)}, ()=>{{throw Error('storage');}});
await wait(1100);
const until = performance.now()+150;
while(performance.now()<until) {{}}
await wait(60);
health.close(); journal.close();
""", encoding="utf-8")
    result = subprocess.run([shutil.which("node"), str(script)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    path = tmp_path / "actions.sqlite"
    assert not path.with_name("actions.sqlite-wal").exists()
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        report = inspect(db, required=True)
    assert report["elapsed_ns"] >= 1_250_000_000
    assert report["cpu_user_us"] + report["cpu_system_us"] > 0
    assert report["rss_peak_at_samples_bytes"] > 0
    assert any(w["delay_ns"] and w["delay_ns"]["max"] >= 80_000_000 for w in report["windows"])
    assert report["terminal_window_present"] and not report["capacity_qualified"]


def test_actual_worker_initialization_failure_still_closes_measurement(tmp_path):
    module = Path(__file__).resolve().parents[1] / "backends/mineflayer/dist/src/worker.js"
    config = {**SCOPE, "state_directory": str(tmp_path), "schema": "strata/ForgeDevelopmentWorker/2",
              "connection_file": str(tmp_path / "deliberately-missing-private-connection.json")}
    script = tmp_path / "failed-start.mjs"
    script.write_text(f"""import {{fork}} from 'node:child_process';
const child = fork({json.dumps(str(module))}, [], {{stdio:['ignore','ignore','pipe','ipc'],windowsHide:true}});
child.stderr.resume();
const timeout=setTimeout(()=>{{child.kill();process.exitCode=2;}},10000);
child.on('message',m=>{{if(m.kind==='bootstrap_ready')child.send({{config:{json.dumps(config)},token:'unused'}});}});
child.on('exit',code=>{{clearTimeout(timeout);process.exitCode=code===1?0:3;}});
""", encoding="utf-8")
    result = subprocess.run([shutil.which("node"), str(script)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "executor.lock").exists()
    with sqlite3.connect((tmp_path / "actions.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        report = inspect(db, required=True)
        assert db.execute("SELECT COUNT(*) FROM actions").fetchone()[0] == 0
    assert report["terminal_window_present"] and report["elapsed_ns"] > 0
    # A complete measurement does not turn failed initialization into game success.
    assert report["capacity_qualified"] is False
