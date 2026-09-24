"""Verbose native framing is distinct from model tokens and report objects."""
import hashlib
import json
import sqlite3

import pytest
import test_native_oauth as oauth_tests

from mcbench.inference_transport import MAX_RESPONSE_BYTES, NATIVE_RESPONSE_BYTES, ResponsesUsage
from mcbench.native_oauth import SyntheticOAuthTransport
from mcbench.native_retirement import _CompletedResponse
from mcbench.storage import Fault, Principal
from native_oauth_conformance import final_report_journal

admitted, ingress, oauth, provider = (oauth_tests.admitted, oauth_tests.ingress,
                                   oauth_tests.oauth, oauth_tests.provider)


def padded_wire(size):
    terminal = oauth_tests.wire(output=[])
    return b":" + b"p" * (size - len(terminal) - 2) + b"\n" + terminal


def test_native_boundary_and_legacy_default_are_separate():
    wire = padded_wire(NATIVE_RESPONSE_BYTES)
    parser = _CompletedResponse("gpt-5.6-luna", "text/event-stream")
    for start in range(0, len(wire), 65536):
        parser.feed(wire[start:start+65536])
    assert parser.finish()["model_calls"] == 1 and parser.response["output"] == []
    with pytest.raises(Fault, match="RESPONSE_SIZE"):
        parser.feed(b" ")
    with pytest.raises(Fault, match="RESPONSE_SIZE"):
        ResponsesUsage("gpt-5.6-luna", "text/event-stream").feed(wire)
    with pytest.raises(Fault, match="RESPONSE_BOUND"):
        ResponsesUsage("gpt-5.6-luna", "text/event-stream", max_bytes=NATIVE_RESPONSE_BYTES+1)


def test_large_native_wire_reserves_persists_settles_then_delivers(oauth, provider):
    gate, (attempt, reserve, request, _), credential, _, _ = oauth
    wire = padded_wire(MAX_RESPONSE_BYTES * 3)
    endpoint, requests = provider(wire, media="application/octet-stream")
    def delivered(chunk):
        assert chunk == wire and gate.status(reserve.operation_id)["state"] == "SETTLED"
        ref = "cas:sha256:" + hashlib.sha256(wire).hexdigest()
        assert gate.cas.read(Principal("operator", "operator"), "operator", ref) == wire
        row = gate.db.connection.execute("SELECT bytes,state FROM artifact_reservations").fetchone()
        assert tuple(row) == (NATIVE_RESPONSE_BYTES, "CONSUMED")
    result = SyntheticOAuthTransport(gate, credential, endpoint).execute("a1", attempt, reserve, request,
        on_headers=lambda *_: None, on_chunk=delivered)
    assert result["state"] == "SETTLED" and len(requests) == 1


@pytest.mark.parametrize("journal_failure", [False, True])
def test_report_quota_failure_always_closes_database(cas, database, tmp_path, monkeypatch, journal_failure):
    with database.transaction() as db:
        database.event(db, "retained.before_failure", {"value": 1})
    def fail(_):
        raise OSError("synthetic journal disk failure")
    if journal_failure:
        monkeypatch.setattr(database, "export_journal", fail)
    with pytest.raises(OSError if journal_failure else Fault):
        with final_report_journal(database, tmp_path):
            cas.put(Principal("operator", "operator"), "operator", "operator",
                    b"x" * (MAX_RESPONSE_BYTES+1))
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        database.connection.execute("SELECT 1")
    if not journal_failure:
        journal = [json.loads(line) for line in (tmp_path / "journal.jsonl").read_bytes().splitlines()]
        assert journal == [{"cursor": 1, "kind": "retained.before_failure", "body": {"value": 1}}]
