import io
import json

import pytest
from pydantic import ValidationError

from mcbench.broker import BrokerGrant, NativeBroker, inspect_game_requests
from mcbench.contracts import RpcRequest
from mcbench.broker_stdio import WorkerTransport, respond, serve
from mcbench.storage import CAS, Database, Fault, canonical


@pytest.fixture
def broker(database, cas, operator):
    from mcbench.native import NativeExec
    NativeExec(database, cas, simulation=True)
    b = NativeBroker(database, cas, "runtime", "a" * 64, clock=lambda: 100)
    evidence = cas.put(operator, "operator", "operator", canonical({"is_example": True}))
    root = BrokerGrant.model_validate({"schema": "strata/NativeBrokerGrant/1",
        "runtime_id": "runtime", "session_id": "root", "thread_id": "root",
        "parent_thread_id": None, "profile_digest": "a" * 64, "model": "gpt-5.6-luna",
        "role": "executor", "namespace": "root-artifacts", "campaign_id": "c1",
        "agent_id": "a1", "epoch": 1, "depth": 0, "expires_unix_ms": 200000,
        "tool_calls": 100, "admission_ref": evidence})
    b.admit(root)
    child = root.model_copy(update={"thread_id": "child", "parent_thread_id": "root",
        "role": "helper", "namespace": "child-results", "depth": 1})
    b.admit(child)
    b.project("root", "initial/skill.md", "Initial immutable skill.")
    b.project("root", "docs/allowed.md", "Allowed corpus.")
    b.project("child", "supplied/plan.md", "Only the explicit helper plan.")
    return b, root, child


def meta(thread="root", **overrides):
    native = {"thread_id": thread, "session_id": "root", "codex_version": "0.154.0-alpha.6.2",
        "model": "gpt-5.6-luna", "thread_source": "user" if thread == "root" else "subagent"}
    if thread != "root":
        native.update(parent_thread_id="root", subagent_kind="thread_spawn")
    native.update(overrides)
    return {"callId": "call-one", "threadId": thread, "x-codex-turn-metadata": native}


def request():
    return {"schema": "strata/GameRequest/1", "request_id": "game-one", "campaign_id": "c1",
        "agent_id": "a1", "epoch": 1, "deadline_at": "1970-01-01T00:01:44Z",
        "method": "observe", "action": None, "target_request_id": None, "after": None}


def test_public_pilot_pagination_reaches_worker_once_and_cannot_expand_methods(broker):
    from mcbench.native_piloting import game_contract, PURPOSE
    b, _, _ = broker
    b.db.connection.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
        ("runtime", "c1", "a1", 1, "executor", None, "a"*64, json.dumps({"purpose": PURPOSE}), "RUNNING"))
    doc = json.loads(game_contract())
    page = request() | {"method": doc["pagination"]["method"], "cursor": "delivered-page"}
    forwarded = []
    def transport(r):
        forwarded.append(r.model_dump())
        return {"status": "ok", "request_id": r.request_id, "result": {"is_example": True}}
    first = b.call("game", {"request": page}, meta(), game_transport=transport)
    assert b.call("game", {"request": page}, meta(), game_transport=transport) == first
    assert len(forwarded) == 1 and forwarded[0]["method"] == "observe.page"
    assert inspect_game_requests(b.db.connection, "runtime")[("root", "game-one")]["cursor"] == "delivered-page"
    with pytest.raises(ValidationError, match="spatial cursor"):
        b.call("game", {"request": page | {"method": "observe"}}, meta(), game_transport=transport)
    with pytest.raises(Fault, match="PILOT_GAME_METHOD"):
        b.call("game", {"request": request() | {"request_id": "not-allowed", "method": "wait_events", "after": 0}},
               meta(), game_transport=transport)
    assert len(forwarded) == 1


def test_scoped_projection_and_drafts_survive_restart(broker):
    b, _, _ = broker
    assert b.call("artifact_read", {"path": "docs/allowed.md"}, meta())["text"] == "Allowed corpus."
    written = b.call("artifact_write", {"path": "notes/one.md", "text": "Own note.",
        "expected_ref": None}, meta())
    db = Database(b.db.path)
    try:
        restored = NativeBroker(db, CAS(db, b.cas.root), "runtime", "a" * 64, clock=lambda: 100)
        assert restored.call("artifact_read", {"path": "notes/one.md"}, meta())["ref"] == written["ref"]
        paths = [f["path"] for f in restored.call("artifact_list", {}, meta("child"))["files"]]
        assert paths == ["supplied/plan.md"]
        with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
            restored.call("artifact_read", {"path": "notes/one.md"}, meta("child"))
    finally:
        db.close()


@pytest.mark.parametrize("path", ["../operator/secret", "C:/Users/account", "//server/share",
    "docs/../../holdout", "docs/x:secret", "docs\\allowed.md", "docs/CON", "docs/link/secret"])
def test_forbidden_paths_have_no_filesystem_resolution(broker, path):
    b, _, _ = broker
    with pytest.raises(Fault, match="UNSAFE_PATH|BROKER_FORBIDDEN"):
        b.call("artifact_read", {"path": path}, meta())


def test_helper_only_writes_own_results_and_cannot_override_identity(broker):
    b, _, _ = broker
    result = b.call("artifact_write", {"path": "results/advice.md", "text": "Advice.",
        "expected_ref": None}, meta("child"))
    assert result["ref"].startswith("cas:sha256:")
    for path in ("notes/parent.md", "initial/skill.md", "docs/new.md"):
        with pytest.raises(Fault, match="BROKER_WRITE_FORBIDDEN"):
            b.call("artifact_write", {"path": path, "text": "spoof", "expected_ref": None}, meta("child"))
    with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
        b.call("artifact_read", {"path": "results/advice.md"}, meta())
    for spoof in ({"threadId": "root"}, {"_meta": meta()}, {"namespace": "root-artifacts"}):
        with pytest.raises(ValidationError):
            b.call("artifact_read", {"path": "docs/allowed.md", **spoof}, meta("child"))


@pytest.mark.parametrize("overrides", [
    {"session_id": "sibling"}, {"thread_id": "root"}, {"parent_thread_id": "sibling"},
    {"model": "different-model"}, {"codex_version": "unpinned"}, {"thread_source": "user"},
    {"subagent_kind": "unknown"}])
def test_metadata_mismatch_never_receives_projection(broker, overrides):
    b, _, _ = broker
    with pytest.raises(Fault, match="BROKER_IDENTITY_MISMATCH"):
        b.call("artifact_read", {"path": "supplied/plan.md"}, meta("child", **overrides))


def test_no_missing_metadata_or_automatic_helper_enrollment(broker):
    b, _, _ = broker
    for m in (None, {}, {"threadId": "root"}, meta("unregistered")):
        with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
            b.call("artifact_list", {}, m)


def test_revocation_expiry_and_grant_replay_do_not_reset_permissions(broker):
    b, root, _ = broker
    b.revoke("root")
    b.admit(root)
    for thread in ("root", "child"):
        with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
            b.call("artifact_list", {}, meta(thread))
    with b.db.transaction() as db:
        db.execute("UPDATE broker_grants SET revoked=0,remaining=0")
    b.admit(root)
    with pytest.raises(Fault, match="BROKER_QUOTA"):
        b.call("artifact_list", {}, meta())
    b.clock = lambda: 201
    with pytest.raises(Fault, match="BROKER_EXPIRED"):
        b.call("artifact_list", {}, meta("child"))


def test_projection_immutable_and_compare_write_quota(broker):
    b, _, _ = broker
    with pytest.raises(Fault, match="INITIAL_IMMUTABLE"):
        b.project("root", "initial/skill.md", "Changed")
    with pytest.raises(Fault, match="BROKER_WRITE_FORBIDDEN"):
        b.call("artifact_write", {"path": "initial/skill.md", "text": "Changed",
            "expected_ref": None}, meta())
    first = b.call("artifact_write", {"path": "notes/x", "text": "first", "expected_ref": None}, meta())
    with pytest.raises(Fault, match="REVISION_CONFLICT"):
        b.call("artifact_write", {"path": "notes/x", "text": "lost update", "expected_ref": None}, meta())
    assert b.call("artifact_write", {"path": "notes/x", "text": "second",
        "expected_ref": first["ref"]}, meta())["ref"] != first["ref"]
    with pytest.raises(Fault, match="ARTIFACT_QUOTA"):
        b.call("artifact_write", {"path": "handoff/x", "text": "é" * 4001, "expected_ref": None}, meta())


def test_game_helper_scope_and_unknown_receipt_no_replay(broker):
    b, _, _ = broker
    calls = []
    def lost(r):
        calls.append(r.request_id)
        raise OSError("private transport detail must not be echoed")
    with pytest.raises(Fault, match="BROKER_GAME_FORBIDDEN"):
        b.call("game", {"request": request()}, meta("child"), game_transport=lost)
    with pytest.raises(Fault, match="BROKER_SCOPE"):
        b.call("game", {"request": request() | {"agent_id": "a2"}}, meta(), game_transport=lost)
    with pytest.raises(Fault, match="BROKER_GAME_OUTCOME_UNKNOWN"):
        b.call("game", {"request": request()}, meta(), game_transport=lost)
    assert calls == ["game-one"]
    restored = NativeBroker(b.db, b.cas, "runtime", "a" * 64, clock=lambda: 100)
    assert restored.call("game", {"request": request()}, meta(), game_transport=lost) == {
        "status": "unknown", "request_id": "game-one", "replayed": False}
    assert calls == ["game-one"]
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        restored.call("game", {"request": request() | {"method": "capabilities"}}, meta(), game_transport=lost)


def test_successful_game_receipt_deduplicates_and_never_exposes_admin(broker):
    b, _, _ = broker
    calls = []
    def forward(r):
        calls.append(r)
        return {"schema": "strata/GameResponse/1", "status": "ok", "result": {"fixture": True}}
    for _ in range(2):
        assert b.call("game", {"request": request()}, meta(), game_transport=forward)["status"] == "ok"
    assert len(calls) == 1
    with pytest.raises(ValidationError):
        b.call("game", {"request": request() | {"method": "admin.eval"}}, meta(), game_transport=forward)


def test_exact_request_is_committed_before_forward_and_survives_lost_reply(broker):
    b, _, _ = broker
    expected = RpcRequest.model_validate(request()).model_dump()
    def forward(_):
        # Independent connection proves the intent transaction has committed.
        other = Database(b.db.path)
        try:
            assert inspect_game_requests(other.connection, "runtime") == {("root", "game-one"): expected}
        finally:
            other.close()
        raise OSError("lost reply")
    with pytest.raises(Fault, match="BROKER_GAME_OUTCOME_UNKNOWN"):
        b.call("game", {"request": request()}, meta(), game_transport=forward)
    restored = NativeBroker(b.db, b.cas, "runtime", "a" * 64, clock=lambda: 100)
    assert restored.call("game", {"request": request()}, meta(), game_transport=lambda _: pytest.fail("replay"))["status"] == "unknown"
    assert inspect_game_requests(b.db.connection, "runtime") == {("root", "game-one"): expected}


@pytest.mark.parametrize("case", ["missing", "changed", "arguments"])
def test_missing_or_conflicting_request_blocks_cached_reply_without_forward(broker, case):
    b, _, _ = broker
    b.call("game", {"request": request()}, meta(), game_transport=lambda _: {"status": "ok"})
    if case == "missing":
        b.db.connection.execute("DELETE FROM broker_game_requests")
    elif case == "arguments":
        row = b.db.connection.execute("SELECT cursor,body FROM outbox WHERE kind='broker.call'").fetchone()
        event = json.loads(row["body"])
        event["game_arguments"]["request"]["method"] = "capabilities"
        b.db.connection.execute("UPDATE outbox SET body=? WHERE cursor=?", (canonical(event).decode(), row["cursor"]))
    else:
        body = RpcRequest.model_validate(request() | {"method": "capabilities"}).model_dump()
        b.db.connection.execute("UPDATE broker_game_requests SET body=?", (canonical(body).decode(),))
    with pytest.raises(Fault, match="BROKER_GAME_REQUEST_MISSING|BROKER_GAME_REQUEST_CONFLICT|BROKER_GAME_REQUEST_EVENT"):
        b.call("game", {"request": request()}, meta(), game_transport=lambda _: pytest.fail("replay"))


def test_legacy_migration_keeps_old_bytes_and_unknown_preimages(broker):
    b, _, _ = broker
    b.call("game", {"request": request()}, meta(), game_transport=lambda _: {"status": "ok"})
    db = b.db.connection
    old = [tuple(r) for r in db.execute("SELECT * FROM broker_game_calls")]
    db.execute("DROP TABLE broker_game_requests")
    db.execute("DROP TABLE broker_game_request_format")
    for row in db.execute("SELECT cursor,body FROM outbox WHERE kind='broker.call'").fetchall():
        event = json.loads(row["body"])
        event.pop("game_arguments", None)  # Reproduce the historical format exactly.
        db.execute("UPDATE outbox SET body=? WHERE cursor=?", (canonical(event).decode(), row["cursor"]))
    restored = NativeBroker(b.db, b.cas, "runtime", "a" * 64, clock=lambda: 100)
    assert [tuple(r) for r in db.execute("SELECT * FROM broker_game_calls")] == old
    assert inspect_game_requests(db, "runtime") == {}
    assert restored.call("game", {"request": request()}, meta(), game_transport=lambda _: pytest.fail("replay")) == {"status": "ok"}
    later = request() | {"request_id": "game-two"}
    restored.call("game", {"request": later}, meta(), game_transport=lambda _: {"status": "ok"})
    evidence = inspect_game_requests(db, "runtime")
    assert set(evidence) == {("root", "game-two")}
    assert evidence[("root", "game-two")] == json.loads(db.execute("SELECT body FROM broker_game_requests").fetchone()[0])
    assert tuple(db.execute("SELECT * FROM broker_game_calls WHERE request='game-one'").fetchone()) == old[0]


def test_request_journal_failure_rolls_back_intent_before_any_forward(broker):
    b, _, _ = broker
    b.db.connection.execute("CREATE TRIGGER synthetic_failure BEFORE INSERT ON broker_game_requests "
                            "BEGIN SELECT RAISE(ABORT, 'synthetic storage failure'); END")
    with pytest.raises(Exception, match="synthetic storage failure"):
        b.call("game", {"request": request()}, meta(), game_transport=lambda _: pytest.fail("unrecorded forward"))
    assert b.db.connection.execute("SELECT count(*) FROM broker_game_calls").fetchone()[0] == 0


def test_stdio_bounded_catalog_metadata_and_redacted_errors(broker):
    b, _, _ = broker
    catalog = respond(b, {"jsonrpc": "2.0", "method": "tools/list"})
    assert {t["name"] for t in catalog["tools"]} == {"artifact_read", "artifact_write", "artifact_list", "game"}
    raw = canonical({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
        "name": "artifact_read", "_meta": meta("child"), "arguments": {
            "path": "docs/allowed.md", "secret": "DO_NOT_ECHO"}}}) + b"\n"
    output = io.BytesIO()
    serve(b, io.BytesIO(raw), output)
    assert b"BROKER_ARGUMENTS_INVALID" in output.getvalue() and b"DO_NOT_ECHO" not in output.getvalue()
    output = io.BytesIO()
    serve(b, io.BytesIO(b"x" * (384 * 1024 + 2)), output)
    assert not output.getvalue()


def test_bad_game_arguments_return_public_schema_without_rejected_input(broker):
    from mcbench.broker import GameCall
    b, _, _ = broker
    result = respond(b, {"jsonrpc": "2.0", "method": "tools/call", "params": {
        "name": "game", "_meta": meta(), "arguments": {"request": {"DO_NOT_ECHO": "secret"}}}})
    raw = result["content"][0]["text"]
    assert result["isError"] and "DO_NOT_ECHO" not in raw and '"secret"' not in raw
    value = json.loads(raw)
    assert value["code"] == "BROKER_ARGUMENTS_INVALID"
    assert value["expected_arguments_schema"] == GameCall.model_json_schema()
    assert b.db.connection.execute("SELECT count(*) FROM broker_game_calls").fetchone()[0] == 0


@pytest.mark.parametrize("offset,accepted", [(-1, False), (0, False), (2, True), (5.25, True), (5.251, False), (60, False)])
def test_game_deadline_window_feedback_and_no_forward_on_rejection(broker, offset, accepted):
    from datetime import datetime, timezone
    b, _, _ = broker
    calls = []
    body = request() | {"deadline_at": datetime.fromtimestamp(100 + offset, timezone.utc).isoformat().replace("+00:00", "Z")}
    result = respond(b, {"jsonrpc": "2.0", "method": "tools/call", "params": {
        "name": "game", "_meta": meta(), "arguments": {"request": body}}},
        game_transport=lambda r: calls.append(r) or {"status": "ok"})
    assert len(calls) == int(accepted)
    if not accepted:
        value = json.loads(result["content"][0]["text"])
        assert result["isError"] and value["code"] == "DEADLINE_EXCEEDED"
        assert value["maximum_future_ms"] == 5250
        assert "Date.now()+2000" in value["guidance"]
        assert body["deadline_at"] not in result["content"][0]["text"]
        assert not inspect_game_requests(b.db.connection, "runtime")


@pytest.mark.parametrize("url", ["http://localhost:123/v1/game", "http://127.0.0.1:123/admin",
    "https://127.0.0.1:123/v1/game", "http://127.0.0.1:123/v1/game?url=elsewhere",
    "http://user:pass@127.0.0.1:123/v1/game"])
def test_worker_endpoint_is_operator_pinned_loopback_only(url):
    with pytest.raises(Fault, match="BROKER_WORKER_DESCRIPTOR"):
        WorkerTransport({"url": url, "token": "x" * 32, "campaign_id": "c1", "agent_id": "a1", "epoch": 1})


def test_native_broker_policy_rejects_tool_and_ancestor_instruction_expansion():
    from mcbench.native_broker_policy import BROKER_TOOLS, restricted_settings, validate_broker_settings
    config = restricted_settings() | {"mcp_servers.strata_broker": {
        "enabled_tools": list(BROKER_TOOLS), "required": True,
        "tools": {"artifact_write": {"approval_mode": "approve"}, "game": {"approval_mode": "approve"}}}}
    validate_broker_settings(config)
    for change in ({"features.shell_tool": True}, {"project_doc_max_bytes": 32768},
                   {"mcp_servers.unapproved": {}}, {"features.hooks": True},
                   {"features.unified_exec": True}, {"features.unreviewed": False},
                   {"features": {"shell_tool": True}}, {"features.multi_agent": True},
                   {"features.plugins": False}, {"features.remote_models": True}):
        with pytest.raises(Fault, match="BROKER_TOOL_POLICY|BROKER_SERVER_POLICY"):
            validate_broker_settings(config | change)
    config["mcp_servers.strata_broker"]["enabled_tools"].append("admin")
    with pytest.raises(Fault, match="BROKER_SERVER_POLICY"):
        validate_broker_settings(config)


@pytest.mark.parametrize("extra", ["url", "env_vars", "bearer_token_env_var", "http_headers",
                                  "enabled", "oauth", "default_tools_approval_mode"])
def test_stdio_policy_rejects_unreviewed_transport_and_auth_fields(extra):
    from mcbench.native_broker_policy import BROKER_TOOLS, restricted_settings, validate_broker_settings
    server = {"enabled_tools": list(BROKER_TOOLS), "required": True,
              "tools": {"artifact_write": {"approval_mode": "approve"},
                        "game": {"approval_mode": "approve"}}}
    with pytest.raises(Fault, match="BROKER_SERVER_POLICY"):
        validate_broker_settings(restricted_settings() | {"mcp_servers.strata_broker": server | {extra: "fixture"}})
