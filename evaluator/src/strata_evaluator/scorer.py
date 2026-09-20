"""Versioned private telemetry predicates, with persisted event/score deduplication.

These development payloads are harness contracts, not an invented Minecraft API.
The actual authenticated read-only server telemetry producer remains a gate.
"""

import json
from typing import Literal

from pydantic import Field

from mcbench.contracts import Id, Name, Positive, Strict, UInt
from mcbench.records import GameEvent
from mcbench.storage import Database, canonical, digest, require

from .scoring_scope import create_tables, record_transaction, register_source, require_source


class CraftEvent(Strict):
    transaction_id: Id
    team_id: Id
    recipe_id: Name
    item_id: Name
    count: Positive
    consumed: dict[Name, Positive]
    source: Literal["craft", "gift", "admin", "quest_reward"]
    expert_mode: bool
    valid_setup: bool


class MachineEvent(Strict):
    transaction_id: Id
    team_id: Id
    machine_id: Id
    recipe_id: Name
    item_id: Name
    interval_start: UInt
    interval_end: UInt
    output_count: UInt
    energy_consumed: UInt
    fluid_consumed: UInt
    source: Literal["machine", "gift", "admin"]
    expert_mode: bool
    valid_setup: bool


class Predicate(Strict):
    predicate_id: Id
    kind: Literal["craft", "machine"]
    team_id: Id
    actors: list[Id]
    recipes: list[Name] = Field(min_length=1)
    item_id: Name
    minimum_output: Positive
    ingredients: dict[Name, Positive]
    sustained_ticks: UInt
    require_energy: bool
    require_fluid: bool
    expert_mode: bool


PAYLOADS = {"strata/CraftEvent/1": ("craft", CraftEvent),
            "strata/MachineEvent/1": ("machine", MachineEvent)}


class Scorer:
    def __init__(self, database: Database):
        self.database = database
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS game_events (boot TEXT, seq INTEGER, digest TEXT, "
                       "body TEXT, PRIMARY KEY(boot,seq))")
            db.execute("CREATE TABLE IF NOT EXISTS predicate_state (instance TEXT, predicate TEXT, "
                       "spec TEXT, body TEXT, PRIMARY KEY(instance,predicate))")
            db.execute("CREATE TABLE IF NOT EXISTS scored_transactions (instance TEXT, predicate TEXT, "
                       "transaction_id TEXT, PRIMARY KEY(instance,predicate,transaction_id))")
            create_tables(db)

    def register_source(self, instance, predicate, source):
        return register_source(self.database, instance, predicate, source)

    def score(self, instance: str, predicate: Predicate, event: GameEvent):
        require(not event.is_example, "EXAMPLE_NOT_EXECUTABLE")
        require(event.payload_schema in PAYLOADS, "SCHEMA_UNSUPPORTED")
        kind, model = PAYLOADS[event.payload_schema]
        require(event.kind == kind, "EVENT_KIND_MISMATCH")
        payload = model.model_validate(event.payload)
        if kind == "machine":
            require(payload.interval_start < payload.interval_end <= event.server_tick,
                    "INVALID_TICK_INTERVAL")
        with self.database.transaction() as db:
            evidence_kind = require_source(db, instance, predicate, event)
            existing = db.execute("SELECT digest FROM game_events WHERE boot=? AND seq=?",
                                  (event.server_boot_id, event.server_event_seq)).fetchone()
            if existing:
                require(existing[0] == digest(event.model_dump()), "IDEMPOTENCY_CONFLICT")
            else:
                db.execute("INSERT INTO game_events VALUES (?,?,?,?)", (event.server_boot_id,
                           event.server_event_seq, digest(event.model_dump()),
                           canonical(event.model_dump()).decode()))
            state_row = db.execute("SELECT * FROM predicate_state WHERE instance=? AND predicate=?",
                                   (instance, predicate.predicate_id)).fetchone()
            state = {"complete": False, "boot": None, "machine": None, "end": None,
                     "ticks": 0, "output": 0, "evidence_kind": evidence_kind,
                     "scoring_authority_qualified": False}
            if state_row:
                require(state_row["spec"] == digest(predicate.model_dump()), "PREDICATE_CHANGED")
                state = json.loads(state_row["body"])
            duplicate = record_transaction(db, instance, predicate, event, payload.transaction_id)
            if state["complete"] or duplicate:
                return state
            valid = (predicate.kind == kind and payload.team_id == predicate.team_id
                     and bool(event.actor_ids) and set(event.actor_ids) <= set(predicate.actors)
                     and payload.recipe_id in predicate.recipes and payload.valid_setup
                     and payload.expert_mode == predicate.expert_mode)
            if kind == "craft":
                valid &= (payload.source == "craft" and payload.item_id == predicate.item_id and
                          all(payload.consumed.get(k, 0) >= v for k, v in predicate.ingredients.items()))
                if valid:
                    state["output"] += payload.count
                    state["complete"] = state["output"] >= predicate.minimum_output
            else:
                valid &= (payload.source == "machine" and payload.item_id == predicate.item_id and
                          (not predicate.require_energy or payload.energy_consumed > 0) and
                          (not predicate.require_fluid or payload.fluid_consumed > 0))
                contiguous = (state["boot"] == event.server_boot_id and
                              state["machine"] == payload.machine_id and
                              state["end"] == payload.interval_start)
                if not valid or not contiguous:
                    state["ticks"], state["output"] = 0, 0
                if valid:
                    state["ticks"] += payload.interval_end - payload.interval_start
                    state["output"] += payload.output_count
                    state["complete"] = (state["ticks"] >= predicate.sustained_ticks and
                                         state["output"] >= predicate.minimum_output)
                state.update(boot=event.server_boot_id, machine=payload.machine_id,
                             end=payload.interval_end)
            db.execute("INSERT OR REPLACE INTO predicate_state VALUES (?,?,?,?)",
                       (instance, predicate.predicate_id, digest(predicate.model_dump()),
                        canonical(state).decode()))
            self.database.event(db, "private.predicate", {"instance": instance,
                                "predicate": predicate.predicate_id, "state": state})
            return state
