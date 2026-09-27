"""Fixture protocol/source tests; actual native run is separate private evidence."""

import importlib
import json
from pathlib import Path

import pytest

from mcbench.storage import Database, Fault, canonical


@pytest.fixture
def m(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    return importlib.import_module("native_team_channel_probe")


@pytest.fixture
def store(m, tmp_path, configs):
    config, agents = configs(2, "owned-team")
    return m.TeamChannelStore(tmp_path / "shared", config, agents)


def test_shared_controller_has_real_roster_and_scoped_foreign_canary(m, store):
    with store:
        store.healthy()
        db = Database(store.database)
        try:
            campaigns = [dict(r) for r in db.connection.execute("SELECT * FROM campaigns ORDER BY id")]
            assert {r["state"] for r in campaigns} == {"RUNNING"}
            assert {tuple(json.loads(r["config"])["agent_ids"]) for r in campaigns} == {("a1", "a2")}
            row = db.connection.execute("SELECT * FROM messages").fetchone()
            assert row["campaign"] == m.FOREIGN and row["body"] == m.FOREIGN_MARKER
            sender, receiver = (m.TeamChannelProbe(store, mode) for mode in ("sender", "receiver"))
            assert sender.scope["agent_id"] != receiver.scope["agent_id"]
            assert sender.scope["account"] != receiver.scope["account"]
            assert sender.store.database == receiver.store.database
        finally:
            db.close()
    assert json.loads((store.root / "heartbeat.json").read_bytes())["thread_stopped"] is True


def test_expired_controller_is_not_rearmed(m, store):
    with store:
        db = Database(store.database)
        try:
            db.connection.execute("UPDATE campaigns SET lease_until=0")
            assert store.stop_event.wait(2)
            with pytest.raises(Fault, match="TEAM_FIXTURE_HEARTBEAT"):
                store.healthy()
            assert store.errors and all(r[0] == 1 for r in db.connection.execute("SELECT epoch FROM campaigns"))
        finally:
            db.close()


@pytest.mark.parametrize("mode", ["sender", "receiver"])
def test_script_refreshes_deadline_and_helper_targets_scoped_facade(m, store, mode):
    p = m.TeamChannelProbe(store, mode)
    for actor in m.ACTORS:
        call = p.start(actor, "op-" + actor, "text('positive artifact control');")
        assert 'new Date(Date.now()+3000).toISOString()' in call["input"]
        assert 'await tools[teamTool.name]({request})' in call["input"]
        assert m.FOREIGN_MARKER not in call["input"]
        assert all(r["agent_id"] in {"a1", "a2"} for _, r in p.cases(actor))
    assert dict(p.cases(m.ROOT))["stale_epoch"]["epoch"] == 2
    assert dict(p.cases(m.ROOT))["wrong_campaign"]["campaign_id"] == m.FOREIGN


def complete(m, store, mode):
    p = m.TeamChannelProbe(store, mode)
    for actor in m.ACTORS:
        item = p.start(actor, actor, "text('initial');")
        rows = [{"probe": "team_catalog", "names": ["mcp__strata_broker__" + n for n in
            ("artifact_read", "artifact_write", "artifact_list", "game", "team")]}]
        for name, request in p.cases(actor):
            code = "BROKER_TEAM_FORBIDDEN" if actor == m.CHILD else {
                "wrong_campaign": "BROKER_SCOPE", "wrong_sender": "BROKER_SCOPE", "stale_epoch": "BROKER_SCOPE",
                "foreign_recipient": "FORBIDDEN"}.get(name)
            if code:
                result = {"isError": True, "content": [{"type": "text", "text": code}]}
            else:
                op = request["operation"]
                body = {"kind": "received", "messages": [], "has_more": False, "next_cursor": 0}
                if op["kind"] == "send":
                    body = {"kind": "sent", "message_id": op["message_id"], "sender_seq": 1 if op["message_id"] == "first" else 2,
                            "expires_unix_ms": 123456}
                if name in {"receive_first", "receive_second"}:
                    index = 0 if name == "receive_first" else 1
                    body |= {"messages": [{"id": "first" if index == 0 else "second", "sender": "a1", "sender_seq": index+1,
                        "body": m.PAYLOADS[index], "cursor": index+1, "expires_unix_ms": 123456}],
                             "has_more": index == 0, "next_cursor": index+1}
                result = {"content": [{"type": "text", "text": canonical({"schema": "strata/TeamResponse/1",
                          "request_id": request["request_id"], "result": body}).decode()}]}
            rows.append({"probe": name, "result": result})
        p.outputs[item["call_id"]] = [{"type": "text", "text": '\n'.join(json.dumps(r) for r in rows)}]
    p.finished = set(m.ACTORS)
    return p


@pytest.mark.parametrize("mode", ["sender", "receiver"])
def test_exact_fixture_positive_report(m, store, mode):
    assert all(complete(m, store, mode).report()["checks"].values())


@pytest.mark.parametrize("mutation", ["no-catalog", "extra-catalog", "wrong-error", "duplicate", "missing",
                                      "changed-response", "wrong-scope", "foreign-canary"])
def test_report_rejects_missing_or_changed_actual_controls(m, store, mutation):
    p = complete(m, store, "sender")
    key = next(key for key, value in p.calls.items() if value["actor"] == m.ROOT)
    rows = [json.loads(line) for line in p.outputs[key][0]["text"].splitlines()]
    if mutation == "no-catalog":
        rows.pop(0)
    elif mutation == "extra-catalog":
        rows[0]["names"].append("mcp__strata_broker__admin")
    elif mutation == "wrong-error":
        rows[-1]["result"]["content"][0]["text"] = "other error"
    elif mutation == "duplicate":
        rows.append(rows[-1])
    elif mutation == "missing":
        rows.pop()
    elif mutation in {"changed-response", "wrong-scope"}:
        value = json.loads(rows[2]["result"]["content"][0]["text"])
        if mutation == "wrong-scope":
            value["request_id"] = "other"
        else:
            value["result"]["sender_seq"] = 3
        rows[2]["result"]["content"][0]["text"] = json.dumps(value)
    else:
        p.requests.append({"actor": m.ROOT, "body": {"input": m.FOREIGN_MARKER}})
    p.outputs[key][0]["text"] = '\n'.join(json.dumps(r) for r in rows)
    assert not all(p.report()["checks"].values())


def test_root_waits_for_actual_helper_final_and_is_bounded(m, store):
    p = m.TeamChannelProbe(store, "sender")
    assert p.next(m.ROOT, 1, "spawn")[0]["name"] == "spawn_agent"
    for index in range(4):
        assert p.next(m.ROOT, index+2, "wait-"+str(index))[0]["name"] == "wait_agent"
    with pytest.raises(Fault, match="TEAM_FIXTURE_DELIVERY_BOUND"):
        p.next(m.ROOT, 6, "excess")
    p.messages.add((m.CHILD, m.ROOT, "FINAL_ANSWER", m.DONE))
    assert p.next(m.ROOT, 7, "final")[0]["type"] == "message"
