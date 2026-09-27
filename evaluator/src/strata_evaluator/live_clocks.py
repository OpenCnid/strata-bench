"""Authenticated clock prefixes while the server runs; never a clean-stop report.

Only evaluator/operator callers may read this stream. An authenticated prefix
does not establish process isolation, roster ownership, freshness at a later
repair boundary, or complete accounting. Those joins remain the controller's job.
"""

import hashlib
from pathlib import Path

from mcbench.records import GameEvent
from mcbench.storage import reject_links, require
from .telemetry import ServerHealth, ServerStartedV20
from .telemetry_auth import MAX_WIRE_RECORD, SpoolVerifier
from .telemetry_clocks import ServerClockSample, advance_clock, reconcile_clock
from mcbench.inference_transport import strict_json


def clock_prefix(path, authority, cursor):
    """Read exactly one bounded, signed prefix ending at a complete clock sample.

    Later appends do not alter the selected receipt. An incomplete requested
    prefix fails; it is not a stopped server or permission to restart one.
    """
    require(type(cursor) is int and 1 <= cursor <= 1_000_000, "CLOCK_PREFIX_CURSOR")
    path = Path(path)
    reject_links(path)
    total, hasher = 0, hashlib.sha256()
    previous, sample = None, None
    ticks, wall, work, health_tick = 0, 0, 0, 0
    with SpoolVerifier(authority) as verifier, path.open("rb") as stream:
        for sequence in range(1, cursor + 1):
            line = stream.readline(MAX_WIRE_RECORD + 1)
            total += len(line)
            require(total <= 256 * 1024**2, "CLOCK_PREFIX_QUOTA")
            event = GameEvent.model_validate(strict_json(verifier.verify(line)))
            require(not event.is_example and event.visibility == "evaluator"
                    and event.campaign_id == verifier.authority.campaign_id
                    and event.epoch == verifier.authority.epoch
                    and event.server_boot_id == verifier.boot
                    and event.seq == event.server_event_seq == sequence
                    and not event.evidence_refs, "CLOCK_PREFIX_SCOPE")
            hasher.update(line)
            if previous is None:
                require(event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/20"
                        and event.server_tick == 0 and not event.actor_ids, "CLOCK_PREFIX_PROFILE")
                ServerStartedV20.model_validate(event.payload)
            else:
                require(event.kind not in {"server_started", "server_clock", "server_stopped"}
                        and event.server_tick >= previous.server_tick, "CLOCK_PREFIX_ORDER")
                if previous.kind == "server_health":
                    require(event.kind == "server_clock_sample", "TELEMETRY_CLOCK_SAMPLE_MISSING")
            if event.kind == "server_health":
                require(event.payload_schema == "strata/ServerHealth/1" and not event.actor_ids,
                        "CLOCK_PREFIX_HEALTH")
                health = ServerHealth.model_validate(event.payload)
                require(health.interval_wall_ns > 0 and health.interval_server_ticks == event.server_tick - health_tick
                        and health.durable_event_seq_before_sample < event.seq, "TELEMETRY_CLOCK_MISMATCH")
                ticks += health.interval_server_ticks
                wall += health.interval_wall_ns
                work += health.observed_tick_work_ns
                health_tick = event.server_tick
            elif event.kind == "server_clock_sample":
                require(previous is not None and previous.kind == "server_health"
                        and event.server_tick == previous.server_tick and not event.actor_ids
                        and event.payload_schema == "strata/ServerClockSample/1", "TELEMETRY_CLOCK_SAMPLE_SCOPE")
                current = ServerClockSample.model_validate(event.payload)
                reconcile_clock(current, final_tick=event.server_tick, sampled_ticks=ticks,
                                sampled_wall_ns=wall, sampled_work_ns=work)
                advance_clock(sample, current)
                sample = current
            previous = event
        require(previous.kind == "server_clock_sample" and sample is not None, "CLOCK_PREFIX_BOUNDARY")
        authentication = verifier.receipt(verifier.boot, cursor)
        return {"schema": "strata/PrivateClockPrefix/1", "campaign_id": verifier.authority.campaign_id,
                "epoch": verifier.authority.epoch, "server_boot_id": verifier.boot,
                "cursor": cursor, "bytes": total, "prefix_sha256": hasher.hexdigest(),
                "authentication": authentication, "clock": sample.model_dump(),
                "clean_stop": False, "active_time_qualified": False,
                "avatar_roster_mapping_qualified": False, "complete_repair_accounting": False}
