import io

import pytest
from pydantic import ValidationError

from mcbench.broker import BrokerGrant, NativeBroker
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
                   {"mcp_servers.unapproved": {}}, {"features.hooks": True}):
        with pytest.raises(Fault, match="BROKER_TOOL_POLICY|BROKER_SERVER_POLICY"):
            validate_broker_settings(config | change)
    config["mcp_servers.strata_broker"]["enabled_tools"].append("admin")
    with pytest.raises(Fault, match="BROKER_SERVER_POLICY"):
        validate_broker_settings(config)
