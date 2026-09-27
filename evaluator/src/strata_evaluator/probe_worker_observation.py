"""Private stopped-worker join of an initial observation to registered saved state.

This proves the observable projection only. Item tags, selected slot, abilities,
effects and other unprojected live state require a separate qualified witness.
"""

from contextlib import closing
from pathlib import Path
import sqlite3

from mcbench.contracts import Observation
from mcbench.inference_transport import strict_json
from mcbench.pack_worker import WorkerPlayerIdentity
from mcbench.storage import canonical, digest, reject_links, require

from .native_game_continuation import player_matches
from .saved_blocks import NbtReader, unpack_chunk
from .probe_saved_bodies import saved_body

POLICY = "registered-worker-initial-own-projection/1"


def verify_initial_worker(worker, observation, saved_player):
    """Use a normally stopped owned worker, not a caller-selected journal path."""
    custody = worker.receipt()
    require(set(custody["owned_processes"]) == {"preflight", "worker"}, "PROBE_WORKER_STOP_UNPROVEN")
    config = worker.resolved["worker_configuration"]
    require(config["schema"] == "strata/DevelopmentWorker/2", "PROBE_BODY_POLICY_REQUIRED")
    require(saved_body(saved_player)["player_uuid"] == config["expected_player_uuid"], "PROBE_INITIAL_IDENTITY")
    observed = Observation.model_validate(observation)
    window = observed.state.window if observed.state is not None else None
    ordinary_inventory = window is None or (
        window.id == 0 and window.type == "minecraft:inventory"
        and window.cursor_item is None and window.machine is None
        and window.slots == observed.state.inventory
    )
    require(not observed.is_example and observed.mode == "structured" and observed.state is not None
            and observed.state.connected
            and all(getattr(observed, k) == config[k] for k in ("campaign_id", "agent_id", "epoch"))
            and observed.last_action_seq is None and observed.state.active_request_id is None
            and not observed.event_gap and not observed.held_keys and ordinary_inventory,
            "PROBE_INITIAL_OBSERVATION")
    player = NbtReader(unpack_chunk(saved_player, 1)).root()
    require(player_matches(player, observed.state.model_dump()), "PROBE_INITIAL_PLAYER_CHANGED")
    path = Path(config["state_directory"]) / "actions.sqlite"
    reject_links(path)
    require(path.is_file() and path.stat().st_nlink == 1 and path.stat().st_size <= 64 * 1024**2,
            "PROBE_WORKER_JOURNAL")
    # WAL-aware read-only access. Do not delete or ignore retained sidecars.
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        require(db.execute("SELECT epoch FROM epochs").fetchall() == [(config["epoch"],)]
                and db.execute("SELECT COUNT(*) FROM actions").fetchone()[0] == 0
                and db.execute("SELECT COALESCE(SUM(value),0) FROM counters WHERE name='primitive_events'").fetchone()[0] == 0,
                "PROBE_INITIAL_ACTIONS")
        rows = db.execute("SELECT cursor,kind,body FROM events WHERE kind IN ('player_identity','observation_delivery') ORDER BY cursor LIMIT 258").fetchall()
        require(len(rows) <= 257 and all(len(r[2]) <= 131072 for r in rows), "PROBE_WORKER_JOURNAL_QUOTA")
    identities = [(cursor, WorkerPlayerIdentity.for_invocation(strict_json(raw), worker.invocation))
                  for cursor, kind, raw in rows if kind == "player_identity"]
    require(len(identities) == 1 and identities[0][1].spawn_seq == 1, "PROBE_INITIAL_IDENTITY")
    matches = [(cursor, strict_json(raw)) for cursor, kind, raw in rows
               if kind == "observation_delivery" and strict_json(raw).get("observation_id") == observed.observation_id]
    # Keep exact delivered JSON; model_dump can add omitted optional defaults.
    require(len(matches) == 1 and canonical(matches[0][1]) == canonical(observation)
            and identities[0][0] < matches[0][0]
            and identities[0][1].mono_ms <= observed.captured_mono_ms,
            "PROBE_INITIAL_JOURNAL_JOIN")
    return {"policy": POLICY, "identity": identities[0][1].model_dump(),
            "observation_digest": digest(observation), "own_state_projection_verified": True,
            "live_initial_state_verified": False, "native_probe_admission": False,
            "worker_custody": custody}
