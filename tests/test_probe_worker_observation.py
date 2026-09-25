"""Synthetic journal/worker provenance; actual strict projection and SQLite reader."""

from copy import deepcopy
import math
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault, canonical
from strata_evaluator.probe_worker_observation import verify_initial_worker
from test_probe_saved_bodies import PLAYER, payload, player
from test_worker_identity import values


def observation(example, config):
    value = example("Observation") | {k: config[k] for k in ("campaign_id", "agent_id", "epoch")}
    value["is_example"] = False
    value["state"].update(position={"x": 1.5, "y": 64., "z": -2.}, yaw=math.pi / 2, pitch=0.,
                          inventory=[{"slot": 36, "item_id": "minecraft:stone", "count": 3, "component_summary": {}}])
    return value


def journal(state, config, observed):
    identity = {k: config[k] for k in ("campaign_id", "agent_id", "epoch", "lease_id", "expected_player_uuid")}
    identity.update(schema="strata/WorkerPlayerIdentity/1", policy="authenticated-saved-player-binding/1",
                    authenticated_player_uuid=PLAYER, connected_player_uuid=PLAYER, spawn_seq=1,
                    recorded_at="2026-09-25T00:00:00Z", mono_ms=1.)
    db = sqlite3.connect(Path(state) / "actions.sqlite")
    db.executescript("CREATE TABLE epochs(epoch INTEGER); CREATE TABLE actions(id TEXT); CREATE TABLE counters(name TEXT,value INTEGER); CREATE TABLE events(cursor INTEGER PRIMARY KEY,kind TEXT,body TEXT);")
    db.execute("INSERT INTO epochs VALUES(?)", (config["epoch"],))
    db.execute("INSERT INTO events VALUES(1,'player_identity',?)", (canonical(identity).decode(),))
    db.execute("INSERT INTO events VALUES(2,'observation_delivery',?)", (canonical(observed).decode(),))
    db.commit()
    db.close()


@pytest.fixture
def stopped(example, tmp_path):
    invocation, _ = values(tmp_path)
    state = Path(invocation["state_directory"])
    state.mkdir()
    config = invocation | {"schema": "strata/DevelopmentWorker/2"}
    obs = observation(example, config)
    journal(state, config, obs)
    worker = SimpleNamespace(invocation=invocation, resolved={"worker_configuration": config},
                             receipt=lambda: {"owned_processes": {"preflight": {}, "worker": {}}})
    return worker, obs, payload(player()), state


def test_join_is_private_projection_only_and_reader_closes_handles(stopped):
    worker, obs, raw, state = stopped
    result = verify_initial_worker(worker, obs, raw)
    assert result["own_state_projection_verified"] and not result["live_initial_state_verified"]
    assert not result["native_probe_admission"]
    assert result["identity"]["connected_player_uuid"] == PLAYER
    # All reader handles closed; retained evidence can be renamed by its owner.
    path = state / "actions.sqlite"
    path.rename(state / "retained.sqlite")


@pytest.mark.parametrize("change", ["example", "health", "scope", "active", "window", "uuid", "journal", "order", "duplicate", "action", "primitive", "epoch", "missing_import"])
def test_initial_join_refuses_foreign_or_changed_or_mutated_evidence(stopped, change):
    worker, obs, raw, state = stopped
    obs = deepcopy(obs)
    db = sqlite3.connect(state / "actions.sqlite")
    if change == "example":
        obs["is_example"] = True
    elif change == "health":
        obs["state"]["health"] = 19
    elif change == "scope":
        obs["agent_id"] = "foreign"
    elif change == "active":
        obs["state"]["active_request_id"] = "mutating"
    elif change == "window":
        obs["last_action_seq"] = 1
    elif change == "uuid":
        worker.resolved["worker_configuration"]["expected_player_uuid"] = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    elif change == "journal":
        altered = deepcopy(obs)
        altered["state"]["food"] = 19
        db.execute("UPDATE events SET body=? WHERE cursor=2", (canonical(altered).decode(),))
    elif change == "order":
        db.execute("UPDATE events SET cursor=3 WHERE cursor=1")
    elif change == "duplicate":
        db.execute("INSERT INTO events SELECT 3,kind,body FROM events WHERE cursor=1")
    elif change == "action":
        db.execute("INSERT INTO actions VALUES('forbidden')")
    elif change == "primitive":
        db.execute("INSERT INTO counters VALUES('primitive_events',1)")
    elif change == "epoch":
        db.execute("INSERT INTO epochs VALUES(2)")
    else:
        worker.receipt = lambda: {"owned_processes": {"worker": {}}}
    db.commit()
    db.close()
    with pytest.raises(Fault, match="PROBE_"):
        verify_initial_worker(worker, obs, raw)
