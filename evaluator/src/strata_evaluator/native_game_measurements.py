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


def inspect_reconciled_pilot(bundle):
    """Join known action outcomes, saved state, locks and settled measured costs.

    Requires the explicit refusal policy. Legacy absence of refusal evidence,
    ambiguous effects and incomplete acknowledgments cannot qualify this join.
    The original two-action goal result remains an independently recorded value.
    """
    from .native_game_evidence import (saved_player_evidence, sealed_pack_evidence, source_evidence,
                                       stop_evidence, worker_evidence)
    report = inspect_completed_pilot_costs(bundle)
    intent = bundle.json("run/intent.json")
    result = bundle.json("run/result.json")
    config = bundle.json("run/worker-config.json")
    # The producer writes forced-cleanup fields only when cleanup was forced.
    # Missing means no reported force; owned-process/stop proofs below remain required.
    require(result.get("logs_complete") is True and result.get("forced_worker_cleanup", False) is False
            and result.get("forced_server_cleanup", False) is False, "NATIVE_MEASUREMENT_STOP")
    with bundle.database("controller.sqlite") as db, bundle.database("run/worker/actions.sqlite") as worker:
        native, source, _ = inspect_native_source(db, EvidenceCAS(db, bundle, "objects"),
                                                intent["plan"]["pilot"]["job_id"], simulation=False)
        require(digest(source) == report["native_source_digest"]
                and native.profile_digest() == report["native_profile_digest"], "NATIVE_MEASUREMENT_CHANGED")
        game, cap, observations = worker_evidence(worker, source, native, config, allow_recorded_refusals=True)
        stop = stop_evidence(db, bundle, native, native, select_job=True)
        pins = source_evidence(bundle, native, intent, cap)
        from mcbench.native_game_retention import GameRetention
        retention = GameRetention({"path": str(bundle.path("run/retention-input.json")),
                                   "sha256": intent["plan"]["retention_source"]["sha256"]})
        retention.check_worker_binding(intent["plan"]["worker_runtime"],
            bundle.files["run/source/backends/mineflayer/dist/src/worker.js"].sha256, capability_digest=cap["digest"])
        saved = saved_player_evidence(bundle, observations)
        player_path = f"run/server/stopped-instance/state/world/playerdata/{report['measurements']['saved_player_uuid']}.dat"
        require(file_hash(bundle.path(player_path)) == report["measurements"]["saved_player_sha256"],
                "NATIVE_GAME_SAVED_PLAYER")
        pack = sealed_pack_evidence(bundle, intent, result, config, bundle.json("run/server-plan.json"),
                                    bundle.json("run/server/result.json"))
    bundle.verify()
    return report | {"schema": "strata/ReconciledNativePilot/1", "action_evidence_reconciled": True,
        "declared_worker_identity_matches": True,
        "game": game, "saved_player": saved, "stop": stop, "locks": pins, "pack": pack}


def main(argv=None):
    import argparse
    import json
    from pathlib import Path
    from .cli import write_report
    from .evidence_bundle import EvidenceBundle
    parser = argparse.ArgumentParser(description="Reconcile a sealed private instrumented pilot; no launch or inference.")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--seal", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    require(not args.output.resolve().is_relative_to(args.bundle.resolve()), "EVIDENCE_READ_ONLY")
    report = inspect_reconciled_pilot(EvidenceBundle(args.bundle, args.seal))
    receipt = write_report(args.output, report)
    print(json.dumps({"status": "reconciled", "visibility": "evaluator", "G0": "fail", **receipt}))


if __name__ == "__main__":
    main()
