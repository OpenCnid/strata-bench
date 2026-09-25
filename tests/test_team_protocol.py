"""Campaign-team contract and authority failures, distinct from native conformance."""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from mcbench.communication import Communication
from mcbench.controller import Controller
from mcbench.storage import Fault, Principal, canonical
from mcbench.team_protocol import TeamPolicy, TeamRequest, TeamResponse
from test_storage_controller import setup_campaign, start

POLICY = {
    "schema": "strata/CommunicationPolicy/1",
    "is_example": True,
    "mode": "campaign_roster",
    "max_body_bytes": 4096,
    "sends_per_minute": 10,
    "queue_limit": 100,
    "max_ttl_s": 600,
    "helper_access": False,
}


@pytest.fixture
def team(database, cas, operator, configs):
    now = [1000.0]
    ref = cas.put(operator, "operator", "operator", canonical(POLICY))

    def configured(n, campaign, admission):
        c, agents = configs(n, campaign, admission)
        return c.model_copy(update={"communication_policy": ref}), agents

    controller = Controller(database, simulation=True, clock=lambda: now[0])
    config, epoch = setup_campaign(controller, configured, n=3)
    start(controller, config, epoch)
    service = Communication(database, clock=lambda: now[0])

    def request(agent="a1", operation=None, **extra):
        return {
            "schema": "strata/TeamRequest/1",
            "request_id": "r1",
            "campaign_id": "c1",
            "agent_id": agent,
            "epoch": epoch,
            "deadline_at": datetime.fromtimestamp(now[0] + 2, timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "operation": operation
            or {
                "kind": "send",
                "message_id": "m1",
                "body": "hello",
                "recipients": ["a2"],
                "ttl_s": 600,
            },
            **extra,
        }

    def call(agent="a1", operation=None, **extra):
        return service.request(
            Principal(f"campaign:c1:agent:{agent}", "executor"),
            request(agent, operation, **extra),
            cas,
        )

    return service, request, call, now, controller


def receive(**extra):
    return {"kind": "receive", "after": 0, "limit": 100, "acknowledge": [], **extra}


def test_positive_order_cursor_and_exact_send_dedup(team, database):
    service, request, call, now, _ = team
    first = call()
    assert first["result"] == {
        "kind": "sent",
        "message_id": "m1",
        "sender_seq": 1,
        "expires_unix_ms": 1600000,
    }
    now[0] += 0.1
    assert call() == first  # refreshed transport deadline preserves semantic identity
    call(operation=request()["operation"] | {"message_id": "m2"}, request_id="r2")
    page = call("a2", receive(limit=1), request_id="read1")["result"]
    assert page["next_cursor"] == 1 and page["has_more"]
    page2 = call("a2", receive(after=1, acknowledge=["m1"]), request_id="read2")["result"]
    assert page2["next_cursor"] == 2 and [m["id"] for m in page2["messages"]] == ["m2"]
    assert not page2["has_more"]
    assert database.connection.execute("SELECT count(*) FROM messages").fetchone()[0] == 2
    assert (
        database.connection.execute(
            "SELECT count(*) FROM outbox WHERE kind='team.message'"
        ).fetchone()[0]
        == 2
    )
    assert TeamResponse.model_validate(first).model_dump() == first


def test_recipient_cursors_do_not_reveal_other_delivery_volume(team):
    _, request, call, _, _ = team
    call()
    call(
        operation=request()["operation"] | {"message_id": "m2", "recipients": ["a3"]},
        request_id="r2",
    )
    assert call("a3", receive(), request_id="read")["result"]["messages"][0]["cursor"] == 1
    assert call("a2", receive(), request_id="read")["result"]["messages"][0]["cursor"] == 1


@pytest.mark.parametrize(
    "change",
    [
        {"epoch": 2},
        {"campaign_id": "other"},
        {"agent_id": "a2"},
        {"deadline_at": "1970-01-01T00:16:40Z"},
        {"deadline_at": "1970-01-01T00:16:46Z"},
    ],
)
def test_scope_epoch_deadline_refuse_without_mutation(team, cas, database, change):
    service, request, _, _, _ = team
    before = database.connection.execute("SELECT count(*) FROM outbox").fetchone()[0]
    with pytest.raises(Fault):
        service.request(Principal("campaign:c1:agent:a1", "executor"), request(**change), cas)
    assert database.connection.execute("SELECT count(*) FROM messages").fetchone()[0] == 0
    assert database.connection.execute("SELECT count(*) FROM outbox").fetchone()[0] == before


@pytest.mark.parametrize("role", ["helper", "operator", "evaluator"])
def test_no_nonexecutor_impersonation(team, cas, role):
    service, request, _, _, _ = team
    with pytest.raises(Fault, match="FORBIDDEN"):
        service.request(Principal("campaign:c1:agent:a1", role), request(), cas)


def test_expired_controller_lease_refuses(team):
    _, _, call, now, _ = team
    now[0] += 7
    with pytest.raises(Fault, match="LEASE_EXPIRED"):
        call()


@pytest.mark.parametrize("change", [{"mode": "disabled"}, {"is_example": False}])
def test_declared_disabled_or_wrong_mode_policy_refuses(team, cas, database, operator, change):
    _, _, call, _, _ = team
    ref = cas.put(operator, "operator", "operator", canonical(POLICY | change))
    row = database.connection.execute("SELECT config FROM campaigns").fetchone()
    config = json.loads(row[0])
    config["communication_policy"] = ref
    database.connection.execute("UPDATE campaigns SET config=?", (canonical(config).decode(),))
    with pytest.raises(Fault):
        call()
    assert database.connection.execute("SELECT count(*) FROM messages").fetchone()[0] == 0


def test_agent_visible_policy_is_not_authority(team, cas, database, operator):
    _, _, call, _, _ = team
    ref = cas.put(operator, "operator", "agent", canonical(POLICY | {"mode": "disabled"}))
    config = json.loads(database.connection.execute("SELECT config FROM campaigns").fetchone()[0])
    config["communication_policy"] = ref
    database.connection.execute("UPDATE campaigns SET config=?", (canonical(config).decode(),))
    with pytest.raises(Fault, match="TEAM_POLICY_PRIVATE"):
        call()


@pytest.mark.parametrize(
    "operation", [{"body": "changed"}, {"message_id": "different"}, {"recipients": ["a3"]}]
)
def test_request_key_reuse_conflicts_atomically(team, database, operation):
    _, request, call, _, _ = team
    call()
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        call(operation=request()["operation"] | operation)
    assert database.connection.execute("SELECT count(*) FROM messages").fetchone()[0] == 1


def test_message_id_reuse_with_different_content_also_conflicts(team):
    _, request, call, _, _ = team
    call()
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        call(operation=request()["operation"] | {"body": "other"}, request_id="r2")


def test_cross_roster_send_and_ack_are_atomic(team, database):
    _, request, call, _, _ = team
    call()
    with pytest.raises(Fault, match="FORBIDDEN"):
        call(
            operation=request()["operation"] | {"message_id": "bad", "recipients": ["other-team"]},
            request_id="bad",
        )
    with pytest.raises(Fault, match="FORBIDDEN"):
        call("a2", receive(acknowledge=["m1", "foreign"]), request_id="bad-ack")
    assert database.connection.execute("SELECT acknowledged FROM deliveries").fetchone()[0] == 0


def test_monotonic_deadline_rolls_back_send_even_if_wall_clock_stalls(team, database):
    service, _, call, _, _ = team
    ticks = iter([0, 3])
    service.monotonic = lambda: next(ticks)
    before = database.connection.execute("SELECT count(*) FROM outbox").fetchone()[0]
    with pytest.raises(Fault, match="DEADLINE_EXCEEDED"):
        call()
    for table in ("messages", "deliveries", "team_delivery_cursors", "team_requests"):
        assert database.connection.execute("SELECT count(*) FROM " + table).fetchone()[0] == 0
    assert database.connection.execute("SELECT count(*) FROM outbox").fetchone()[0] == before


def test_cursor_damage_is_refused_not_silently_backfilled(team, database):
    _, _, call, _, _ = team
    call()
    database.connection.execute("DELETE FROM team_delivery_cursors")
    with pytest.raises(Fault, match="TEAM_CURSOR_MISSING"):
        Communication(database)
    assert (
        database.connection.execute("SELECT count(*) FROM team_delivery_cursors").fetchone()[0] == 0
    )


def test_legacy_migration_preserves_message_bytes_and_is_idempotent(team, database):
    _, _, call, _, _ = team
    call()
    before = [tuple(r) for r in database.connection.execute("SELECT * FROM messages")]
    database.connection.execute("DROP TABLE team_cursor_format")
    database.connection.execute("DROP TABLE team_delivery_cursors")
    Communication(database)
    assert [tuple(r) for r in database.connection.execute("SELECT * FROM messages")] == before
    assert (
        database.connection.execute("SELECT cursor FROM team_delivery_cursors").fetchone()[0] == 1
    )
    count = database.connection.execute(
        "SELECT count(*) FROM outbox WHERE kind='team.cursor_migration'"
    ).fetchone()[0]
    Communication(database)
    assert (
        database.connection.execute(
            "SELECT count(*) FROM outbox WHERE kind='team.cursor_migration'"
        ).fetchone()[0]
        == count
    )


@pytest.mark.parametrize(
    "change",
    [
        {"ttl_s": True},
        {"ttl_s": 0},
        {"ttl_s": 601},
        {"ttl_s": 1.5},
        {"recipients": ["a2", "a2"]},
        {"recipients": []},
        {"body": "é" * 2049},
        {"body": "\ud800"},
        {"body": ""},
        {"extra": True},
        {"kind": "unknown"},
    ],
)
def test_send_wire_negatives(team, change):
    _, request, _, _, _ = team
    value = request()
    value["operation"].update(change)
    with pytest.raises(ValidationError):
        TeamRequest.model_validate(value)


@pytest.mark.parametrize(
    "change",
    [
        {"after": True},
        {"after": -1},
        {"limit": 0},
        {"limit": 101},
        {"acknowledge": ["x", "x"]},
        {"acknowledge": ["x"] * 101},
    ],
)
def test_receive_wire_negatives(team, change):
    _, request, _, _, _ = team
    with pytest.raises(ValidationError):
        TeamRequest.model_validate(request(operation=receive(**change)))


@pytest.mark.parametrize(
    "change",
    [
        {"helper_access": 0},
        {"helper_access": True},
        {"max_body_bytes": 4096.0},
        {"sends_per_minute": 11},
        {"mode": "open_web"},
    ],
)
def test_policy_is_exact_and_cannot_silently_expand(change):
    with pytest.raises(ValidationError):
        TeamPolicy.model_validate(POLICY | change)


def advance(now, controller, seconds):
    end = now[0] + seconds
    while now[0] < end:
        now[0] = min(end, now[0] + 5)
        controller.heartbeat("c1", "owner", 1)


def test_expired_message_retry_never_refreshes_delivery_or_charge(team, database):
    _, request, call, now, controller = team
    operation = request()["operation"] | {"ttl_s": 1}
    first = call(operation=operation)
    advance(now, controller, 2)
    assert call(operation=operation, request_id="retry")["result"] == first["result"]
    assert call("a2", receive(), request_id="read")["result"]["messages"] == []
    assert (
        database.connection.execute(
            "SELECT count(*) FROM outbox WHERE kind='team.message'"
        ).fetchone()[0]
        == 1
    )


def test_rate_queue_and_ack_limits_compose_atomically(team, database):
    _, request, call, now, controller = team
    for batch in range(5):
        for sender in ("a1", "a3"):
            for i in range(10):
                message = f"{sender}-{batch * 10 + i}"
                operation = request()["operation"] | {"message_id": message}
                call(sender, operation, request_id=message)
            with pytest.raises(Fault, match="RATE_LIMITED"):
                call(
                    sender,
                    operation | {"message_id": sender + "-excess"},
                    request_id=sender + "-excess",
                )
        advance(now, controller, 61)
    extra = request()["operation"] | {"message_id": "beyond-queue"}
    with pytest.raises(Fault, match="QUEUE_FULL"):
        call(operation=extra, request_id="beyond-queue")
    assert database.connection.execute("SELECT count(*) FROM messages").fetchone()[0] == 100
    call("a2", receive(acknowledge=["a1-0"]), request_id="ack")
    call(operation=extra, request_id="beyond-queue")
    assert (
        call("a2", receive(after=100), request_id="tail")["result"]["messages"][0]["cursor"] == 101
    )


@pytest.mark.parametrize("damage", ["partial", "gap", "event", "orphan", "missing_message"])
def test_migration_damage_refuses_without_repair(team, database, damage):
    _, _, call, _, _ = team
    call()
    if damage == "partial":
        database.connection.execute("DROP TABLE team_cursor_format")
    if damage == "gap":
        database.connection.execute("UPDATE team_delivery_cursors SET cursor=2")
    if damage == "event":
        database.connection.execute(
            "UPDATE outbox SET kind='changed' WHERE kind='team.cursor_migration'"
        )
    if damage == "orphan":
        database.connection.execute("DELETE FROM deliveries")
    if damage == "missing_message":
        database.connection.execute("DELETE FROM messages")
    with pytest.raises(Fault):
        Communication(database)


def test_concurrent_idempotent_sends_commit_one_message_and_cursor(team, database, cas):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from mcbench.storage import CAS, Database

    _, request, _, _, _ = team
    barrier = threading.Barrier(2)

    def worker():
        db = Database(database.path)
        try:
            objects = CAS(db, cas.root)
            service = Communication(db, clock=lambda: 1000.0)
            barrier.wait(timeout=3)
            return service.request(
                Principal("campaign:c1:agent:a1", "executor"), request(), objects
            )
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        results = [f.result() for f in futures]
    assert results[0] == results[1]
    assert database.connection.execute("SELECT count(*) FROM messages").fetchone()[0] == 1
    assert (
        database.connection.execute("SELECT count(*) FROM team_delivery_cursors").fetchone()[0] == 1
    )
