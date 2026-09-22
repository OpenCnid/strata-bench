"""Reconstruct a stopped native/vanilla smoke bundle without launching anything.

This verifies recorded evidence, not isolation, live model reasoning, a scorer,
or a complete checkpoint. Invocation requires an independently retained seal.
"""

import argparse
import json
import math
import os
from collections import Counter
from pathlib import Path, PureWindowsPath
from typing import Literal

from pydantic import Field

from mcbench.accounting import EstimateBasis, UsageValuation
from mcbench.budgets import Budgets
from mcbench.contracts import ActionAck, ActionBatch, Digest, Id, Observation, Positive, RpcRequest, Strict, UInt, Utc
from mcbench.inference_dispatch import DispatchBound, EstimateDispatchBound, InferenceAttempt
from mcbench.inference_transport import ResponsesUsage, strict_json
from mcbench.native_export import OPERATOR, inspect_native_source
from mcbench.server_health import inspect_server_log
from mcbench.storage import canonical, digest, reject_links, require, safe_relative

from .evidence_bundle import EvidenceBundle, EvidenceCAS
from .saved_blocks import NbtReader, field, unpack_chunk

POLICY = "sealed-native-vanilla-evidence-join/1"
SCOPE = ("campaign_id", "agent_id", "epoch")
TERMINAL = {"completed", "emitted", "failed", "cancelled", "rejected", "unknown"}
PRIMITIVE_POLICY = "durable-pre-dispatch-charge/1"


class PrimitiveAccounting(Strict):
    schema_: Literal["strata/MineflayerPrimitiveAccounting/1"] = Field(alias="schema")
    policy: Literal["durable-pre-dispatch-charge/1"]
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    opening_primitive_events: UInt


class PrimitiveCharge(Strict):
    schema_: Literal["strata/MineflayerPrimitiveCharge/1"] = Field(alias="schema")
    policy: Literal["durable-pre-dispatch-charge/1"]
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    request_id: Id
    action_seq: Positive
    request_digest: Digest
    charge_seq: Positive
    action_charge_seq: Positive
    safety_release: bool
    recorded_at: Utc
    mono_ms: UInt
    emission_confirmed: Literal[False]


class NativeGameEvidencePlan(Strict):
    schema_: Literal["strata/NativeGameEvidencePlan/1"] = Field(alias="schema")
    bundle: str
    seal_sha256: Digest
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    job_id: Id


def windows(value):
    return PureWindowsPath(value.removeprefix("\\\\?\\"))


def bootstrap_inventory(bundle):
    """Follow the sealed bootstrap's file hashes, never its original OS paths.

    Older flat Windows seals omitted deep paths. The bootstrap inventory was
    captured before launch and its own bytes ARE in the flat seal. Its archived
    entries therefore retain a hash chain to that original external seal.
    """
    original = windows(bundle.json("run/intent.json")["plan"]["output"])
    require(original.is_absolute(), "NATIVE_GAME_BOOTSTRAP_MISMATCH")
    bootstrap = bundle.json("run/native/broker-runtime.manifest.json")
    require(bootstrap.get("schema") == "strata/NativeBootstrap/1"
            and bootstrap["inventory"].get("schema") == "strata/LaunchFileInventory/1",
            "NATIVE_GAME_BOOTSTRAP_MISMATCH")
    entries = bootstrap["inventory"]["files"]
    require(isinstance(entries, list) and len(entries) <= 16384, "EVIDENCE_QUOTA")
    output = []
    for entry in entries:
        old = windows(entry["path"])
        if old.is_relative_to(original):
            output.append({"path": "run/" + old.relative_to(original).as_posix(),
                           "sha256": entry["sha256"], "bytes": entry["bytes"]})
    require(len({e["path"].casefold() for e in output}) == len(output), "EVIDENCE_INVENTORY_CONFLICT")
    return output


def same_scope(value, plan):
    require(all(value[k] == getattr(plan, k) for k in SCOPE), "NATIVE_GAME_EVIDENCE_SCOPE")


def events(db, kind):
    return [(r["cursor"], strict_json(r["body"])) for r in db.execute(
        "SELECT cursor,body FROM outbox WHERE kind=? ORDER BY cursor", (kind,))]


def one_event(db, kind, key, value):
    rows = [(cursor, body) for cursor, body in events(db, kind) if body.get(key) == value]
    require(len(rows) == 1, "NATIVE_GAME_EVENT_INCOMPLETE")
    return rows[0]


def model_usage(db, cas, native, source):
    """Reparse wire receipts and reconcile each distinct request exactly once."""
    require(native.provider == "strata_local_fixture", "NATIVE_GAME_PROFILE_UNSUPPORTED")
    receipts = {r["record"]["operation_id"]: r["record"] for r in source["ledger"]
                if r["record"]["posting"] == "settle"}
    totals = Counter()
    by_thread = {}
    provider_events = set()
    units = set()
    calls = []
    for admission in source["attempts"]:
        attempt = admission["dispatch"]
        request = InferenceAttempt.model_validate(strict_json(attempt["request"]))
        reserve, receipt = strict_json(attempt["reservation"]), receipts[admission["operation"]]
        require(request.runtime_job_id == native.job_id and request.provider == native.provider
                and request.auth_mode == native.auth_mode, "NATIVE_GAME_RECEIPT_SCOPE")
        for key in ("campaign_id", "agent_id", "epoch", "operation_id", "parent_operation_id",
                    "campaign_account", "kind", "pricing_ref", "model_identity"):
            require(receipt[key] == reserve[key], "NATIVE_GAME_RECEIPT_SCOPE")
        raw = cas.read(OPERATOR, "operator", receipt["raw_usage_ref"], max_bytes=256 * 1024)
        media = db.execute("SELECT media_type FROM objects WHERE namespace='operator' AND ref=?",
                           (receipt["raw_usage_ref"],)).fetchone()[0]
        parser = ResponsesUsage(native.model, media)
        parser.feed(raw)
        measured = parser.finish()
        require(measured["event"] not in provider_events, "NATIVE_GAME_RECEIPT_DUPLICATE")
        provider_events.add(measured["event"])
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "model_calls"):
            require(receipt["usage"][key] == measured[key], "NATIVE_GAME_USAGE_MISMATCH")
        bound_body = strict_json(cas.read(OPERATOR, "operator", request.bound_ref, max_bytes=65536))
        bound_type = EstimateDispatchBound if bound_body.get("schema") == "strata/InferenceDispatchBound/2" else DispatchBound
        bound = bound_type.model_validate(bound_body)
        require(bound.is_example is True and bound.runtime_job_id == native.job_id
                and bound.profile_digest == native.profile_digest()
                and bound.request_digest == request.request_digest
                and bound.reservation_digest == digest(reserve)
                and bound.pricing_ref == receipt["pricing_ref"]
                and bound.provider == request.provider and bound.auth_mode == request.auth_mode
                and bound.finite_dispatch_bound_verified and bound.pricing_semantics_verified,
                "NATIVE_GAME_BOUND_MISMATCH")
        price = strict_json(cas.read(OPERATOR, "operator", bound.pricing_ref, max_bytes=65536))
        fingerprint = {"provider_event_id": measured["event"], "receipt": receipt}
        valuation = admission["valuation"]
        if isinstance(bound, EstimateDispatchBound):
            basis = EstimateBasis.model_validate(price)
            value = UsageValuation.model_validate(valuation)
            require(value.kind == "api_equivalent_estimate" and value.token_evidence == "synthetic_fixture"
                    and value.basis_digest == basis.fingerprint()
                    and value.raw_usage_ref == receipt["raw_usage_ref"]
                    and value.usage.model == native.model
                    and value.usage.cache_write_tokens == measured.get("cache_write_tokens")
                    and all(getattr(value.usage, k) == measured[k] for k in
                            ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens"))
                    and value.amount_microusd == basis.estimate(value.usage)
                    and receipt["metering"] == "estimated", "NATIVE_GAME_VALUATION_MISMATCH")
            amount = value.amount_microusd
            unit = "api_equivalent_estimate_of_synthetic_tokens"
            fingerprint["valuation"] = value.model_dump()
        else:
            require(valuation is None and receipt["metering"] == "reported"
                    and price.get("schema") == "strata/SyntheticTokenPricing/1"
                    and price.get("is_example") is True, "NATIVE_GAME_PRICING")
            keys = ("input_microusd_per_token", "cached_microusd_per_token", "output_microusd_per_token")
            require(all(type(price.get(k)) is int and 0 <= price[k] <= 2**53 - 1 for k in keys),
                    "NATIVE_GAME_PRICING")
            amount = ((measured["input_tokens"] - measured["cached_input_tokens"]) * price[keys[0]]
                      + measured["cached_input_tokens"] * price[keys[1]]
                      + measured["output_tokens"] * price[keys[2]])
            unit = "synthetic_fixture_units"
        require(amount == receipt["usage"]["spend_microusd"]
                and digest(fingerprint) == attempt["receipt_digest"]
                and digest({"provider": request.provider, "event": measured["event"]}) == attempt["provider_event"],
                "NATIVE_GAME_RECEIPT_MISMATCH")
        _, capture = one_event(db, "inference.wire_capture", "operation_id", admission["operation"])
        require(capture == {"operation_id": admission["operation"], "raw_usage_ref": receipt["raw_usage_ref"],
                            "bytes": len(raw), "simulation": True}, "NATIVE_GAME_CAPTURE_MISMATCH")
        units.add(unit)
        usage = {k: measured[k] for k in ("input_tokens", "cached_input_tokens", "output_tokens", "model_calls")}
        usage.update(amount=amount, request_wall_ms=receipt["usage"]["wall_ms"])
        totals.update(usage)
        by_thread.setdefault(admission["thread"], Counter()).update(usage)
        calls.append({"operation_id": admission["operation"], "thread_id": admission["thread"],
                      "receipt_digest": attempt["receipt_digest"], "raw_usage_ref": receipt["raw_usage_ref"], **usage})
    require(len(units) == 1, "NATIVE_GAME_MIXED_UNITS")
    aggregate = Budgets.exposures(db)[native.operation_id]
    require(all(aggregate[k] == totals[k] for k in ("input_tokens", "output_tokens", "model_calls"))
            and aggregate["spend_microusd"] == totals["amount"], "NATIVE_GAME_ACCOUNTING_MISMATCH")
    return {"model_evidence": "scripted_provider", "unit": next(iter(units)),
            "real_model_requests": 0, "actual_charge_microusd": None,
            "totals": dict(totals), "participants": {k: dict(v) for k, v in sorted(by_thread.items())},
            "calls": calls, "closed_envelopes": len(source["participants"])}


def worker_evidence(db, source, plan, config):
    require([r[0] for r in db.execute("SELECT epoch FROM epochs ORDER BY epoch")] == [plan.epoch],
            "NATIVE_GAME_EVIDENCE_SCOPE")
    rows = db.execute("SELECT * FROM events ORDER BY cursor").fetchall()
    require([r["cursor"] for r in rows] == list(range(1, len(rows) + 1)), "NATIVE_GAME_EVENT_GAP")
    observations, acks, charge_traces, accounting = {}, {}, [], []
    ack_order = []
    for row in rows:
        body = strict_json(row["body"])
        if row["kind"] == "observation_delivery":
            observation = Observation.model_validate(body)
            same_scope(body, plan)
            require(not observation.is_example and observation.mode == "structured"
                    and observation.state is not None and observation.observation_id not in observations,
                    "NATIVE_GAME_OBSERVATION_INVALID")
            observations[observation.observation_id] = (row["cursor"], body)
        elif row["kind"] == "ack":
            ack = ActionAck.model_validate(body)
            same_scope(body, plan)
            require(not ack.is_example, "EXAMPLE_NOT_EXECUTABLE")
            acks.setdefault(ack.request_id, []).append((row["cursor"], body))
            ack_order.append(ack.seq)
        elif row["kind"] in {"primitive_accounting", "primitive_charge"}:
            model = PrimitiveAccounting if row["kind"] == "primitive_accounting" else PrimitiveCharge
            parsed = model.model_validate(body)
            same_scope(body, plan)
            (accounting if row["kind"] == "primitive_accounting" else charge_traces).append((row["cursor"], parsed))
        else:
            require(row["kind"] == "public_signal", "NATIVE_GAME_EVENT_KIND")
    require(ack_order == list(range(1, len(ack_order) + 1)), "NATIVE_GAME_ACK_SEQUENCE")
    counters = dict(db.execute("SELECT name,value FROM counters"))
    require(all(type(v) is int and v >= 0 for v in counters.values()), "NATIVE_GAME_COUNTER_MISMATCH")
    actions, primitives = [], 0
    action_rows = db.execute("SELECT * FROM actions ORDER BY seq").fetchall()
    require(action_rows and len(action_rows) <= 10000, "NATIVE_GAME_ACTION_MISSING")
    for index, row in enumerate(action_rows, 1):
        batch_raw, terminal = strict_json(row["request"]), strict_json(row["ack"])
        batch, ack = ActionBatch.model_validate(batch_raw), ActionAck.model_validate(terminal)
        same_scope(batch_raw, plan)
        same_scope(terminal, plan)
        require(not batch.is_example and not ack.is_example and batch.mode == "structured"
                and batch.lease_id == config["lease_id"] and row["epoch"] == batch.epoch
                and row["seq"] == batch.seq == index and row["request_id"] == batch.request_id == ack.request_id
                and row["digest"] == digest(batch_raw) and ack.action_seq == batch.seq,
                "NATIVE_GAME_ACTION_BINDING")
        history = acks.get(batch.request_id, [])
        require(history and history[-1][1] == terminal
                and sum(h["status"] in TERMINAL for _, h in history) == 1
                and all(h["action_seq"] == batch.seq for _, h in history)
                and history[0][1]["status"] == "accepted"
                and all(h["status"] in {"accepted", "executing"} for _, h in history[:-1]),
                "NATIVE_GAME_ACK_INCOMPLETE")
        require(ack.status in {"completed", "emitted"} and ack.release_confirmed
                and not ack.requires_resync and ack.emitted_events is not None
                and ack.completed_mono_ms is not None, "NATIVE_GAME_ACTION_UNCERTAIN")
        before = observations.get(batch.observation_id)
        after = observations.get(ack.result_observation_id)
        require(before is not None and after is not None and before[0] < history[0][0]
                and after[0] < history[-1][0] and after[0] > history[0][0], "NATIVE_GAME_OBSERVATION_BINDING")
        require(before[1]["state_revision"] == batch.expected_state_revision
                and before[1]["control_revision"] == batch.control_revision
                and before[1]["capability_digest"] == after[1]["capability_digest"] == batch.capability_digest
                and after[1]["last_action_seq"] == batch.seq, "NATIVE_GAME_OBSERVATION_BINDING")
        primitives += ack.emitted_events
        actions.append({"request_id": batch.request_id, "action_seq": batch.seq, "status": ack.status,
                        "primitive_events": ack.emitted_events, "request_digest": digest(batch_raw),
                        "receipt_digest": digest(terminal), "result_observation_id": ack.result_observation_id})
    require(set(acks) == {a["request_id"] for a in actions}
            and counters.get("primitive_events") == primitives <= config["primitive_limit"]
            and counters.get(f"{plan.epoch}:action") == len(actions)
            and counters.get(f"{plan.epoch}:ack") == len(ack_order)
            and counters.get(f"{plan.epoch}:observation") == len(observations), "NATIVE_GAME_COUNTER_MISMATCH")
    root = next(p["participant"]["thread"] for p in source["participants"] if p["participant"]["depth"] == 0)
    seen_calls, returned_acks, returned_observations, capabilities = set(), [], [], []
    request_preimages = 0
    actions_by_id = {a["request_id"]: a for a in actions}
    for call in source["game_calls"]:
        require(call["runtime"] == plan.job_id and call["thread"] == root and call["request"] not in seen_calls,
                "NATIVE_GAME_BROKER_SCOPE")
        seen_calls.add(call["request"])
        response = strict_json(call["result"])
        require(response.get("schema") == "strata/GameResponse/1" and response.get("status") == "ok"
                and response.get("request_id") == call["request"], "NATIVE_GAME_RESPONSE_INVALID")
        matches = [c for c in source["broker_calls"] if c["state"] == "RETURNED"
                   and c["result_digest"] == digest(response)
                   and strict_json(c["body"])["thread"] == root
                   and strict_json(c["body"])["tool"] == "game"]
        require(matches, "NATIVE_GAME_BROKER_RESULT_MISSING")
        value = response["result"]
        if "request_body" in call:
            request = RpcRequest.model_validate(call["request_body"])
            same_scope(request.model_dump(), plan)
            require(request.request_id == call["request"]
                    and digest(request.model_dump()) == call["fingerprint"], "NATIVE_GAME_REQUEST_MISMATCH")
            if request.method == "act":
                action = actions_by_id.get(request.action.request_id)
                require(action is not None and action["request_digest"] == digest(request.action.model_dump())
                        and value.get("schema") == "mcbench/ActionAck/1"
                        and value.get("request_id") == request.action.request_id, "NATIVE_GAME_REQUEST_MISMATCH")
            elif request.method in {"action_status", "cancel"}:
                require(value.get("schema") == "mcbench/ActionAck/1"
                        and value.get("request_id") == request.target_request_id, "NATIVE_GAME_REQUEST_MISMATCH")
            else:
                expected = {"observe": "mcbench/Observation/1", "observe.page": "mcbench/Observation/1",
                            "wait_events": "mcbench/Observation/1", "capabilities": "strata/Capabilities/1"}
                require(request.method in expected and value.get("schema") == expected[request.method],
                        "NATIVE_GAME_REQUEST_MISMATCH")
            request_preimages += 1
        if value.get("schema") == "mcbench/Observation/1":
            require(value.get("observation_id") in observations
                    and observations[value["observation_id"]][1] == value, "NATIVE_GAME_OBSERVATION_BINDING")
            returned_observations.append(value)
        elif value.get("schema") == "mcbench/ActionAck/1":
            require(any(value == a for _, a in acks.get(value.get("request_id"), [])), "NATIVE_GAME_RECEIPT_MISMATCH")
            returned_acks.append(value)
        else:
            require(value.get("schema") == "strata/Capabilities/1", "NATIVE_GAME_RESPONSE_INVALID")
            capabilities.append(value)
    require(returned_observations and all(any(digest(a) == action["receipt_digest"] for a in returned_acks)
                                         for action in actions), "NATIVE_GAME_RECEIPT_MISSING")
    require(len(capabilities) == 1, "NATIVE_GAME_CAPABILITY_MISSING")
    cap = capabilities[0]
    body = {k: v for k, v in cap.items() if k not in {"digest", "epoch", "lease_id"}}
    require(cap["digest"] == digest(body) and cap["epoch"] == plan.epoch
            and cap["lease_id"] == config["lease_id"] and cap["backend"] == "mineflayer"
            and cap["profile"] == "vanilla-development/1" and not cap["keybindings"]
            and all(o[1]["capability_digest"] == cap["digest"] for o in observations.values()),
            "NATIVE_GAME_CAPABILITY_MISMATCH")
    trace_verified = False
    if cap.get("primitive_accounting") is not None or accounting or charge_traces:
        require(cap.get("primitive_accounting") == {"policy": PRIMITIVE_POLICY, "emission_confirmation": False}
                and len(accounting) == 1 and accounting[0][1].opening_primitive_events == 0,
                "NATIVE_GAME_PRIMITIVE_POLICY")
        charged, last_mono = Counter(), -1
        for index, (cursor, charge) in enumerate(charge_traces, 1):
            action = actions_by_id.get(charge.request_id)
            history = acks.get(charge.request_id, [])
            charged[charge.request_id] += 1
            require(action is not None and history and accounting[0][0] < history[0][0] < cursor < history[-1][0]
                    and charge.charge_seq == index and charge.action_charge_seq == charged[charge.request_id]
                    and charge.action_seq == action["action_seq"] and charge.request_digest == action["request_digest"]
                    and last_mono <= charge.mono_ms <= history[-1][1]["completed_mono_ms"],
                    "NATIVE_GAME_PRIMITIVE_BINDING")
            last_mono = charge.mono_ms
        require(len(charge_traces) == primitives and all(charged[a["request_id"]] == a["primitive_events"]
                for a in actions), "NATIVE_GAME_PRIMITIVE_INCOMPLETE")
        trace_verified = True
    return {"actions": actions, "primitive_events": primitives, "game_calls": len(seen_calls),
            "observations": len(observations), "returned_observations": len(returned_observations),
            "request_preimages_verified": request_preimages,
            "request_preimages_complete": request_preimages == len(seen_calls),
            "primitive_trace_verified": trace_verified, "primitive_charges_confirm_emission": False,
            "capability_digest": cap["digest"]}, cap, list(observations.values())


def stop_evidence(db, bundle, native, plan):
    rows = db.execute("SELECT * FROM native_worker_bindings").fetchall()
    require(len(rows) == 1 and rows[0]["job"] == plan.job_id, "NATIVE_GAME_STOP_SCOPE")
    row = rows[0]
    require(strict_json(row["scope"]) == {k: getattr(plan, k) for k in SCOPE}
            and row["state"] == "STOPPED" and row["stop_request"] and row["stop_result"], "NATIVE_GAME_STOP_UNCERTAIN")
    request = RpcRequest.model_validate(strict_json(row["stop_request"]))
    same_scope(request.model_dump(), plan)
    require(request.method == "stop_all" and request.action is None and request.target_request_id is None,
            "NATIVE_GAME_STOP_UNCERTAIN")
    response = strict_json(row["stop_result"])
    require(response == {"schema": "strata/GameResponse/1", "request_id": request.request_id,
                         "status": "ok", "result": {"status": "stopped"}}, "NATIVE_GAME_STOP_UNCERTAIN")
    grant = bundle.json("run/native/worker.json")
    same_scope(grant, plan)
    require(digest(grant) == row["grant_digest"]
            and grant == bundle.json(f"run/worker/grant-{plan.epoch}.json"), "NATIVE_GAME_STOP_SCOPE")
    cursors = []
    for kind in ("bound", "stop_intent", "stopped"):
        cursor, event = one_event(db, "native.worker_" + kind, "job", native.job_id)
        expected = {"job": native.job_id, **{k: getattr(plan, k) for k in SCOPE}}
        expected.update({"grant_digest": row["grant_digest"]} if kind == "bound" else {"request_id": request.request_id})
        require(event == expected, "NATIVE_GAME_STOP_SCOPE")
        cursors.append(cursor)
    require(cursors == sorted(set(cursors)), "NATIVE_GAME_STOP_ORDER")
    final, value = one_event_for_state(db, native.job_id, "FINALIZED")
    require(final > cursors[-1] and value["returncode"] == 0, "NATIVE_GAME_STOP_ORDER")
    return {"native_state": "FINALIZED", "game_lane": "STOPPED",
            "stop_request_digest": digest(request.model_dump()), "stop_result_digest": digest(response),
            "complete_checkpoint": False, "shutdown_timing_qualified": False}


def one_event_for_state(db, job, state):
    rows = [(c, b) for c, b in events(db, "runtime.state") if b.get("job_id") == job and b.get("state") == state]
    require(len(rows) == 1, "NATIVE_GAME_STATE_AMBIGUOUS")
    return rows[0]


def worker_runtime_evidence(bundle, intent, cap):
    """Join the pinned worker's recorded lease; archived paths stay inert data.

    This does not imply arbitrary-process isolation or archive external runtime
    files. Their independently held pins and source manifest remain explicit.
    """
    plan = intent["plan"]
    result = bundle.json("run/result.json")
    pinned = plan["schema"] in {"strata/M0NativeGameSmoke/3", "strata/M0NativeGameRecovery/2"}
    if not pinned:
        require("worker_runtime" not in plan and "worker_runtime" not in result
                and "run/worker-runtime.json" not in bundle.files, "NATIVE_GAME_WORKER_PROFILE")
        return {"pinned": False, "external_runtime_bytes_archived": False}
    reference = plan["worker_runtime"]
    require(set(reference) == {"path", "sha256"} and "node" not in plan,
            "NATIVE_GAME_WORKER_PROFILE")
    raw = bundle.read("run/worker-runtime.json", maximum=16 * 1024**2)
    import hashlib
    require(hashlib.sha256(raw).hexdigest() == reference["sha256"], "NATIVE_GAME_WORKER_MANIFEST")
    body = strict_json(raw)
    root = windows(body["root"])
    require(root.is_absolute() and body["schema"] == "strata/WorkerRuntimeBundle/1"
            and body["profile"] == "vanilla1192-private-worker/1"
            and body["python_arguments"] == ["-I", "-S", "-B"], "NATIVE_GAME_WORKER_PROFILE")
    files = {windows(e["path"]).relative_to(root).as_posix(): e for e in body["inventory"]["files"]}
    require(len(files) == len(body["inventory"]["files"]) and 0 < len(files) < 12000,
            "NATIVE_GAME_WORKER_MANIFEST")
    from mcbench.worker_bundle import WORKER_PATHS
    require(all(windows(body[key]) == root / name and name in files for key, name in WORKER_PATHS.items()),
            "NATIVE_GAME_WORKER_MANIFEST")
    modules = {PureWindowsPath(name).name: e["sha256"] for name, e in files.items()
               if name.startswith("backends/mineflayer/dist/src/") and name.count('/') == 4 and name.endswith('.js')}
    schemas = {name: files[f"schemas/v1/public/{name}.json"]["sha256"]
               for name in ("ActionBatch", "ActionAck", "Observation", "RpcRequest")}
    require(digest(modules) == cap["implementation_digest"]
            and digest(schemas) == cap["schema_digest"]
            and files["backends/mineflayer/package-lock.json"]["sha256"] == cap["dependency_lock_digest"],
            "NATIVE_GAME_WORKER_CAPABILITY")
    expected = {"schema": "strata/HeldWorkerRuntime/1", "manifest_sha256": reference["sha256"],
        "policy": "expected-bundle-deny-write-through-owned-stop/1", "files": len(files),
        "bytes": sum(e["bytes"] for e in files.values()), "manifest_held": True,
        "isolation_qualified": False, "runtime_qualified": False,
        "owned_processes": {name: {"parent_returncode": 0, "active_processes": 0}
                            for name in ("worker-preflight", "worker-driver", "server-driver")},
        "held_through_owned_stop": True, "root": body["root"],
        "preflight_argv": [body["node"], body["worker"], "--check-vanilla-runtime"],
        "worker_argv": [body["node"], body["worker"], str(windows(plan["output"]) / "worker-config.json")]}
    require(result.get("worker_runtime") == expected and "worker_runtime_error" not in result,
            "NATIVE_GAME_WORKER_CUSTODY")
    return {"pinned": True, "manifest_sha256": reference["sha256"], "files": len(files),
            "held_through_owned_stop": True, "isolation_qualified": False, "external_runtime_bytes_archived": False}


def source_evidence(bundle, native, intent, cap):
    pins = bundle.json("source-pins.json")
    require(isinstance(pins, dict) and pins and isinstance(intent.get("source_pins"), dict), "NATIVE_GAME_SOURCE_PINS")
    for name, sha in pins.items():
        safe_relative(name)
        require(bundle.files.get("source/" + name) is not None
                and bundle.files["source/" + name].sha256 == sha, "NATIVE_GAME_SOURCE_PINS")
    require(all(pins.get(k) == v for k, v in intent["source_pins"].items()), "NATIVE_GAME_SOURCE_PINS")
    modules = {PureWindowsPath(k).name: v for k, v in pins.items()
               if k.startswith("backends/mineflayer/dist/src/") and k.count("/") == 4 and k.endswith(".js")}
    require(modules and digest(modules) == cap["implementation_digest"], "NATIVE_GAME_SOURCE_PINS")
    require(bundle.files["run/native/broker-runtime.manifest.json"].sha256 == native.bootstrap_digest,
            "NATIVE_GAME_BOOTSTRAP_MISMATCH")
    bootstrap = bundle.json("run/native/broker-runtime.manifest.json")
    require(bootstrap.get("schema") == "strata/NativeBootstrap/1", "NATIVE_GAME_BOOTSTRAP_MISMATCH")
    # Map archived Windows paths lexically; never follow them into current installs.
    original = windows(intent["plan"]["output"])
    external = []
    for entry in bootstrap["inventory"]["files"]:
        old_path = windows(entry["path"])
        if old_path.is_relative_to(original):
            archived = "run/" + old_path.relative_to(original).as_posix()
            actual = bundle.files.get(archived)
            require(actual is not None and actual.sha256 == entry["sha256"] and actual.bytes == entry["bytes"],
                    "NATIVE_GAME_BOOTSTRAP_MISMATCH")
        else:
            require(old_path == windows(native.executable) and entry["sha256"] == native.binary_digest,
                    "NATIVE_GAME_EXTERNAL_PIN")
            external.append(entry["sha256"])
    require(external == [native.binary_digest], "NATIVE_GAME_EXTERNAL_PIN")
    lock = bundle.files.get("source/backends/mineflayer/package-lock.json")
    schema_names = ("ActionBatch", "ActionAck", "Observation", "RpcRequest")
    schemas = {name: bundle.files.get(f"source/schemas/v1/public/{name}.json") for name in schema_names}
    dependency_bytes_verified = lock is not None and all(schemas.values())
    if lock is not None or any(schemas.values()):
        require(dependency_bytes_verified and lock.sha256 == cap["dependency_lock_digest"]
                and digest({name: entry.sha256 for name, entry in schemas.items()}) == cap["schema_digest"],
                "NATIVE_GAME_DEPENDENCY_PINS")
    return {"source_manifest_digest": digest(pins), "archived_source_files": len(pins),
            "native_profile_digest": native.profile_digest(), "native_binary_digest": native.binary_digest,
            "dovetail_commit": native.dovetail_commit, "bootstrap_digest": native.bootstrap_digest,
            "worker_implementation_digest": cap["implementation_digest"],
            "worker_dependency_lock_digest": cap["dependency_lock_digest"],
            "worker_schema_digest": cap["schema_digest"], "pack_lock_qualified": False,
            "dependency_lock_and_schema_bytes_verified": dependency_bytes_verified,
            "external_executable_archived": False,
            "worker_runtime": worker_runtime_evidence(bundle, intent, cap)}


def saved_player_evidence(bundle, observations):
    before, after = [NbtReader(unpack_chunk(bundle.read("run/player-" + phase + ".dat"), 1)).root()
                     for phase in ("before", "after")]
    rotations = [field(value, "Rotation", 9) for value in (before, after)]
    positions = field(after, "Pos", 9)
    # NBT lists carry their element tag kind separately from the payload list.
    require(all(v[0] == 5 and len(v[1]) == 2 for v in rotations)
            and positions[0] == 6 and len(positions[1]) == 3, "NATIVE_GAME_SAVED_PLAYER")
    rotation = [t.value for t in rotations[1][1]]
    position = [t.value for t in positions[1]]
    latest = max(observations, key=lambda o: o[1]["seq"])[1]["state"]
    yaw = (180 - math.degrees(latest["yaw"]) + 180) % 360 - 180
    yaw_error = abs((rotation[0] - yaw + 180) % 360 - 180)
    pitch_error = abs(rotation[1] + math.degrees(latest["pitch"]))
    require(all(math.isfinite(v) for v in [*rotation, *position])
            and yaw_error <= .01 and pitch_error <= .01
            and all(abs(position[i] - latest["position"][axis]) <= .01 for i, axis in enumerate(("x", "y", "z"))),
            "NATIVE_GAME_SAVED_PLAYER")
    return {"orientation_changed": rotations[0] != rotations[1], "position_matches": True,
            "orientation_matches": True, "complete_checkpoint": False}


def inspect_native_game(plan: NativeGameEvidencePlan):
    bundle = EvidenceBundle(plan.bundle, plan.seal_sha256, inventory_extension=bootstrap_inventory)
    additional = len(bundle.files) - len(bundle.primary_files)
    custody = {"direct_manifest_inventory": "fail" if additional else "pass",
               "direct_files": len(bundle.primary_files), "transitive_bootstrap_files": additional,
               "complete_transitive_inventory": "pass", "original_seal_replaced": False}
    intent, config = bundle.json("run/intent.json"), bundle.json("run/worker-config.json")
    require(intent.get("schema") == "strata/M0NativeGameIntent/1"
            and intent.get("model_provider") == "synthetic" and intent.get("real_model_requests") == 0
            and intent.get("authentic_game") is True and intent.get("shared_desktop_input") is False
            and config.get("server_kind") == "vanilla", "NATIVE_GAME_PROFILE_UNSUPPORTED")
    same_scope(config, plan)
    with bundle.database("run/native/synthetic.sqlite") as db, bundle.database("run/worker/actions.sqlite") as worker:
        cas = EvidenceCAS(db, bundle, "run/native/objects")
        native, source, _ = inspect_native_source(db, cas, plan.job_id, simulation=True)
        same_scope(native.model_dump(), plan)
        row = db.execute("SELECT * FROM native_jobs WHERE id=?", (plan.job_id,)).fetchone()
        reserve = next(r["record"] for r in source["ledger"]
                       if r["record"]["operation_id"] == native.operation_id and r["record"]["posting"] == "reserve")
        require(row["returncode"] == 0 and row["plan_digest"] == digest({
                    "plan": strict_json(row["plan"]), "reserve": reserve, "fixture_argv": None})
                and row["role"] == native.role and row["parent"] is None
                and (row["campaign"], row["agent"], row["epoch"]) == (plan.campaign_id, plan.agent_id, plan.epoch),
                "NATIVE_GAME_JOB_MISMATCH")
        require(db.execute("SELECT COUNT(*) FROM native_jobs").fetchone()[0] == 1, "NATIVE_GAME_JOB_MISMATCH")
        model = model_usage(db, cas, native, source)
        game, cap, observations = worker_evidence(worker, source, plan, config)
        stop = stop_evidence(db, bundle, native, plan)
        pins = source_evidence(bundle, native, intent, cap)
        saved = saved_player_evidence(bundle, observations)
        from .native_game_retention import inspect_retention, inspect_stopped_components
        retention = inspect_retention(db, cas, bundle, native, intent)
        started, ended = row["started"], row["ended"]
        require(all(type(v) in (int, float) and math.isfinite(v) for v in (started, ended))
                and 0 < started <= ended, "NATIVE_GAME_CLOCK_INVALID")
        tools = source["broker_calls"]
        require(all(type(c["elapsed_ns"]) is int and c["elapsed_ns"] >= 0 for c in tools),
                "NATIVE_GAME_CLOCK_INVALID")
    result, server = bundle.json("run/result.json"), bundle.json("run/server/result.json")
    require(result.get("schema") == "strata/M0NativeGameResult/1" and result.get("status") == "pass"
            and result.get("logs_complete") is True and not result.get("forced_worker_cleanup")
            and not result.get("forced_server_cleanup")
            and all(result.get(name) == {"returncode": 0} for name in ("worker-preflight", "worker-driver", "server-driver")),
            "NATIVE_GAME_OUTER_STOP_UNCERTAIN")
    server_plan = bundle.json("run/server/plan.json")
    retention = inspect_stopped_components(bundle, retention, server, server_plan, result)
    require(server == result.get("server_result") and server.get("plan_digest") == digest(server_plan)
            and server.get("target") == "vanilla" and server.get("status") == "stopped_unqualified"
            and server.get("exit_code") == 0 and server.get("stop_sent") is True
            and server.get("forced_stop") is False and server.get("logs_complete") is True,
            "NATIVE_GAME_SERVER_STOP_UNCERTAIN")
    for name in ("stdout.log", "stderr.log"):
        health = inspect_server_log(bundle.path("run/server/" + name))
        require(health["result"] == "pass" and health == server["log_health"][name], "NATIVE_GAME_SERVER_LOG")
    for value in (result.get("elapsed_s"), server.get("elapsed_s"), server.get("started_unix"), intent.get("started_unix")):
        require(type(value) in (int, float) and math.isfinite(value) and value > 0, "NATIVE_GAME_CLOCK_INVALID")
    require(ended - started <= result["elapsed_s"] and server["elapsed_s"] <= result["elapsed_s"]
            and intent["started_unix"] <= server["started_unix"] <= started <= ended
            <= server["started_unix"] + server["elapsed_s"] + .25, "NATIVE_GAME_CLOCK_INVALID")
    # Cross-check old summaries, but all totals above came from independent inputs.
    expected = result.get("fixture_model_costs", {}).get("committed_and_reserved", {})
    require(all(expected.get(k) == model["totals"][k] for k in ("input_tokens", "output_tokens", "model_calls"))
            and expected.get("spend_microusd") == model["totals"]["amount"], "NATIVE_GAME_SUMMARY_CONFLICT")
    bundle.verify()
    return {"schema": "strata/NativeGameEvidenceReport/1", "policy": POLICY, "visibility": "evaluator",
            "reconciliation": "pass", "seal_sha256": plan.seal_sha256,
            "custody": custody,
            **{k: getattr(plan, k) for k in (*SCOPE, "job_id")},
            "evidence_kind": "authentic_game_with_scripted_inference", "model": model, "game": game,
            "stop": stop | {"server": "stopped_unqualified"}, "pins": pins, "saved_player": saved,
            "retention": retention,
            "clocks": {"native_observed_wall_s": ended - started,
                       "native_wall_basis": "recorded_unix_lifecycle_difference",
                       "outer_observed_wall_s": result["elapsed_s"], "server_observed_wall_s": server["elapsed_s"],
                       "broker_call_elapsed_ns_sum": sum(c["elapsed_ns"] for c in tools),
                       "provider_request_wall_ms_sum": model["totals"]["request_wall_ms"],
                       "overlapping_intervals_are_not_added": True,
                       "server_ticks": None, "avatar_ticks": None, "active_wall_s": None,
                       "server_tps": None, "server_mspt": None, "worker_event_loop_lag": None},
            "scoring_eligible": False, "production_qualified": False, "G0": "fail",
            "complete_project_accounting": False,
            "gaps": ["authentic_model_reasoning_and_reply_qualification", "full_runtime_and_helper_isolation",
                     "qualified_pack_and_role_locks", "authoritative_scorer_setup_and_controls",
                     "authoritative_server_avatar_ticks_and_active_intervals", "performance_and_resource_series",
                     "external_runtime_dependency_bytes_not_archived",
                     *([] if game["request_preimages_complete"] else ["broker_game_request_preimages_not_recorded"]),
                     *([] if pins["dependency_lock_and_schema_bytes_verified"]
                       else ["worker_dependency_lock_and_schema_bytes_not_archived"]),
                     *([] if game["primitive_trace_verified"] else ["per_primitive_worker_event_trace_not_recorded"]),
                     "shutdown_deadline_measurement",
                     "complete_joint_game_agent_checkpoint_and_recovery"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    reject_links(args.plan)
    require(args.plan.stat().st_size <= 65536, "EVIDENCE_INPUT_SIZE")
    plan = NativeGameEvidencePlan.model_validate(strict_json(args.plan.read_bytes()))
    output = args.output.absolute()
    reject_links(output)
    require(not output.exists() and not output.is_relative_to(Path(plan.bundle).absolute())
            and not output.is_relative_to(Path(__file__).resolve().parents[3]), "EVIDENCE_OUTPUT_PRIVATE")
    report = inspect_native_game(plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(canonical({"schema": "strata/ReportArtifact/1", "content_digest": digest(report), "report": report}) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"reconciliation": report["reconciliation"], "G0": report["G0"], "digest": digest(report)}))


if __name__ == "__main__":
    main()
