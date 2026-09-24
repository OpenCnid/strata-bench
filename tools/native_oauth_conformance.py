"""Operator-only one-call native OAuth receipt qualification in the original store.

Uses a fresh private profile and exact current native canary evidence. No game
grant, helper, scientific sample, new allowance, automatic retry or promotion.
Credentials never enter result files, prompts, command lines or printed output.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time

from mcbench.accounting import EstimateBasis, FiniteExposure
from mcbench.authorization import Authorizations
from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceDispatches
from mcbench.inventory import file_hash
from mcbench.native import CODEX_VERSION, DOVETAIL_COMMIT, CONFORMANCE_PREREQUISITES, NativeExec, NativeLaunch
from mcbench.native_bootstrap import acquire_native_bootstrap, prepare_bundle
from mcbench.native_conformance import PROMPT, SCHEMA, record_outcome, require_receipt_profile, tls_probe
from mcbench.native_gateway import GatewayConfig, NativeGateway
from mcbench.native_ingress import HEADER, POLICY as INGRESS_POLICY, credential
from mcbench.native_oauth import HOST, NATIVE_HEADERS, PATHS, POLICY as OAUTH_POLICY
from mcbench.native_skills import INSTRUCTIONS, prepare_skill_corpus
from mcbench.plugins import CODEX_BINARY_SHA256, install_dovetail
from mcbench.storage import CAS, Database, Fault, Principal, canonical, digest, reject_links, require, safe_relative
from native_dispatch_probe import ledger, put, wait_job

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = Principal("operator", "operator")


def normalized_config(plan):
    """Declared relocation only. No feature/tool/timeout/approval key is omitted."""
    from mcbench.native_broker_policy import validate_broker_settings
    from mcbench.native_ingress import provider_binding
    validate_broker_settings(plan.config_overrides)
    provider_binding(plan)
    lease = acquire_native_bootstrap(plan)
    lease.close()
    config = json.loads(json.dumps(plan.config_overrides))
    if "model_catalog_json" in config:
        # Relocate only identical, sealed catalog bytes; never normalize away a
        # model/tool metadata change.
        config["model_catalog_json"] = {"sealed_sha256": file_hash(Path(config["model_catalog_json"]))}
    prefix = "model_providers." + config["model_provider"] + "."
    config[prefix + "base_url"] = "<owned-literal-loopback>/v1"
    config[prefix + "http_headers"] = {HEADER: "<per-job-capability>"}
    server = config["mcp_servers.strata_broker"]
    server["command"] = "<sealed-python>"
    server["args"] = ["-I", "-S", "-B", "<pinned-bootstrap>", "--manifest", "<manifest>",
                       "--sha256", "<manifest-digest>"]
    def normalize(value):
        if isinstance(value, dict):
            return {k: normalize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [normalize(v) for v in value]
        if isinstance(value, str):
            text = value.replace("\\", "/").removeprefix("//?/")
            base = plan.profile_directory.replace("\\", "/").removeprefix("//?/")
            if text.startswith(base + "/"):
                return "<private-profile>" + text[len(base):]
        return value
    return normalize(config)


def inspect_preflight(directory, plan, cas, *, piloting=False):
    directory = directory.resolve()
    result = json.loads((directory / "result.json").read_bytes())
    manifest = json.loads((directory / "manifest.json").read_bytes())
    required = {"root_and_helper_exact_skill_read", "gateway_all_requests_settled_and_fenced",
                "native_oauth_headers_all_requests", "oauth_secrets_absent_from_context_and_journal",
                "exact_root_helper_tool_catalogs", "no_unauthorized_loopback", "private_file_not_in_requests",
                "ancestor_instructions_not_in_requests", "direct_shell_dispatch_denied"}
    if piloting:
        required = {"public_contract_read", "malformed_calls_rejected", "deadline_window_rejected", "valid_observation_forwarded_once",
                    "gateway_all_requests_settled_and_fenced", "native_oauth_headers_all_requests",
                    "oauth_secrets_absent_from_context_and_journal", "every_request_projection_checked",
                    "native_completed", "zero_helpers", "three_settled_fixture_requests", "observation_page_forwarded"}
        require(result.get("scope") == "development_piloting_public_contract" and
                result.get("isolation_qualified") is False, "PREFLIGHT_SCOPE_MISMATCH")
    require(result.get("is_example") is True and result.get("production_qualified") is False and
            required <= set(result.get("checks", {})) and all(result["checks"].values()) and
            result.get("closure", {}).get("state") == "FINALIZED" and
            manifest.get("binary_sha256") == plan.binary_digest == CODEX_BINARY_SHA256,
            "PREFLIGHT_INCOMPLETE")
    require({"src/mcbench/native_conformance.py", "tools/native_oauth_conformance.py"} <=
            set(manifest["source_sha256"]), "PREFLIGHT_SOURCE_UNPINNED")
    if piloting:
        require({"src/mcbench/native_piloting.py", "src/mcbench/pilot_budget.py", "tools/native_pilot_trial.py",
                 "tools/native_pilot_report.py", "tools/native_pilot_contract_probe.py", "tools/m0_native_game.py"} <=
                set(manifest["source_sha256"]), "PREFLIGHT_SOURCE_UNPINNED")
    for path, sha in manifest["source_sha256"].items():
        require(file_hash(ROOT / safe_relative(path)) == sha, "PREFLIGHT_SOURCE_CHANGED")
    db = sqlite3.connect("file:" + (directory / "synthetic.sqlite").as_posix() + "?mode=ro", uri=True)
    try:
        source = NativeLaunch.model_validate_json(db.execute("SELECT plan FROM native_jobs WHERE id='root'").fetchone()[0])
        require(db.execute("SELECT simulation FROM native_profile").fetchone()[0] == 1,
                "PREFLIGHT_STORE_MISMATCH")
    finally:
        db.close()
    from mcbench.native_tool_projection import read_tool_projection
    if piloting:
        require(source.purpose == "development_piloting" and source.helper_limit == 0,
                "PREFLIGHT_SCOPE_MISMATCH")
    require(result.get("tool_projection", {}).get("expected") == {
        role: digest(blocks) for role, blocks in read_tool_projection(cas, plan).items()},
        "PREFLIGHT_TOOL_PROJECTION_MISMATCH")
    require(source.profile_digest() == result["profile_digest"] and
            normalized_config(source) == normalized_config(plan) and
            all(getattr(source, k) == getattr(plan, k) for k in (
                "binary_digest", "binary_version", "dovetail_commit", "model", "budget_mode", "auth_mode",
                "session_storage", "broker_policy", "ingress_policy", "hard_timeout_s", "output_limit_bytes",
                "tool_catalog_policy"))
            and source.environment["PATH"] == plan.environment["PATH"] and
            set(source.environment) == set(plan.environment) == {"PATH", "TEMP", "TMP"},
            "PREFLIGHT_PROFILE_MISMATCH")
    # Replay transfer is explicitly scoped: equivalent relocated native/tool
    # software, with helper/game privileges removed for one receipt request.
    return {"schema": "strata/NativePreflightTransfer/1", "is_example": False,
            "native_execution": "actual_pinned_cli", "provider": "synthetic_fixture",
            "source_profile_digest": source.profile_digest(), "target_profile_digest": plan.profile_digest(),
            "config_contract_digest": digest(normalized_config(plan)),
            "source_manifest": manifest, "observed_result": result,
            "scope": "development_piloting" if piloting else "first_receipt_conformance", "full_T06_qualified": False,
            "declared_changes": ["fresh private paths and transport capability", "helper limit reduced to zero",
                                 "scoped real worker grant" if piloting else "worker grant removed",
                                 "provider changes from fixture to fixed OpenAI TLS"]}


def run(args):
    return run_native_trial(args)


def run_native_trial(args, *, pilot=None):
    """Shared native lifecycle. The separate M0 driver supplies a real worker.

    Ordinary accounting admission remains required, except explicit D15/D16 pilots.
    The one-use D12 branch remains receipt-only.
    """
    from mcbench import native_piloting
    require(pilot is None or getattr(args, "metering_trial", None) is None, "PILOT_D12_FORBIDDEN")
    output = args.output.resolve()
    require(not output.exists() and not output.is_relative_to(ROOT), "PRIVATE_FRESH_OUTPUT_REQUIRED")
    require(args.database.is_file() and args.objects.is_dir(), "ORIGINAL_ACCOUNTING_REQUIRED")
    require(os.name == "nt" and file_hash(args.codex) == CODEX_BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    require(args.catalog is not None and args.tool_projections is not None,
            "REVIEWED_NATIVE_CATALOG_REQUIRED")
    for path in (args.database, args.objects, args.credentials, args.preflight,
                 args.catalog, args.tool_projections):
        reject_links(path)
        require(not path.resolve().is_relative_to(ROOT), "PRIVATE_PATH_REQUIRED")
    output.mkdir(parents=True)
    db = Database(args.database)
    cas = CAS(db, args.objects)
    auth = Authorizations(db)
    before = auth.status(args.authorization)
    require((before["authorization"]["schema"], before["authorization"]["decision_id"]) in {
                ("strata/ExecutionAuthorization/2", "D11"), ("strata/ExecutionAuthorization/3", "D17")} and
            db.connection.execute("SELECT 1 FROM authorization_migrations WHERE id=?",
                                  (args.authorization,)).fetchone(), "ORIGINAL_ACCOUNTING_REQUIRED")
    (output / "accounting-before.json").write_bytes(canonical(before))
    # One durable first-receipt job in this authority. A stopped or uncertain job
    # is inspected/reconciled explicitly; rerunning this script cannot replay it.
    trial = getattr(args, "metering_trial", None)
    if pilot and pilot.get("budget_decision") is not None:
        from mcbench.pilot_budget import check_decision
        check_decision(db.connection, pilot["budget_decision"])
    job = pilot["job_id"] if pilot else args.authorization + (
        ":oauth-receipt-d12" if trial == "D12" else ":oauth-first-receipt")
    if db.connection.execute("SELECT 1 FROM sqlite_master WHERE name='native_jobs'").fetchone():
        require(db.connection.execute("SELECT 1 FROM native_jobs WHERE id=?", (job,)).fetchone() is None,
                "FIRST_RECEIPT_ALREADY_ATTEMPTED")
    from mcbench.native_worker import NativeWorker
    worker = NativeWorker(db, pilot["descriptor"]) if pilot else None
    runtime = NativeExec(db, cas, authorization_id=args.authorization,
                         revoke_game=worker.revoke if worker else lambda *_: None)
    gate = InferenceDispatches(db, cas, authorization_id=args.authorization)
    gateway = NativeGateway(db.path, cas.root)
    plan = None
    seal = None
    try:
        profile, workspace, temporary = (output / n for n in ("profile", "workspace", "tmp"))
        workspace.mkdir()
        temporary.mkdir()
        installed = install_dovetail(args.codex, profile)
        commands = json.loads((profile / "installation-commands.json").read_bytes())
        installed_root = Path(json.loads(commands[-1]["stdout"])["installedPath"])
        source_db = sqlite3.connect("file:" + (args.preflight / "synthetic.sqlite").as_posix() + "?mode=ro", uri=True)
        try:
            previous = NativeLaunch.model_validate_json(source_db.execute(
                "SELECT plan FROM native_jobs WHERE id='root'").fetchone()[0])
        finally:
            source_db.close()
        config = previous.config_overrides | installed["required_config_overrides"]
        prefix = "model_providers." + config["model_provider"] + "."
        config[prefix + "base_url"] = gateway.base_url
        config[prefix + "http_headers"] = {HEADER: credential()}
        config[prefix + "requires_openai_auth"] = True
        config["developer_instructions"] = INSTRUCTIONS
        config["cli_auth_credentials_store"] = "file"
        require(args.catalog is not None and args.tool_projections is not None,
                "REVIEWED_NATIVE_CATALOG_REQUIRED")
        from mcbench.native_catalog import install_no_patch_catalog
        from mcbench.native_tool_projection import pin_tool_projection
        catalog = install_no_patch_catalog(args.catalog, profile / "model-catalog.json",
            expected_sha256=file_hash(args.catalog), model=previous.model)
        config.update(catalog["config_overrides"])
        if pilot:
            (output / "worker.json").write_bytes(canonical(pilot["descriptor"]))
        (output / "broker.json").write_bytes(canonical({"schema": "strata/SealedBrokerConfig/1",
            "database": str(db.path), "objects": str(cas.root), "runtime_id": job,
            "worker_grant": str(output / "worker.json") if pilot else None}))
        sealed = prepare_bundle(output / "broker-runtime", native_executable=args.codex,
            plugin_root=installed_root, broker_config=output / "broker.json", static_files=[
                profile / "config.toml", profile / "pinned-marketplace/.agents/plugins/marketplace.json",
                *map(Path, catalog["static_files"])])
        config["mcp_servers.strata_broker"] = sealed["server"]
        corpus_ref = prepare_skill_corpus(cas, installed_root)
        basis = EstimateBasis.model_validate(before["authorization"]["accounting_basis"])
        pricing = put(cas, basis.model_dump())
        exposure = FiniteExposure.model_validate({"schema": "strata/FiniteInferenceExposure/1",
            "basis_digest": basis.fingerprint(), "max_input_tokens": basis.context_window_tokens,
            "max_output_tokens": basis.max_output_tokens, "max_requests": 1,
            "input_bound_method": "provider_context_limit", "output_bound_method": "provider_model_limit",
            "enforcement_ref": "cas:sha256:" + "a" * 64})
        amount = exposure.amount(basis)
        job_amount = native_piloting.MAX_SPEND if pilot else amount
        calls = (pilot.get("budget_decision", {}).get("max_requests", native_piloting.MAX_REQUESTS)
                 if pilot else 1)
        require((before["budget"]["dispatch_allowed"] or trial == "D12" or
                 pilot and pilot.get("budget_decision") is not None) and
                amount <= job_amount <= before["authorization"]["first_trial_max_microusd"]
                and before["budget"]["committed_and_reserved"]["spend_microusd"] + job_amount
                    <= before["authorization"]["total_spend_microusd"], "ALLOWANCE_UNAVAILABLE")
        gateway_config = GatewayConfig.model_validate({"schema": "strata/NativeGatewayConfig/1",
            "job_id": job, "profile_digest": "a" * 64, "pricing_ref": pricing, "exposure": exposure,
            "transport_qualification_ref": None, "authorization_id": args.authorization,
            "max_requests": calls, "max_handlers": 1, "skill_corpus_ref": corpus_ref,
            "request_timeout_s": 60 if pilot else 30})
        account, campaign = job + ":account", "oauth-receipt-d12" if trial else "oauth-first-receipt"
        plan = NativeLaunch.model_validate({"schema": "strata/NativeLaunch/1", "job_id": job,
            "campaign_id": campaign, "agent_id": "a1", "epoch": 1, "role": "executor",
            "purpose": native_piloting.PURPOSE if pilot else "conformance",
            "parent_job_id": None, "depth": 0, "helper_limit": 0,
            "account": account, "operation_id": job + ":envelope", "workspace": str(workspace),
            "profile_directory": str(profile), "executable": str(args.codex),
            "binary_digest": CODEX_BINARY_SHA256, "binary_version": CODEX_VERSION,
            "dovetail_commit": DOVETAIL_COMMIT, "model": basis.model, "provider": "openai",
            "auth_mode": "chatgpt_oauth", "budget_mode": "per_dispatch",
            "accounting_basis_digest": basis.fingerprint(), "broker_policy": previous.broker_policy,
            "bootstrap_manifest": sealed["path"], "bootstrap_digest": sealed["sha256"],
            "tool_catalog_policy": catalog["policy"],
            "ingress_policy": INGRESS_POLICY, "gateway_config_digest": gateway_config.profile_fingerprint(),
            "config_overrides": config, "environment": {"PATH": previous.environment["PATH"],
            "TMP": str(temporary), "TEMP": str(temporary)}, "prompt": PROMPT,
            "hard_timeout_s": 90, "output_limit_bytes": previous.output_limit_bytes, "qualification_ref": None})
        if pilot:
            scope = {k: pilot["descriptor"][k] for k in ("campaign_id", "agent_id", "epoch")}
            plan = plan.model_copy(update=scope | {"prompt": native_piloting.prompt(scope, pilot["lease_id"], calls)})
            campaign = plan.campaign_id
        plan = plan.model_copy(update={"tool_projection_ref": pin_tool_projection(
            cas, plan, json.loads(args.tool_projections.read_bytes()))})
        gateway_config.profile_digest = plan.profile_digest()
        if pilot:
            native_piloting.require_profile(plan, gateway_config, pilot["lease_id"])
        else:
            require_receipt_profile(plan, gateway_config)
        transfer = inspect_preflight(args.preflight, plan, cas, piloting=bool(pilot))
        transfer_ref = put(cas, transfer)
        tls = tls_probe()
        tls_ref = put(cas, tls)
        (output / "tls.json").write_bytes(canonical(tls))
        price_evidence = put(cas, {"schema": "strata/PublishedExposureBasis/1", "is_example": False,
            "basis": basis.model_dump(), "source_kind": "published_model_API_limits",
            "sources": basis.price_sources, "observed_date": basis.price_date,
            "meaning": "conservative API-equivalent exposure, not an OAuth invoice or measured token limit"})
        checks = {}
        prerequisites = {"native_tool_boundary": [transfer_ref], "all_request_reservations": [transfer_ref],
            "credential_containment": [transfer_ref], "finite_exposure": [price_evidence], "verified_tls": [tls_ref]}
        if pilot:
            prerequisites.pop("credential_containment")
            prerequisites["scoped_native_tools"] = prerequisites.pop("native_tool_boundary")
        for check, refs in prerequisites.items():
            checks[check] = put(cas, {"schema": "strata/NativePreDispatchEvidence/1", "is_example": False,
                "scope": native_piloting.PURPOSE if pilot else "first_receipt_conformance", "check": check, "result": "pass",
                "profile_digest": plan.profile_digest(), "evidence_refs": refs})
        exposure.enforcement_ref = put(cas, {"schema": "strata/InferenceExposureEvidence/1",
            "is_example": False, "profile_digest": plan.profile_digest(), "result": "pass",
            "evidence_ref": price_evidence, **{k: getattr(exposure, k) for k in (
                "basis_digest", "input_bound_method", "output_bound_method", "max_input_tokens", "max_output_tokens")}})
        gateway_config.exposure = exposure
        limits = dict.fromkeys(DIMENSIONS, None) | {"spend_microusd": job_amount, "model_calls": calls}
        require(db.connection.execute("SELECT 1 FROM accounts WHERE id=?", (account,)).fetchone() is None,
                "FIRST_RECEIPT_ALREADY_PREPARED")
        gate.budgets.create_account(account, limits, campaign, plan.agent_id, before["account"], category="development")
        # Native authentication receives a private copy only after native boundary,
        # fixed peer and finite allowance prerequisites have passed. Never serialize
        # token fields to a journal or qualification artifact.
        auth_bytes = args.credentials.read_bytes()
        auth_body = json.loads(auth_bytes)
        require(auth_body.get("auth_mode") == "chatgpt" and isinstance(auth_body.get("tokens"), dict)
                and all(isinstance(auth_body["tokens"].get(k), str) and auth_body["tokens"][k]
                        for k in ("access_token", "refresh_token", "id_token", "account_id")),
                "NATIVE_AUTH_CACHE_REQUIRED")
        account_digest = hashlib.sha256(auth_body["tokens"]["account_id"].encode()).hexdigest()
        (profile / "auth.json").write_bytes(auth_bytes)
        del auth_bytes, auth_body
        permit = {"schema": SCHEMA, "is_example": False, "purpose": "first_receipt_conformance",
            "production_qualified": False, "policy": OAUTH_POLICY, "job_id": job,
            "profile_digest": plan.profile_digest(), "account_digest": account_digest,
            "host": HOST, "paths": PATHS, "native_headers": sorted(NATIVE_HEADERS),
            "gateway_config_digest": plan.gateway_config_digest, "authorization_id": args.authorization,
            "authorization_digest": digest(auth.check(args.authorization, account, "openai", "chatgpt_oauth",
                                                       basis.model).model_dump()),
            "basis_digest": basis.fingerprint(), "maximum_microusd": amount,
            "expires_unix": time.time() + 300, "max_requests": 1, "prechecks": checks}
        if pilot:
            permit.update(schema=native_piloting.SCHEMA, purpose=native_piloting.PURPOSE,
                scope_decision="D14", isolation_qualified=False, lease_id=pilot["lease_id"],
                max_requests=calls, maximum_microusd=job_amount)
        gateway_config.transport_qualification_ref = put(cas, permit)
        from mcbench.native_conformance import validate_permit
        (native_piloting.validate_permit if pilot else validate_permit)(
            gate, permit, plan, gateway_config, account_digest=account_digest)
        if not pilot:
            runtime_checks = {}
            for check in CONFORMANCE_PREREQUISITES:
                runtime_checks[check] = put(cas, {"is_example": False, "check": check, "result": "pass",
                    "scope": "pre_dispatch_first_receipt_only", "evidence_refs": [transfer_ref, price_evidence, tls_ref],
                    "profile_digest": plan.profile_digest(), "workspace": plan.workspace,
                    "profile_directory": plan.profile_directory, "role": plan.role,
                    "environment_digest": digest(plan.environment), "currency": "USD", "auth_mode": plan.auth_mode,
                    "pricing_semantics_verified": True, "finite_dispatch_bound_verified": True,
                    "accounting_basis_digest": basis.fingerprint()})
            plan.qualification_ref = put(cas, {"schema": "strata/RuntimeQualification/1", "is_example": False,
                "profile_digest": plan.profile_digest(), "purpose": "conformance",
                "expires_unix": time.time()+300, "checks": runtime_checks})
        if pilot:
            plan.qualification_ref = put(cas, {"schema": "strata/NativePilotAdmission/1", "is_example": False,
                "scope_decision": "D14", "isolation_qualified": False, "production_qualified": False,
                "profile_digest": plan.profile_digest(), "account_digest": account_digest,
                "permit_ref": gateway_config.transport_qualification_ref})
        gateway.bind(plan, gateway_config)
        reserve = ledger(plan, plan.operation_id, parent=None, calls=calls, spend=job_amount, pricing=pricing,
            inputs=exposure.max_input_tokens*calls, outputs=exposure.max_output_tokens*calls).model_copy(
                update={"reason": "D12 distinct receipt trial; retained prior hold; API-equivalent estimate" if trial
                        else "D14 development piloting; API-equivalent estimate" if pilot
                        else "D11 first native OAuth receipt conformance; API-equivalent estimate"})
        if trial == "D12":
            from mcbench.metering_trial import MeteringTrials, MAXIMUM, POLICY as TRIAL_POLICY
            require(amount == MAXIMUM, "METERING_TRIAL_SCOPE")
            decision_ref = put(cas, {"schema": "strata/MeteringTrialDecision/1", "decision_id": "D12",
                "policy": TRIAL_POLICY, "authorization_id": args.authorization,
                "authorization_digest": digest(auth.check(args.authorization, account, "openai", "chatgpt_oauth",
                                                         basis.model).model_dump()),
                "maximum_microusd": MAXIMUM, "max_requests": 1, "retained_hold_microusd": MAXIMUM,
                "combined_exposure_microusd": 2 * MAXIMUM, "user_authorized": True})
            record = MeteringTrials(db).install(args.authorization, plan, reserve, decision_ref=decision_ref,
                                               cas=cas, snapshot_digest=auth.snapshot())
            (output / "metering-trial.json").write_bytes(canonical(record))
        if pilot and pilot.get("budget_decision") is not None:
            from mcbench.pilot_budget import install
            record = install(db, cas, plan, reserve, pilot["budget_decision"])
            (output / "pilot-budget.json").write_bytes(canonical(record))
        (output / "admission.json").write_bytes(canonical({"profile_digest": plan.profile_digest(),
            "maximum_microusd": job_amount, "transfer_ref": transfer_ref, "permit_ref": gateway_config.transport_qualification_ref,
            "no_game_grant": not bool(pilot), "helper_limit": 0, "max_requests": calls, "production_qualified": False,
            **({"isolation_qualified": False, "scope_decision": "D14"} if pilot else {})}))
        if worker:
            worker.bind(plan)
        runtime.start(plan, reserve)
        wait_job(runtime, plan)
    finally:
        gateway.stop_admission()
        for active in list(runtime.live):
            runtime.interrupt(active, "conformance_cleanup")
        seal = gateway.close(runtime)
        if plan and db.connection.execute("SELECT 1 FROM native_jobs WHERE id=?", (plan.job_id,)).fetchone():
            closure_error = None
            try:
                runtime.close_dispatch_budget(plan.job_id, seal)
            except Fault as error:
                closure_error = error.code  # Unknown costs retain their existing holds.
            if pilot:
                from native_pilot_report import record_outcome as pilot_outcome
                ref, result = pilot_outcome(gate, plan, seal)
            else:
                ref, result = record_outcome(gate, plan, seal)
            result.update(result_ref=ref, closure_error=closure_error, runtime=runtime.status(plan.job_id))
            (output / "result.json").write_bytes(canonical(result))
            db.export_journal(output / "journal.jsonl")
        db.close()
    return {"result": result["receipt_result"], "profile_digest": plan.profile_digest(),
            "attempts": result["attempts"], "valuations": result["valuations"],
            "closure_error": result["closure_error"], "production_qualified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--objects", type=Path, required=True)
    parser.add_argument("--credentials", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--authorization", default="validation-2026-09-18")
    parser.add_argument("--metering-trial", choices=["D12"])
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--tool-projections", type=Path)
    args = parser.parse_args()
    try:
        result = run(args)
        print(json.dumps(result, indent=2))
        if result["result"] != "pass" or result["closure_error"] is not None:
            raise SystemExit(1)
    except Exception as error:
        # Never print an exception's raw text from a credential-bearing operation.
        print(json.dumps({"result": "failed", "code": error.code if isinstance(error, Fault)
                          else type(error).__name__}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
