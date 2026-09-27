# ruff: noqa: F401, F811
"""Signed synthetic server history joined to the real controller/budget stores."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.storage import Fault, canonical
from strata_evaluator.repair_clocks import RepairClockEvidence
from test_clock_barriers import (clock_source, sampled, fields_history, team_history, globals_history,
    clocked, history, native, reference, native_env, repair_env, initial)
from test_craft_reference import ACTOR
from test_telemetry_auth import signed, write

pytestmark = pytest.mark.parametrize("fields_history", [6], indirect=True)


@pytest.fixture
def measured(clock_source, native_env, monkeypatch):
    e, worker, client, target, *_ = native_env
    source = clock_source(campaign="c1", roster={"a1": ACTOR, "a2": "22222222-2222-2222-2222-222222222222"})
    body = hashlib.sha256(("127.0.0.1:25569\n" + ACTOR).encode()).hexdigest()
    original = client.call
    def call(*args, **kwargs):
        result = original(*args, **kwargs)
        if "body_fingerprint" in result:
            result["body_fingerprint"] = body
        return result
    monkeypatch.setattr(client, "call", call)
    monkeypatch.setattr(NativeGameClient, "call", lambda *args, **kwargs: {
        "schema": "strata/NativeGameIdentity/1", "body_fingerprint": body, "connection_generation": 1})
    e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target.model_copy(update={"body_fingerprint": body}))
    service = RepairClockEvidence(e.repairs)
    initial(source)
    service.request_barrier("tx", "opening", "owner", e.epoch, worker, client, source.source)
    service.request_barrier("tx", "closing", "owner", e.epoch, worker, client, source.source)
    first_health = source.events[source.first - 2]
    assert first_health["kind"] == "server_health" and source.first > 3
    first_health["payload"]["durable_event_seq_before_sample"] = 2
    source.events[source.last - 2]["payload"]["durable_event_seq_before_sample"] = source.first
    write(source.path, signed(source.broker.authority, Path(source.broker.authority.key_file).read_bytes(), source.events))
    source.body.update(records=source.first, clock_sample_cursor=source.first)
    source.persist()
    service.capture("tx", "opening", "owner", e.epoch, worker, client, source.source)
    source.body.update(records=source.last, clock_sample_cursor=source.last)
    source.persist()
    service.capture("tx", "closing", "owner", e.epoch, worker, client, source.source)
    def retain(opening="opening", closing="closing"):
        return service.retain_consumption("tx", opening, closing, "owner", e.epoch, worker, client, source.source)
    def reserve(ticks):
        # This changes only the synthetic fixture's pre-existing reservation.
        with e.database.transaction() as db:
            value = json.loads(db.execute("SELECT reserved FROM operations WHERE id='repair-op'").fetchone()[0])
            value["avatar_ticks"] = ticks
            db.execute("UPDATE operations SET reserved=? WHERE id='repair-op'", (canonical(value).decode(),))
    def extend():
        service.request_barrier("tx", "later", "owner", e.epoch, worker, client, source.source)
        # Two authentic-format sample pairs: the first ACK equals the request
        # threshold; the next ACK is newer. All earlier signed bytes are stable.
        for _ in range(2):
            health = copy.deepcopy(source.events[source.last - 2])
            sample = copy.deepcopy(source.events[source.last - 1])
            health["server_tick"] += 1
            health["payload"]["durable_event_seq_before_sample"] = source.last
            sample["server_tick"] += 1
            sample["payload"]["completed_server_ticks"] += 1
            sample["payload"]["elapsed_wall_ns"] += health["payload"]["interval_wall_ns"]
            sample["payload"]["observed_tick_work_ns"] += health["payload"]["observed_tick_work_ns"]
            sample["payload"]["avatar_tick_events"][ACTOR] += 1
            source.events[source.last:source.last] = [health, sample]
            from test_setup_facts import renumber
            renumber(source.events)
            source.last += 2
        write(source.path, signed(source.broker.authority, Path(source.broker.authority.key_file).read_bytes(), source.events))
        source.body.update(records=source.last, clock_sample_cursor=source.last)
        source.persist()
        service.capture("tx", "later", "owner", e.epoch, worker, client, source.source)
    source.extend = extend
    return e, source, service, retain, reserve


def test_owned_tick_delta_retains_hold_deduplicates_and_never_grants_resume(measured):
    e, source, service, retain, reserve = measured
    reserve(10)
    before = e.budgets.status("a1")
    proof = retain()
    assert proof["actor_uuid"] == ACTOR and proof["avatar_ticks"] == 1
    assert proof["server_ticks"] == 1 and proof["elapsed_server_ns"] > 0
    assert not proof["complete_repair_accounting"] and not proof["consumption_settled"]
    assert not proof["campaign_permission_published"]
    assert retain() == proof
    floors = e.database.connection.execute("SELECT * FROM budget_consumption_floors").fetchall()
    assert len(floors) == 1 and floors[0]["dimension"] == "avatar_ticks" and floors[0]["minimum"] == 1
    assert json.loads(floors[0]["body"])["evidence"] == proof
    assert e.budgets.status("a1") == before
    assert e.database.connection.execute("SELECT actual FROM operations WHERE id='repair-op'").fetchone()[0] is None
    assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
    assert e.repairs.status("tx")["phase"] == "RECONFIGURING"
    with pytest.raises(Fault, match="CONFIRMED_CONSUMPTION_REFUND"):
        e.budget("settle", primitive_events=0)  # This fixture's settlement reports zero avatar ticks.
    assert e.database.connection.execute("SELECT actual FROM operations WHERE id='repair-op'").fetchone()[0] is None


def test_tick_overrun_remains_recorded_and_blocks_subsequent_work(measured):
    e, source, service, retain, reserve = measured
    with pytest.raises(Fault, match="REPAIR_BUDGET_EXHAUSTED"):
        retain()
    assert e.budgets.status("a1")["committed_and_reserved"]["avatar_ticks"] == 1
    assert e.database.connection.execute("SELECT count(*) FROM repair_clock_consumption").fetchone()[0] == 1
    with pytest.raises(Fault, match="REPAIR_BUDGET_EXHAUSTED"):
        retain()
    assert e.database.connection.execute("SELECT count(*) FROM budget_consumption_floors").fetchone()[0] == 1


def test_cumulative_extension_does_not_double_charge_or_allow_origin_changes(measured):
    e, source, service, retain, reserve = measured
    reserve(10)
    assert retain()["avatar_ticks"] == 1
    source.extend()
    assert retain(closing="later")["avatar_ticks"] == 3
    assert e.budgets.consumption_floors(e.database.connection)["repair-op"]["avatar_ticks"] == 3
    assert retain(closing="later")["avatar_ticks"] == 3
    assert e.database.connection.execute("SELECT count(*) FROM budget_consumption_floors").fetchone()[0] == 2
    with pytest.raises(Fault, match="REPAIR_CLOCK_ORIGIN_CHANGED"):
        retain("closing", "later")
    with pytest.raises(Fault, match="REPAIR_CLOCK_INTERVAL"):
        retain()


def test_failed_cost_storage_cannot_advance_the_accounting_cursor(measured, monkeypatch):
    e, source, service, retain, reserve = measured
    reserve(10)
    event = e.database.event
    def fail(db, kind, body):
        if kind == "budget.consumption_observed":
            raise OSError("synthetic cost storage failure")
        event(db, kind, body)
    monkeypatch.setattr(e.database, "event", fail)
    with pytest.raises(OSError, match="synthetic cost storage"):
        retain()
    assert e.database.connection.execute("SELECT count(*) FROM repair_clock_consumption").fetchone()[0] == 0
    assert e.database.connection.execute("SELECT count(*) FROM budget_consumption_floors").fetchone()[0] == 0
    monkeypatch.setattr(e.database, "event", event)
    assert retain()["avatar_ticks"] == 1


@pytest.mark.parametrize("change", ["noncausal", "body", "clock", "terminal", "reverse"])
def test_changed_evidence_cannot_charge_another_or_unproven_interval(measured, monkeypatch, change):
    e, source, service, retain, reserve = measured
    reserve(10)
    if change == "terminal":
        source.persist("STOPPED")
    elif change not in {"reverse"}:
        original = e.controller.evidence
        def evidence(ref):
            value = copy.deepcopy(original(ref))
            if value.get("mark") == "opening":
                if change == "noncausal":
                    value["schema"] = "strata/RepairClockWitness/1"
                elif change == "clock":
                    value["controller_clock_id"] = "foreign"
                else:
                    value["source"]["roster"]["a1"] = value["source"]["roster"]["a2"]
            return value
        monkeypatch.setattr(e.controller, "evidence", evidence)
    with pytest.raises(Fault):
        retain("closing", "opening") if change == "reverse" else retain()
    assert e.database.connection.execute("SELECT count(*) FROM budget_consumption_floors").fetchone()[0] == 0
