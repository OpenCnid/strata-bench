"""Synthetic observed-shape receipts and local HTTP; no OAuth or inference."""

import copy
import json
import time

import pytest
import test_inference_transport
import test_native_gateway

from mcbench.inference_transport import ResponsesUsage
from mcbench.receipt_recovery import reconcile_captured_sse
from mcbench.storage import Fault

gateway = test_native_gateway.gateway
provider = test_native_gateway.provider


@pytest.fixture(autouse=True)
def legacy_rejected_media_profile(monkeypatch):
    # Reproduce captures retained by the prior /1 transport, before /2 can
    # normalize a complete validated SSE body. No receipt/state rows are forged.
    from mcbench.native_oauth import SyntheticOAuthTransport
    monkeypatch.setattr(SyntheticOAuthTransport, "buffered_sse_policy", None)


def attributed():
    value = test_inference_transport.response(model="gpt-5.6-luna", tool_usage={})
    usage = value["usage"]
    usage["input_tokens_details"]["cache_write_tokens"] = 3
    counters = {"input_tokens": 10, "output_tokens": 4, "cached_tokens": 2, "cache_write_tokens": 3}
    usage["attribution"] = {"items": {"synthetic-message": counters | {"content": [counters.copy()]}}}
    return value


def test_native_attribution_is_validated_not_double_counted():
    parser = ResponsesUsage("gpt-5.6-luna", "text/event-stream")
    raw = test_inference_transport.stream(attributed()) * 2
    for start in range(0, len(raw), 7):
        parser.feed(raw[start:start+7])
    result = parser.finish()
    assert result["input_tokens"] == 10 and result["output_tokens"] == 4
    assert result["cache_write_tokens"] == 3 and result["model_calls"] == 1


def test_only_exact_zero_hosted_usage_shape_is_supported():
    from mcbench.native_usage import validate_no_hosted_usage
    zero = {"image_gen": {"input_tokens": 0, "input_tokens_details": {"image_tokens": 0, "text_tokens": 0},
        "output_tokens": 0, "output_tokens_details": {"image_tokens": 0, "text_tokens": 0}, "total_tokens": 0},
        "web_search": {"num_requests": 0}}
    validate_no_hosted_usage(zero)
    for value in (1, False, None, 0.0):
        changed = copy.deepcopy(zero)
        changed["web_search"]["num_requests"] = value
        with pytest.raises(Fault, match="HOSTED_TOOL_USAGE_UNSUPPORTED"):
            validate_no_hosted_usage(changed)


@pytest.mark.parametrize("case", ["new_category", "missing_write", "item_total", "content_total", "write_overlap", "hosted_tool"])
def test_changed_or_ambiguous_native_usage_is_rejected(case):
    value = attributed()
    usage = value["usage"]
    if case == "new_category":
        usage["attribution"]["items"]["synthetic-message"]["audio_tokens"] = 1
    elif case == "missing_write":
        del usage["input_tokens_details"]["cache_write_tokens"]
    elif case == "item_total":
        usage["attribution"]["items"]["duplicate"] = copy.deepcopy(usage["attribution"]["items"]["synthetic-message"])
    elif case == "content_total":
        usage["attribution"]["items"]["synthetic-message"]["content"][0]["output_tokens"] += 1
    elif case == "write_overlap":
        usage["input_tokens_details"]["cache_write_tokens"] = 9
    else:
        value["tool_usage"] = {"web_search": 1}
    parser = ResponsesUsage("gpt-5.6-luna", "text/event-stream")
    with pytest.raises(Fault):
        parser.feed(test_inference_transport.stream(value))
        parser.finish()


def captured(g, provider, *, truncated=False):
    wire = test_inference_transport.stream(attributed())
    if truncated:
        wire = wire[:-1]
    endpoint, requests = provider(wire, media="application/octet-stream")
    g.service.fixture_upstream = endpoint.removesuffix("/v1/responses")
    assert g.post()[0] == 403
    assert len(requests) == 1
    db = g.gate.db.connection
    db.execute("UPDATE native_jobs SET state='UNSETTLED',ended=?", (time.time(),))
    seal = g.service.close(g.runtime)
    operation = db.execute("SELECT operation FROM inference_attempts").fetchone()[0]
    return operation, seal, requests


def test_capture_recovery_settles_once_and_closes_only_fenced_envelope(gateway, provider):
    g = gateway
    operation, seal, requests = captured(g, provider)
    result = reconcile_captured_sse(g.gate, operation, seal)
    assert result["settled_now"] and result["new_requests"] == 0
    assert result["amount_microusd"] == 7
    assert g.runtime.close_dispatch_budget(g.plan.job_id, seal)["state"] == "FINALIZED"
    assert not reconcile_captured_sse(g.gate, operation, seal)["settled_now"]
    assert len(requests) == 1
    value = json.loads(g.gate.db.connection.execute("SELECT body FROM inference_valuations").fetchone()[0])
    assert value["usage"]["cache_write_tokens"] == 3
    assert g.gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 7


@pytest.mark.parametrize("case", ["truncated", "wrong_seal", "duplicate_capture", "still_running"])
def test_recovery_cannot_bypass_capture_or_runtime_uncertainty(gateway, provider, case):
    g = gateway
    operation, seal, requests = captured(g, provider, truncated=case == "truncated")
    db = g.gate.db.connection
    if case == "wrong_seal":
        seal = g.put({"schema": "strata/InferenceIngressSeal/1"})
    elif case == "duplicate_capture":
        row = db.execute("SELECT body FROM outbox WHERE kind='inference.wire_capture'").fetchone()
        db.execute("INSERT INTO outbox(kind,body) VALUES('inference.wire_capture',?)", (row[0],))
    elif case == "still_running":
        db.execute("UPDATE native_jobs SET state='RUNNING'")
    with pytest.raises(Fault):
        reconcile_captured_sse(g.gate, operation, seal)
    assert db.execute("SELECT state FROM inference_attempts").fetchone()[0] == "UNSETTLED"
    assert g.gate.budgets.status("a1")["uncertain"] and len(requests) == 1
