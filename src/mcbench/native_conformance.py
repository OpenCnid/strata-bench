"""One-call OAuth receipt qualification, never campaign admission.

Pre-dispatch native boundary/accounting evidence remains mandatory. The receipt
being tested is an outcome, not an invented prerequisite or a production pass.
"""

import hashlib
import json
import time

from .authorization import Authorizations
from .native import NativeLaunch
from .native_broker_policy import validate_broker_settings
from .native_gateway import GatewayConfig, require_gateway
from .native_ingress import provider_binding
from .native_oauth import HOST, NATIVE_HEADERS, PATHS, POLICY
from .native_skills import INSTRUCTIONS
from .storage import canonical, digest, require

SCHEMA = "strata/NativeOAuthConformancePermit/1"
PROMPT = "Reply with exactly STRATA_OAUTH_RECEIPT_OK. Do not call any tools or helpers."
PRECHECKS = {"native_tool_boundary", "all_request_reservations", "credential_containment",
             "finite_exposure", "verified_tls"}


def require_receipt_profile(plan, config):
    require(plan.purpose == "conformance" and plan.role == "executor" and plan.depth == 0 and
            plan.parent_job_id is None and plan.helper_limit == 0 and plan.prompt == PROMPT and
            plan.budget_mode == "per_dispatch" and plan.auth_mode == "chatgpt_oauth" and
            plan.model == "gpt-5.6-luna" and plan.hard_timeout_s <= 120 and
            plan.bootstrap_digest is not None and plan.ingress_policy is not None and
            plan.config_overrides.get("developer_instructions") == INSTRUCTIONS and
            config.max_requests == 1 and config.max_handlers == 1 and
            config.helper_calls_bound == 1 and config.skill_corpus_ref is not None and
            config.authorization_id is not None and config.job_id == plan.job_id and
            config.profile_digest == plan.profile_digest() and
            config.profile_fingerprint() == plan.gateway_config_digest, "RECEIPT_CONFORMANCE_SCOPE")
    validate_broker_settings(plan.config_overrides)
    binding = provider_binding(plan)
    require(binding["native_oauth"], "RECEIPT_CONFORMANCE_SCOPE")
    # The frozen broker has no game grant; this is not a gameplay trial.
    from .launch_integrity import read_manifest, safe
    manifest = read_manifest(plan.bootstrap_manifest, plan.bootstrap_digest)
    broker = json.loads(safe(manifest["broker_config"]).read_bytes())
    require(broker.get("worker_grant") is None, "RECEIPT_GAME_FORBIDDEN")


def validate_permit(gate, proof, plan, config, *, account_digest):
    require(not gate.simulation, "OAUTH_LIVE_STORE_REQUIRED")
    require_receipt_profile(plan, config)
    require(proof.get("schema") == SCHEMA and proof.get("is_example") is False and
            proof.get("purpose") == "first_receipt_conformance" and
            proof.get("production_qualified") is False and proof.get("policy") == POLICY and
            proof.get("job_id") == plan.job_id and proof.get("profile_digest") == plan.profile_digest() and
            proof.get("account_digest") == account_digest and proof.get("host") == HOST and
            proof.get("paths") == PATHS and proof.get("native_headers") == sorted(NATIVE_HEADERS) and
            proof.get("gateway_config_digest") == plan.gateway_config_digest and
            proof.get("authorization_id") == config.authorization_id and
            type(proof.get("expires_unix")) in {float, int} and
            time.time() < proof["expires_unix"] <= time.time() + 600 and
            proof.get("max_requests") == 1 and isinstance(proof.get("prechecks"), dict) and
            set(proof["prechecks"]) == PRECHECKS, "OAUTH_CONFORMANCE_UNADMITTED")
    policy = gate.authorizations.check(config.authorization_id, plan.account,
                                      plan.provider, plan.auth_mode, plan.model)
    require(proof.get("authorization_digest") == digest(policy.model_dump()) and
            proof.get("basis_digest") == plan.accounting_basis_digest == policy.accounting_basis.fingerprint()
            and proof.get("maximum_microusd") == config.exposure.amount(policy.accounting_basis)
            <= policy.first_trial_max_microusd, "OAUTH_CONFORMANCE_ALLOWANCE")
    for check, ref in proof["prechecks"].items():
        item = json.loads(gate._private_ref(ref, 1024 * 1024))
        require(item.get("schema") == "strata/NativePreDispatchEvidence/1" and
                item.get("check") == check and item.get("result") == "pass" and
                item.get("is_example") is False and item.get("profile_digest") == plan.profile_digest() and
                item.get("scope") == "first_receipt_conformance" and
                isinstance(item.get("evidence_refs"), list) and bool(item["evidence_refs"]),
                "OAUTH_CONFORMANCE_EVIDENCE")
        for source in item["evidence_refs"]:
            gate._private_ref(source, 4 * 1024 * 1024)
    return policy


def require_permit_for_request(gate, proof, credentials, attempt, reserve):
    row = gate.db.connection.execute("SELECT plan FROM native_jobs WHERE id=?",
                                     (credentials.job,)).fetchone()
    require(row is not None, "OAUTH_CONFORMANCE_UNADMITTED")
    plan = NativeLaunch.model_validate_json(row[0])
    gateway = require_gateway(gate.db.connection, plan, "OPEN")
    config = GatewayConfig.model_validate_json(gateway["config"])
    validate_permit(gate, proof, plan, config, account_digest=credentials.account_digest)
    require(credentials.path == "/v1/responses" and reserve.parent_operation_id == plan.operation_id and
            reserve.kind == "model" and reserve.campaign_account == "development" and
            attempt.runtime_job_id == plan.job_id, "OAUTH_CONFORMANCE_UNADMITTED")
    requests = list(gate.db.connection.execute("SELECT operation FROM native_gateway_requests WHERE job=?",
                                              (plan.job_id,)))
    require(len(requests) == 1 and requests[0][0] == reserve.operation_id,
            "OAUTH_CONFORMANCE_REQUEST_LIMIT")
    previous = gate.db.connection.execute("SELECT operation FROM inference_attempts WHERE "
        "json_extract(request,'$.runtime_job_id')=?", (plan.job_id,)).fetchall()
    require(not previous, "OAUTH_CONFORMANCE_ALREADY_DISPATCHED")


def tls_probe():
    """Verify the fixed peer with no auth, HTTP request or model dispatch."""
    import socket
    import ssl
    context = ssl.create_default_context()
    with socket.create_connection((HOST, 443), timeout=10) as raw:
        with context.wrap_socket(raw, server_hostname=HOST) as secure:
            return {"schema": "strata/FixedTLSObservation/1", "is_example": False,
                    "host": HOST, "port": 443, "certificate_validation": "system_trust_and_hostname",
                    "protocol": secure.version(), "cipher": secure.cipher()[0],
                    "certificate_sha256": hashlib.sha256(secure.getpeercert(binary_form=True)).hexdigest(),
                    "observed_unix": time.time(), "http_requests": 0, "credentials_sent": False}


def record_outcome(gate, plan, seal_ref):
    """Report actual attempts/valuations without granting campaign qualification."""
    calls = [dict(r) for r in gate.db.connection.execute(
        "SELECT operation,state,reason,receipt_digest FROM inference_attempts WHERE "
        "json_extract(request,'$.runtime_job_id')=?", (plan.job_id,))]
    valuations = [json.loads(r[0]) for r in gate.db.connection.execute(
        "SELECT v.body FROM inference_valuations v JOIN inference_attempts a ON a.operation=v.operation "
        "WHERE json_extract(a.request,'$.runtime_job_id')=?", (plan.job_id,))]
    result = {"schema": "strata/NativeOAuthConformanceResult/1", "is_example": False,
        "job_id": plan.job_id, "profile_digest": plan.profile_digest(), "production_qualified": False,
        "receipt_result": "pass" if len(calls) == len(valuations) == 1 and calls[0]["state"] == "SETTLED"
            else "fail", "attempts": calls, "valuations": valuations, "seal_ref": seal_ref,
        "authorization": Authorizations(gate.db).status(gate.authorization_id)}
    from .storage import Principal
    return gate.cas.put(Principal("operator", "operator"), "operator", "operator", canonical(result)), result
