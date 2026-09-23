"""D14 development piloting, explicitly without an isolation qualification.

This admission does not bypass accounting, settle unknown usage, authorize a
retained-hold exception, or grant campaign/scoring qualification.
"""

import json
import time

from .native_broker_policy import validate_broker_settings
from .native_gateway import GatewayConfig, require_gateway
from .native_ingress import provider_binding
from .native_oauth import HOST, NATIVE_HEADERS, PATHS, POLICY
from .native_skills import INSTRUCTIONS
from .storage import Principal, canonical, digest, require

PURPOSE = "development_piloting"
SCHEMA = "strata/NativePilotPermit/1"
MAX_REQUESTS = 6
MAX_SPEND = 1_000_000
PRECHECKS = {"scoped_native_tools", "all_request_reservations", "finite_exposure", "verified_tls"}
GAME_CONTRACT_PATH = "initial/game/contract.json"


def game_contract():
    """Public wire documentation only; no coordinates, targets or evaluator data."""
    from .broker import GameCall
    return canonical({"schema": "strata/PublicGameInstructions/1",
        "tool": "strata_broker.game", "arguments_schema": GameCall.model_json_schema(),
        "instructions": [
            "Wrap the RPC object in the tool's request field. The operation selector is method.",
            "Use schema=strata/GameRequest/1, a unique request_id, and the supplied campaign_id, agent_id and epoch.",
            "deadline_at is an absolute future UTC ISO timestamp, not a duration. Construct it immediately before calling.",
            "For capabilities and observe, action, target_request_id and after are explicitly null.",
            "An act request carries an ActionBatch in action; target_request_id and after stay null.",
            "Copy observation_id, state_revision as expected_state_revision, capability_digest and control_revision from a fresh observation.",
            "Set the batch seq to last_action_seq+1 (use 1 when null), and use the supplied lease_id and scope.",
            "Use the ActionBatch schema for the remaining required fields. Targets must come from permitted observations.",
            "Poll action_status with target_request_id equal to the batch request_id and action=null; never replay an uncertain action.",
            "Schema availability does not grant a capability. Respect the runtime capabilities and the pilot's action limits."
        ]}).decode()


def prompt(scope, lease_id):
    require(set(scope) == {"campaign_id", "agent_id", "epoch"} and
            isinstance(lease_id, str) and 0 < len(lease_id) <= 128, "PILOT_SCOPE")
    return (
        "Pilot this Minecraft avatar using the scoped game tool. First read " + GAME_CONTRACT_PATH +
        " through strata_broker.artifact_read; it documents the exact request envelope and action schema. "
        "Do not guess argument names. Inspect capabilities and a fresh "
        "observation first. Choose a visible nearby landmark, turn toward it, then walk one to two "
        "blocks toward it on safe observed ground and stop. Use look_at and move_to only. Choose "
        "the target coordinates yourself from observations; do not invent hidden terrain. If no safe "
        "move is available, stop and explain. No helpers. At most two act calls. Each action must "
        "have a deadline and duration no greater than 2000 ms, and release_at_end=true. Use fresh "
        "observation IDs, revisions, capability digest and next sequence for each ActionBatch. "
        "Poll action_status for an accepted/executing action; never replay an uncertain action. "
        "Observe after each action and report the actual position and orientation changes, including "
        "failures. Finish promptly; the trial allows at most six model requests and 90 seconds. "
        "The public game scope is " + canonical(scope).decode() + "; lease_id=" + json.dumps(lease_id) + "."
    )


def require_profile(plan, config, lease_id):
    scope = {k: getattr(plan, k) for k in ("campaign_id", "agent_id", "epoch")}
    require(plan.purpose == PURPOSE and plan.role == "executor" and plan.depth == 0 and
            plan.parent_job_id is None and plan.helper_limit == 0 and plan.prompt == prompt(scope, lease_id) and
            plan.budget_mode == "per_dispatch" and plan.auth_mode == "chatgpt_oauth" and
            plan.provider == "openai" and plan.model == "gpt-5.6-luna" and plan.hard_timeout_s <= 90 and
            plan.bootstrap_digest is not None and plan.ingress_policy is not None and
            plan.config_overrides.get("developer_instructions") == INSTRUCTIONS and
            config.max_requests == MAX_REQUESTS and config.max_handlers == 1 and
            config.helper_calls_bound == 1 and config.skill_corpus_ref is not None and
            config.authorization_id is not None and config.job_id == plan.job_id and
            config.profile_digest == plan.profile_digest() and
            config.profile_fingerprint() == plan.gateway_config_digest, "PILOT_SCOPE")
    validate_broker_settings(plan.config_overrides)
    require(provider_binding(plan)["native_oauth"], "PILOT_SCOPE")
    from .launch_integrity import read_manifest, safe
    from .broker_stdio import WorkerTransport
    manifest = read_manifest(plan.bootstrap_manifest, plan.bootstrap_digest)
    require(manifest["schema"] == "strata/NativeBootstrap/2", "NATIVE_COMPANION_PINS_REQUIRED")
    broker = json.loads(safe(manifest["broker_config"]).read_bytes())
    require(isinstance(broker.get("worker_grant"), str), "PILOT_GAME_REQUIRED")
    descriptor = json.loads(safe(broker["worker_grant"]).read_bytes())
    WorkerTransport(descriptor)
    require(all(descriptor[k] == v for k, v in scope.items()), "PILOT_SCOPE")


def validate_permit(gate, proof, plan, config, *, account_digest):
    require(not gate.simulation, "OAUTH_LIVE_STORE_REQUIRED")
    require_profile(plan, config, proof.get("lease_id"))
    require(proof.get("schema") == SCHEMA and proof.get("is_example") is False and
            proof.get("purpose") == PURPOSE and proof.get("scope_decision") == "D14" and
            proof.get("production_qualified") is False and proof.get("isolation_qualified") is False and
            proof.get("policy") == POLICY and proof.get("job_id") == plan.job_id and
            proof.get("profile_digest") == plan.profile_digest() and
            proof.get("account_digest") == account_digest and proof.get("host") == HOST and
            proof.get("paths") == PATHS and proof.get("native_headers") == sorted(NATIVE_HEADERS) and
            proof.get("gateway_config_digest") == plan.gateway_config_digest and
            proof.get("authorization_id") == config.authorization_id and
            type(proof.get("expires_unix")) in {float, int} and
            time.time() < proof["expires_unix"] <= time.time() + 600 and
            proof.get("max_requests") == MAX_REQUESTS and proof.get("maximum_microusd") == MAX_SPEND and
            isinstance(proof.get("prechecks"), dict) and set(proof["prechecks"]) == PRECHECKS,
            "PILOT_UNADMITTED")
    policy = gate.authorizations.check(config.authorization_id, plan.account,
                                      plan.provider, plan.auth_mode, plan.model)
    require(proof.get("authorization_digest") == digest(policy.model_dump()) and
            proof.get("basis_digest") == plan.accounting_basis_digest == policy.accounting_basis.fingerprint()
            and config.exposure.amount(policy.accounting_basis) <= MAX_SPEND <= policy.first_trial_max_microusd,
            "PILOT_ALLOWANCE")
    for check, ref in proof["prechecks"].items():
        item = json.loads(gate._private_ref(ref, 1024 * 1024))
        require(item.get("schema") == "strata/NativePreDispatchEvidence/1" and
                item.get("check") == check and item.get("result") == "pass" and
                item.get("is_example") is False and item.get("profile_digest") == plan.profile_digest() and
                item.get("scope") == PURPOSE and isinstance(item.get("evidence_refs"), list) and
                bool(item["evidence_refs"]), "PILOT_EVIDENCE")
        for source in item["evidence_refs"]:
            gate._private_ref(source, 4 * 1024 * 1024)
    return policy


def validate_runtime_admission(runtime, proof, plan):
    require(proof.get("schema") == "strata/NativePilotAdmission/1" and
            proof.get("is_example") is False and proof.get("scope_decision") == "D14" and
            proof.get("isolation_qualified") is False and proof.get("production_qualified") is False and
            proof.get("profile_digest") == plan.profile_digest(), "PILOT_UNADMITTED")
    config = GatewayConfig.model_validate_json(require_gateway(runtime.db.connection, plan, "OPEN")["config"])
    require(proof.get("permit_ref") == config.transport_qualification_ref, "PILOT_UNADMITTED")
    from .inference_dispatch import InferenceDispatches
    gate = InferenceDispatches(runtime.db, runtime.cas, authorization_id=runtime.authorization_id)
    permit = runtime.cas.json(Principal("operator", "operator"), "operator", proof["permit_ref"])
    validate_permit(gate, permit, plan, config, account_digest=proof.get("account_digest"))


def require_permit_for_request(gate, proof, credentials, attempt, reserve):
    from .native import NativeLaunch
    row = gate.db.connection.execute("SELECT plan FROM native_jobs WHERE id=?", (credentials.job,)).fetchone()
    require(row is not None, "PILOT_UNADMITTED")
    plan = NativeLaunch.model_validate_json(row[0])
    config = GatewayConfig.model_validate_json(require_gateway(gate.db.connection, plan, "OPEN")["config"])
    validate_permit(gate, proof, plan, config, account_digest=credentials.account_digest)
    require(credentials.path == "/v1/responses" and reserve.parent_operation_id == plan.operation_id and
            reserve.kind == "model" and reserve.campaign_account == "development" and
            attempt.runtime_job_id == plan.job_id, "PILOT_UNADMITTED")
    requests = list(gate.db.connection.execute("SELECT operation FROM native_gateway_requests WHERE job=?",
                                              (plan.job_id,)))
    require(1 <= len(requests) <= MAX_REQUESTS and
            any(row[0] == reserve.operation_id for row in requests), "PILOT_REQUEST_LIMIT")


def require_bounded_game_request(db, runtime_id, request):
    """Within the broker's forwarding transaction, before any game side effect."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='native_jobs'").fetchone():
        return  # Legacy synthetic broker fixtures have no native job.
    row = db.execute("SELECT plan FROM native_jobs WHERE id=?", (runtime_id,)).fetchone()
    if row is None or json.loads(row[0]).get("purpose") != PURPOSE:
        return
    require(request.method in {"capabilities", "observe", "act", "action_status", "cancel", "stop_all"},
            "PILOT_GAME_METHOD")
    if request.method != "act":
        return
    action = request.action
    require(action is not None and action.mode == "structured" and not action.events and
            action.release_at_end and action.duration_ms <= 2000 and
            action.action.kind in {"look_at", "move_to"}, "PILOT_ACTION_SCOPE")
    from datetime import datetime
    deadline = datetime.fromisoformat(action.deadline_at.replace("Z", "+00:00")).timestamp()
    require(deadline <= time.time() + 2.25, "PILOT_ACTION_SCOPE")
    used = db.execute("SELECT count(*) FROM broker_game_requests WHERE runtime=? AND "
                      "json_extract(body,'$.method')='act'", (runtime_id,)).fetchone()[0]
    require(used < 2, "PILOT_ACTION_LIMIT")
