"""Derive helper cell drain from actual issued tools and captured native returns.

Terminal agent status and interrupted waits do not terminate a yielded cell.
This read-only retirement gate never cancels, replays or infers a missing result.
"""

import re

from .inference_transport import NATIVE_RESPONSE_BYTES, strict_json
from .native_retirement import _CompletedResponse, private_bytes
from .records import BudgetLedger
from .storage import canonical, require

POLICY = "native-source-bound-cell-drain/2"


def _text(value):
    if isinstance(value, str):
        return value
    require(isinstance(value, list) and all(isinstance(x, dict) and (
        x.get("type") in {"text", "input_text"} and isinstance(x.get("text"), str)
        or set(x) == {"type", "image_url"} and x["type"] == "input_image"
        and isinstance(x["image_url"], str) and x["image_url"].startswith("data:image/")) for x in value),
        "NATIVE_CELL_RESULT_SHAPE")
    return "\n".join(x["text"] for x in value if "text" in x)


def _status(output):
    text = _text(output)
    if re.fullmatch(r"aborted by user after [0-9]+(?:\.[0-9]+)?s", text):
        return "aborted", None
    lines = [line for line in text.splitlines() if line]
    require(len(lines) >= 3 and re.fullmatch(r"Wall time [0-9]+\.[0-9]+ seconds", lines[1]) and
            lines[2] == "Output:", "NATIVE_CELL_RESULT_SHAPE")
    found = re.fullmatch(r"Script running with cell ID ([A-Za-z0-9_-]{1,128})", lines[0])
    if found:
        return "pending", found[1]
    if lines[0] in {"Script completed", "Script terminated"}:
        return lines[0].removeprefix("Script "), None
    if len(lines) == 5 and lines[:1] == ["Script failed"] and lines[3] == "Script error:":
        absent = re.fullmatch(r"exec cell ([A-Za-z0-9_-]{1,128}) not found", lines[4])
        if absent:
            return "absent", absent[1]
    require(False, "NATIVE_CELL_DRAIN_UNKNOWN")


def require_native_cells_drained(db, cas, plan, thread, *, stopped_job=False):
    """Reconstruct from immutable per-call receipts, retaining history across compaction."""
    from .native_admission import context_metadata
    requests = db.execute("SELECT a.rowid ordinal,a.*,i.state,i.request FROM native_request_admissions a "
        "JOIN inference_attempts i ON i.operation=a.operation WHERE a.job=? AND a.thread=? ORDER BY a.rowid",
        (plan.job_id, thread)).fetchall()
    issued, observed, first_seen = {}, {}, {}
    for row in requests:
        require(row["state"] == "SETTLED", "METERING_UNKNOWN")
        attempt = strict_json(row["request"])
        require(attempt["runtime_job_id"] == plan.job_id and attempt["profile_digest"] == plan.profile_digest()
            and attempt["request_digest"] == row["request_digest"] and
            row["raw_ref"] == "cas:sha256:" + row["request_digest"], "NATIVE_CELL_SOURCE_SCOPE")
        if plan.ingress_policy is not None:
            from .native_ingress import require_ingress_capture
            require_ingress_capture(db, plan, row["operation"], row["request_digest"])
        raw, _ = private_bytes(db, cas, row["raw_ref"], 1024 * 1024)
        body = strict_json(raw)
        require(context_metadata(body)["thread_id"] == thread and isinstance(body.get("input"), list),
                "NATIVE_CELL_SOURCE_SCOPE")
        in_calls = {}
        for item in body["input"]:
            if not isinstance(item, dict) or item.get("type") not in {
                    "custom_tool_call", "function_call", "custom_tool_call_output", "function_call_output"}:
                continue
            key = item.get("call_id")
            require(isinstance(key, str) and 0 < len(key) <= 256, "NATIVE_CELL_RESULT_SHAPE")
            first_seen.setdefault(key, row["ordinal"])
            if item["type"] in {"custom_tool_call", "function_call"}:
                require(key not in in_calls, "NATIVE_CELL_RESULT_DUPLICATE")
                in_calls[key] = item
        seen = set()
        for output in body["input"]:
            if not isinstance(output, dict) or output.get("type") not in {
                    "custom_tool_call_output", "function_call_output"}:
                continue
            key = output.get("call_id")
            if key not in issued:
                continue
            call, ordinal = issued[key]
            fields = ("type", "namespace", "name", "call_id", "input" if call["name"] == "exec" else "arguments")
            require(row["ordinal"] > ordinal and key in in_calls and
                    all(in_calls[key].get(k) == call.get(k) for k in fields), "NATIVE_CELL_RESULT_SCOPE")
            value = output.get("output")
            require(output["type"] == ("custom_tool_call_output" if call["name"] == "exec"
                    else "function_call_output"), "NATIVE_CELL_RESULT_SCOPE")
            if call["name"] == "exec" and isinstance(value, str):
                # Native notify() emits arbitrary model-controlled strings under
                # the exec call ID. Even a perfect terminal/pending-header mimic
                # is not authoritative cell evidence. Silent native yields also
                # use this ambiguous shape: retain the hold until an unambiguous
                # frame or whole-process drain can establish closure.
                continue
            require(key not in seen, "NATIVE_CELL_RESULT_DUPLICATE")
            seen.add(key)
            require(isinstance(value, list) and value and isinstance(value[0], dict)
                    and value[0].get("type") in {"text", "input_text"}
                    or call["name"] == "wait" and isinstance(value, str)
                    and re.fullmatch(r"aborted by user after [0-9]+(?:\.[0-9]+)?s", value),
                    "NATIVE_CELL_RESULT_SHAPE")
            require(key not in observed or canonical(observed[key][0]) == canonical(value),
                    "NATIVE_CELL_RESULT_CHANGED")
            observed.setdefault(key, (value, row["ordinal"]))
        receipts = db.execute("SELECT body FROM ledger WHERE json_extract(body,'$.operation_id')=? "
            "AND json_extract(body,'$.posting')='settle'", (row["operation"],)).fetchall()
        require(len(receipts) == 1, "NATIVE_CELL_SOURCE_RECEIPT")
        receipt = BudgetLedger.model_validate_json(receipts[0][0])
        raw, media = private_bytes(db, cas, receipt.raw_usage_ref, NATIVE_RESPONSE_BYTES)
        parser = _CompletedResponse(plan.model, media)
        parser.feed(raw)
        parser.finish()
        for call in parser.response["output"]:
            if call.get("namespace") != "functions":
                continue
            name = call.get("name")
            require(name in {"exec", "wait"}, "NATIVE_CELL_UNKNOWN_TOOL")
            key = call.get("call_id")
            require(isinstance(key, str) and 0 < len(key) <= 256 and key not in issued and key not in first_seen,
                    "NATIVE_CELL_ISSUANCE_REUSED")
            require(call.get("type") == ("custom_tool_call" if name == "exec" else "function_call") and
                    isinstance(call.get("input" if name == "exec" else "arguments"), str),
                    "NATIVE_CELL_ISSUANCE_SHAPE")
            issued[key] = (call, row["ordinal"])
    require(type(stopped_job) is bool, "NATIVE_CELL_DRAIN_SCOPE")
    pending, known, unresolved = {}, set(), set()
    ambiguous_execs = set()
    for key, (call, ordinal) in issued.items():
        args = None
        if call["name"] == "wait":
            args = strict_json(call["arguments"])
            require(isinstance(args, dict) and isinstance(args.get("cell_id"), str) and
                    re.fullmatch(r"[A-Za-z0-9_-]{1,128}", args["cell_id"]) and
                    set(args) <= {"cell_id", "yield_time_ms", "max_tokens", "terminate"} and
                    ("terminate" not in args or type(args["terminate"]) is bool) and all(
                        key not in args or type(args[key]) is int and args[key] >= 0
                        for key in ("yield_time_ms", "max_tokens")), "NATIVE_CELL_WAIT_SCOPE")
        if key not in observed:
            require(stopped_job, "NATIVE_CELL_RESULT_MISSING")
            unresolved.add(key)
            if call["name"] == "exec":
                ambiguous_execs.add(key)
            continue
        output, observed_at = observed[key]
        status, cell = _status(output)
        if call["name"] == "exec":
            require(status in {"completed", "pending"}, "NATIVE_CELL_DRAIN_UNKNOWN")
            if status == "pending":
                require(cell not in known, "NATIVE_CELL_HANDLE_REUSED")
                known.add(cell)
                pending[cell] = observed_at
            continue
        target = args["cell_id"]
        if target not in known:
            # An earlier scalar-only exec cannot authenticate its yielded ID.
            # Only a stopped whole-job fence may dispose of this uncertainty;
            # never count this wait as proof of an owner's successful cleanup.
            require(stopped_job and ambiguous_execs, "NATIVE_CELL_WAIT_SCOPE")
            unresolved.add(key)
            continue
        # A model must have received the original yielded handle before issuing
        # this wait. A guessed concurrent handle cannot establish causal drain.
        if target in pending:
            require(ordinal >= pending[target], "NATIVE_CELL_WAIT_SCOPE")
        if status == "aborted":
            continue  # Native interruption cancels the wait, not necessarily its cell.
        if status == "pending":
            require(target in pending and cell == target, "NATIVE_CELL_WAIT_SCOPE")
        elif status in {"completed", "terminated", "absent"}:
            require(status != "absent" or cell == target, "NATIVE_CELL_WAIT_SCOPE")
            require(status != "terminated" or args.get("terminate") is True, "NATIVE_CELL_WAIT_SCOPE")
            pending.pop(target, None)
        else:
            require(False, "NATIVE_CELL_DRAIN_UNKNOWN")
    if pending or unresolved:
        require(stopped_job, "NATIVE_CELL_DRAIN_PENDING")
        from .native_process_drain import require_process_drain
        fence = require_process_drain(db, cas, plan)
        return {"policy": "native-process-fenced-cell-disposal/1", "issued_tools": len(issued),
                "observed_yielded_cells": len(known), "observed_pending_before_fence": len(pending),
                "unresolved_call_ids": sorted(unresolved), "pending_cells": 0, "process_fence": fence,
                "tool_success_inferred": False}
    return {"policy": POLICY, "issued_tools": len(issued), "yielded_cells": len(known), "pending_cells": 0}
