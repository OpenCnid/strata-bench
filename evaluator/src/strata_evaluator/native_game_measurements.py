"""Read an externally sealed instrumented native pilot without launching it."""

from mcbench.inventory import file_hash
from mcbench.native_export import inspect_native_source
from mcbench.native_game_measurements import inspect_measurements
from mcbench.storage import digest, require

from .evidence_bundle import EvidenceCAS
from .native_game_evidence import model_usage


def _inspect_recorded_measurements(bundle):
    intent = bundle.json("run/intent.json")
    plan = intent["plan"]
    require(plan["schema"] == "strata/M0NativePilot/2" and intent["model_provider"] == "native_oauth"
            and intent["isolation_qualified"] is False, "NATIVE_MEASUREMENT_PROFILE")
    server_plan = bundle.json("run/server-plan.json")
    require(server_plan["clock"] == plan["clock"] and server_plan["base"]["pack"] == plan["pack"],
            "NATIVE_MEASUREMENT_PROFILE")
    require(file_hash(bundle.path("run/worker-runtime.json")) == plan["worker_runtime"]["sha256"],
            "NATIVE_MEASUREMENT_PROFILE")
    config = bundle.json("run/worker-config.json")
    require(all(config[k] == plan["worker_invocation"][k] for k in ("campaign_id", "agent_id", "epoch")),
            "NATIVE_MEASUREMENT_SCOPE")
    result = bundle.json("run/result.json")
    server = bundle.json("run/server/result.json")
    require(result["server_result"] == server and result["status"] in {"pass", "fail"}
            and type(result["native_worker_journal_join"]) is bool, "NATIVE_MEASUREMENT_STOP")
    with bundle.database("run/worker/actions.sqlite") as db:
        report = inspect_measurements(bundle.path("run/result.json").parent, server_plan, config,
            server, result["worker_health"], plan["pilot"]["job_id"], db)
    require(report == result["measurements"], "NATIVE_MEASUREMENT_CHANGED")
    bundle.verify()
    return {"schema": "strata/SealedNativeGameMeasurements/1", "seal_sha256": bundle.seal_sha256,
            "intent_digest": digest(intent), "measurements": report,
            "model_costs_reconciled": False, "G0": "fail"}


def inspect_native_measurements(bundle):
    result = bundle.json("run/result.json")
    require(result["status"] == "pass" and result["native_worker_journal_join"] is True,
            "NATIVE_MEASUREMENT_STOP")
    return _inspect_recorded_measurements(bundle)


def _join_completed_costs(bundle, measured):
    """Join independently reconstructed measurements to actual distinct costs.

    The archive must include scoped broker workspace CAS bytes as well as model
    receipts. Missing private inputs are errors, never inferred zero costs.
    """
    plan = bundle.json("run/intent.json")["plan"]
    scope = measured["measurements"]
    with bundle.database("controller.sqlite") as db:
        cas = EvidenceCAS(db, bundle, "objects")
        native, source, _ = inspect_native_source(db, cas, plan["pilot"]["job_id"], simulation=False)
        require(all(getattr(native, k) == scope[k] for k in ("campaign_id", "agent_id", "epoch"))
                and native.job_id == scope["run_id"] and source["returncode"] == 0,
                "NATIVE_MEASUREMENT_SCOPE")
        costs = model_usage(db, cas, native, source, simulation=False)
        result = bundle.json("run/native/result.json")
        require(result["is_example"] is False and result["model_evidence"] == "actual_native_oauth"
                and result["job_id"] == native.job_id and result["profile_digest"] == native.profile_digest()
                and len(result["attempts"]) == costs["real_model_requests"]
                and isinstance(result["checks"], dict) and result["checks"].get("native_completed") is True
                and all(type(v) is bool for v in result["checks"].values())
                and sorted(result["valuations"], key=lambda v: v["raw_usage_ref"]) ==
                    sorted((a["valuation"] for a in source["attempts"]), key=lambda v: v["raw_usage_ref"]),
                "NATIVE_MEASUREMENT_COSTS")
        tools = source["broker_calls"]
        require(all(type(c["elapsed_ns"]) is int and c["elapsed_ns"] >= 0 for c in tools),
                "NATIVE_MEASUREMENT_COSTS")
        tool_costs = {"basis": "recorded-monotonic-broker-call-duration", "calls": tools,
                     "sum_call_ns": sum(c["elapsed_ns"] for c in tools),
                     "overlapping_calls_are_not_wall_time": True}
    bundle.verify()
    return measured | {"schema": "strata/InstrumentedNativePilotEvidence/1", "model_costs_reconciled": True,
        "model": costs, "tool_execution": tool_costs, "native_source_digest": digest(source),
        "native_profile_digest": native.profile_digest(), "scientific_qualified": False,
        "complete_G0_qualification": False}


def inspect_instrumented_pilot(bundle):
    """Preserve the strict successful-pilot admission contract."""
    measured = inspect_native_measurements(bundle)
    report = _join_completed_costs(bundle, measured)
    require(all(v is True for v in bundle.json("run/native/result.json")["checks"].values()),
            "NATIVE_MEASUREMENT_COSTS")
    return report


def inspect_completed_pilot_costs(bundle):
    """Reconstruct normal-completion costs even when the recorded goal failed.

    A settled native job and complete stopped measurements are still required.
    Gameplay checks and the action join are retained as recorded outcomes, not
    independently certified here. Unknown usage and incomplete stops still fail.
    """
    report = _join_completed_costs(bundle, _inspect_recorded_measurements(bundle))
    result = bundle.json("run/result.json")
    native = bundle.json("run/native/result.json")
    return report | {"schema": "strata/CompletedNativePilotCosts/1",
        "outcome": {"run_status": result["status"], "native_checks": native["checks"],
            "worker_action_join_recorded": result["native_worker_journal_join"],
            "run_result_digest": digest(result), "native_result_digest": digest(native)},
        "gameplay_success_qualified": False, "action_effects_reconciled": False}
