"""Operator-only settlement from an existing fenced transport capture; no I/O replay.

This does not qualify the rejected media type for future live forwarding. The
operator explicitly selects SSE decoding of already captured, request-bound
bytes. A complete terminal receipt is required, even after transport failure.
"""

import json
import math

from .accounting import EstimateBasis, TokenUsage, UsageValuation
from .inference_dispatch import InferenceAttempt
from .inference_transport import ResponsesUsage
from .native import NativeLaunch
from .native_gateway import require_gateway_seal
from .native_usage import POLICY as USAGE_POLICY
from .records import BudgetLedger
from .storage import Principal, canonical, digest, require

POLICY = "fenced-captured-sse-receipt-recovery/1"
OPERATOR = Principal("operator", "operator")


def reconcile_captured_sse(gate, operation, seal_ref):
    db, cas = gate.db.connection, gate.cas
    attempt_row = db.execute("SELECT * FROM inference_attempts WHERE operation=?", (operation,)).fetchone()
    require(attempt_row is not None and attempt_row["state"] in {"UNSETTLED", "SETTLED"},
            "RECEIPT_RECOVERY_NOT_STOPPED")
    attempt = InferenceAttempt.model_validate_json(attempt_row["request"])
    reserve = BudgetLedger.model_validate_json(attempt_row["reservation"])
    job = db.execute("SELECT * FROM native_jobs WHERE id=?", (attempt.runtime_job_id,)).fetchone()
    require(job is not None and job["state"] in {"UNSETTLED", "FINALIZED"}, "RECEIPT_RECOVERY_NOT_STOPPED")
    plan = NativeLaunch.model_validate_json(job["plan"])
    proof = cas.json(OPERATOR, "operator", seal_ref)
    require(proof.get("schema") == "strata/InferenceIngressSeal/1" and
            proof.get("is_example") is gate.simulation and proof.get("job_id") == plan.job_id and
            proof.get("profile_digest") == attempt.profile_digest == plan.profile_digest() and
            all(proof.get(k) is True for k in ("process_tree_dead", "ingress_closed", "handlers_fenced")) and
            operation in proof.get("attempt_ids", []), "DISPATCH_SEAL_UNVERIFIED")
    require_gateway_seal(gate.db, cas, plan, proof, gate.simulation)
    events = [dict(row) | {"body": json.loads(row["body"])} for row in db.execute(
        "SELECT * FROM outbox WHERE kind IN ('inference.http_response','inference.wire_capture') "
        "AND json_extract(body,'$.operation_id')=? ORDER BY cursor", (operation,))]
    require(len(events) == 2 and [v["kind"] for v in events] == [
                "inference.http_response", "inference.wire_capture"] and
            all(e["body"].get("simulation") is gate.simulation for e in events) and
            events[0]["body"].get("status") == 200 and events[0]["body"].get("identity_encoding") is True,
            "RECEIPT_RECOVERY_CAPTURE_REQUIRED")
    capture = events[1]["body"]
    raw = gate._private_ref(capture["raw_usage_ref"], 256 * 1024)
    require(len(raw) == capture["bytes"] and raw.startswith(b"event:"), "RECEIPT_RECOVERY_CAPTURE_REQUIRED")
    parser = ResponsesUsage(reserve.model_identity, "text/event-stream")
    parser.feed(raw)
    observed = parser.finish()
    provider_event = observed.pop("event")
    writes = observed.pop("cache_write_tokens", None)
    basis = EstimateBasis.model_validate_json(gate._private_ref(reserve.pricing_ref, 65536))
    tokens = TokenUsage.model_validate({k: observed[k] for k in (
        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens")} |
        {"model": reserve.model_identity, "cache_write_tokens": writes})
    amount = basis.estimate(tokens)
    valuation = UsageValuation.model_validate({"schema": "strata/UsageValuation/1",
        "kind": "api_equivalent_estimate", "basis_digest": basis.fingerprint(),
        "raw_usage_ref": capture["raw_usage_ref"], "usage": tokens, "amount_microusd": amount,
        "token_evidence": "synthetic_fixture" if gate.simulation else "provider_reported"})
    with gate.db.transaction() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS captured_receipt_recoveries "
                           "(operation TEXT PRIMARY KEY, proof_ref TEXT NOT NULL)")
    saved = db.execute("SELECT proof_ref FROM captured_receipt_recoveries WHERE operation=?", (operation,)).fetchone()
    if saved is None:
        require(job["started"] is not None and job["ended"] is not None and
                job["ended"] >= job["started"], "RECEIPT_RECOVERY_CLOCK_REQUIRED")
        # This is an observed native lifetime upper bound, not invented provider
        # latency. Model latency is not summed into campaign active-time budgets.
        wall = math.ceil((job["ended"] - job["started"]) * 1000)
        event_id = "capture-recovery-" + digest({"operation": operation})
        receipt = BudgetLedger.model_validate(reserve.model_dump() | {
            "posting": "settle", "source_event_id": event_id, "ledger_id": event_id,
            "raw_usage_ref": capture["raw_usage_ref"], "metering": "estimated",
            "reason": "reconcile: captured receipt; wall_ms is native lifetime upper bound; provider latency unknown",
            "usage": reserve.usage.model_dump() | observed | {"spend_microusd": amount, "wall_ms": wall}})
        body = {"schema": "strata/CapturedReceiptRecovery/1", "policy": POLICY, "usage_policy": USAGE_POLICY,
            "is_example": gate.simulation, "operation": operation, "seal_ref": seal_ref,
            "capture_ref": capture["raw_usage_ref"], "provider_event": provider_event,
            "source_event_cursors": [e["cursor"] for e in events], "receipt": receipt.model_dump(),
            "valuation": valuation.model_dump(), "latency_basis": "native_lifetime_upper_bound",
            "future_transport_qualified": False, "new_requests": 0}
        ref = cas.put(OPERATOR, "operator", "operator", canonical(body))
        with gate.db.transaction() as connection:
            connection.execute("INSERT INTO captured_receipt_recoveries VALUES(?,?)", (operation, ref))
            gate.db.event(connection, "inference.capture_recovery_prepared", {"operation": operation, "proof_ref": ref})
    else:
        ref = saved["proof_ref"]
        body = cas.json(OPERATOR, "operator", ref)
        require(body["policy"] == POLICY and body["usage_policy"] == USAGE_POLICY and
                body["operation"] == operation and body["seal_ref"] == seal_ref and
                body["capture_ref"] == capture["raw_usage_ref"] and body["provider_event"] == provider_event and
                body["valuation"] == valuation.model_dump(), "RECEIPT_RECOVERY_CONFLICT")
        receipt = BudgetLedger.model_validate(body["receipt"])
    changed = gate.settle(operation, provider_event, receipt, valuation=valuation)
    return {"proof_ref": ref, "settled_now": changed, "amount_microusd": amount,
            "future_transport_qualified": False, "new_requests": 0}
