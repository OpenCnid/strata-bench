"""Read private executor metrics from a stopped, caller-verified worker journal.

No gameplay endpoint. Callers own source/DB custody and require the stream for
the new byte-pinned worker. Legacy absence remains unavailable, never zero.
"""

from typing import Annotated, Literal

from pydantic import Field

from .contracts import Id, Positive, Strict, UInt
from .inference_transport import strict_json
from .storage import require

POLICY = "private-worker-resource-windows/1"
SCOPE = ("campaign_id", "agent_id", "epoch")
Number = Annotated[float, Field(ge=0, le=2**53 - 1)]


class HealthScope(Strict):
    policy: Literal["private-worker-resource-windows/1"]
    campaign_id: Id
    agent_id: Id
    epoch: Positive


class HealthStart(HealthScope):
    schema_: Literal["strata/WorkerHealthStart/1"] = Field(alias="schema")
    pid: Positive
    node: Literal["24.19.0"]
    platform: Literal["win32", "linux", "darwin"]
    clock: Literal["node-hrtime-ns/process"]
    origin_hrtime_ns: Annotated[str, Field(pattern=r"^[0-9]{1,24}$")]
    period_ms: Literal[1000]
    delay_resolution_ms: Literal[10]
    interval: Literal["executor-initialization-through-lane-close"]
    visibility: Literal["evaluator"]


class Delay(Strict):
    min: Number
    p50: Number
    p95: Number
    max: Number
    mean: Number


class HealthWindow(HealthScope):
    schema_: Literal["strata/WorkerHealthWindow/1"] = Field(alias="schema")
    seq: Positive
    terminal: bool
    start_ns: UInt
    end_ns: UInt
    elapsed_ns: UInt
    window_ns: UInt
    cpu_user_us: UInt
    cpu_system_us: UInt
    rss_bytes: UInt
    heap_used_bytes: UInt
    heap_total_bytes: UInt
    external_bytes: UInt
    array_buffers_bytes: UInt
    delay_samples: UInt
    delay_ns: Delay | None


def health_required(paths):
    """Inspect held/hashed runtime membership, never a current unpinned checkout."""
    return any(str(path).replace("\\", "/").endswith("/dist/src/worker_health.js") for path in paths)


def inspect_worker_health(db, campaign_id, agent_id, epoch, *, required=False):
    expected = {"campaign_id": campaign_id, "agent_id": agent_id, "epoch": epoch}
    require(db.execute("SELECT COUNT(*) FROM events WHERE kind LIKE 'worker_health%'").fetchone()[0]
            <= 32768, "WORKER_HEALTH_QUOTA")
    rows = db.execute("SELECT cursor,kind,body FROM events WHERE kind LIKE 'worker_health%' ORDER BY cursor")
    selected = []
    for cursor, kind, raw in rows:
        require(kind in {"worker_health_start", "worker_health_window"}, "WORKER_HEALTH_KIND")
        value = (HealthStart if kind == "worker_health_start" else HealthWindow).model_validate(strict_json(raw))
        require((value.campaign_id, value.agent_id) == (campaign_id, agent_id), "WORKER_HEALTH_SCOPE")
        if value.epoch == epoch:
            selected.append((cursor, kind, value))
    require(len(selected) <= 1024, "WORKER_HEALTH_QUOTA")
    if not selected:
        require(not required, "WORKER_HEALTH_REQUIRED")
        return None
    require(len(selected) >= 2 and selected[0][1] == "worker_health_start"
            and all(kind == "worker_health_window" for _, kind, _ in selected[1:]), "WORKER_HEALTH_ORDER")
    start = selected[0][2]
    windows = [item[2] for item in selected[1:]]
    previous, user, system = 0, 0, 0
    for seq, window in enumerate(windows, 1):
        require(window.seq == seq and window.start_ns == previous and window.end_ns >= previous
                and window.window_ns == window.end_ns - previous and window.elapsed_ns == window.end_ns
                and window.terminal == (seq == len(windows))
                and window.cpu_user_us >= user and window.cpu_system_us >= system,
                "WORKER_HEALTH_CONTINUITY")
        require((window.delay_samples == 0) == (window.delay_ns is None), "WORKER_HEALTH_DELAY")
        if window.delay_ns is not None:
            delay = window.delay_ns
            require(delay.min <= delay.p50 <= delay.p95 <= delay.max
                    and delay.min <= delay.mean <= delay.max, "WORKER_HEALTH_DELAY")
        require(window.heap_used_bytes <= window.heap_total_bytes, "WORKER_HEALTH_MEMORY")
        previous, user, system = window.end_ns, window.cpu_user_us, window.cpu_system_us
    last = windows[-1]
    return {"schema": "strata/WorkerHealthReport/1", "policy": POLICY, "visibility": "evaluator", **expected,
        "source": start.model_dump(), "journal_cursors": [selected[0][0], selected[-1][0]],
        "coverage": start.interval, "terminal_window_present": True, "elapsed_ns": last.elapsed_ns,
        "cpu_user_us": user, "cpu_system_us": system,
        "rss_peak_at_samples_bytes": max(w.rss_bytes for w in windows),
        "delay_samples": sum(w.delay_samples for w in windows),
        "delay_basis": "node-monitorEventLoopDelay/resolution10ms; window-local histograms",
        "percentiles_are_not_aggregated": True,
        "period_overruns_ns": [max(0, w.window_ns - 1_000_000_000) for w in windows if not w.terminal],
        "windows": [w.model_dump() for w in windows],
        "server_ticks": None, "avatar_ticks": None, "server_tps": None, "server_mspt": None,
        "isolation_qualified": False, "capacity_qualified": False,
        "gaps": ["executor_pre_import_and_post_close", "parent_and_descendant_resources",
                 "disk_and_network_io", "between_sample_memory_peaks", "histogram_reset_and_journal_overhead",
                 "telemetry_overhead_control", "server_and_avatar_clocks"]}
