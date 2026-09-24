"""Synthetic admission parser fixtures. No real credentials, TLS or inference."""

import hashlib
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import test_native_gateway

from mcbench.authorization import ExecutionAuthorization
from mcbench.native_conformance import (
    PRECHECKS, PROMPT, SCHEMA, require_receipt_profile, validate_permit,
)
from mcbench.native_oauth import HOST, NATIVE_HEADERS, PATHS, POLICY
from mcbench.native_skills import INSTRUCTIONS
from mcbench.storage import Fault, canonical, digest

gateway = test_native_gateway.gateway
provider = test_native_gateway.provider


@pytest.fixture
def permit(gateway, tmp_path):
    g = gateway
    broker = tmp_path / "empty-broker.json"
    broker.write_text(json.dumps({"worker_grant": None}))
    manifest = tmp_path / "manifest.json"
    raw = canonical({"schema": "strata/NativeBootstrap/1", "broker_config": str(broker)})
    manifest.write_bytes(raw)
    cfg = g.cfg.model_copy(deep=True, update={"authorization_id": "validation-2026-09-18",
        "skill_corpus_ref": "cas:sha256:" + "b" * 64, "helper_calls_bound": 1,
        "max_handlers": 1, "max_requests": 1})
    plan = g.plan.model_copy(deep=True, update={"purpose": "conformance", "helper_limit": 0,
        "prompt": PROMPT, "bootstrap_manifest": str(manifest),
        "bootstrap_digest": hashlib.sha256(raw).hexdigest(), "gateway_config_digest": cfg.profile_fingerprint(),
        "config_overrides": g.plan.config_overrides | {"developer_instructions": INSTRUCTIONS}})
    cfg.profile_digest = plan.profile_digest()
    policy = ExecutionAuthorization.model_validate_json((Path(__file__).resolve().parents[1] /
        "configs/operator/legacy/live-validation-d11.json").read_text())
    data = {}
    for check in PRECHECKS:
        data[check] = canonical({"schema": "strata/NativePreDispatchEvidence/1", "is_example": False,
            "profile_digest": plan.profile_digest(), "check": check, "scope": "first_receipt_conformance",
            "result": "pass", "evidence_refs": ["synthetic-evidence"]})
    data["synthetic-evidence"] = b'{"fixture":true}'
    fake = SimpleNamespace(simulation=False, authorizations=SimpleNamespace(check=lambda *a: policy),
        _private_ref=lambda ref, size: data[ref])
    proof = {"schema": SCHEMA, "is_example": False, "purpose": "first_receipt_conformance",
        "production_qualified": False, "policy": POLICY, "job_id": plan.job_id,
        "profile_digest": plan.profile_digest(), "account_digest": "c" * 64, "host": HOST,
        "paths": PATHS, "native_headers": sorted(NATIVE_HEADERS),
        "gateway_config_digest": plan.gateway_config_digest, "authorization_id": cfg.authorization_id,
        "authorization_digest": digest(policy.model_dump()), "basis_digest": plan.accounting_basis_digest,
        "maximum_microusd": 755400, "expires_unix": time.time() + 60, "max_requests": 1,
        "prechecks": {check: check for check in PRECHECKS}}
    return fake, proof, plan, cfg, data, broker


def test_first_receipt_admission_does_not_require_invented_receipt(permit):
    gate, proof, plan, cfg, _, _ = permit
    assert validate_permit(gate, proof, plan, cfg, account_digest="c" * 64).first_trial_max_microusd == 1000000
    assert "usage_receipts" not in proof["prechecks"] and proof["production_qualified"] is False


@pytest.mark.parametrize("field,value", [("purpose", "campaign"), ("helper_limit", 1),
    ("prompt", "do something else"), ("role", "helper"), ("hard_timeout_s", 121),
    ("bootstrap_digest", None), ("budget_mode", "whole_job")])
def test_scope_expansion_never_admitted(permit, field, value):
    _, _, plan, cfg, _, _ = permit
    plan = plan.model_copy(update={field: value})
    cfg.profile_digest = plan.profile_digest()
    with pytest.raises(Fault, match="RECEIPT_CONFORMANCE_SCOPE"):
        require_receipt_profile(plan, cfg)


@pytest.mark.parametrize("field,value", [("max_requests", 2), ("max_handlers", 2),
    ("helper_calls_bound", 2), ("skill_corpus_ref", None), ("authorization_id", None)])
def test_gateway_privilege_expansion_rejected(permit, field, value):
    _, _, plan, cfg, _, _ = permit
    cfg = cfg.model_copy(update={field: value})
    plan.gateway_config_digest = cfg.profile_fingerprint()
    cfg.profile_digest = plan.profile_digest()
    with pytest.raises(Fault, match="RECEIPT_CONFORMANCE_SCOPE"):
        require_receipt_profile(plan, cfg)


@pytest.mark.parametrize("field,value", [("production_qualified", True), ("is_example", True),
    ("job_id", "sibling"), ("account_digest", "d" * 64), ("host", "example.invalid"),
    ("max_requests", 2), ("expires_unix", 1), ("maximum_microusd", 1),
    ("authorization_digest", "d" * 64)])
def test_permit_cannot_change_account_authority_scope_or_cost(permit, field, value):
    gate, proof, plan, cfg, _, _ = permit
    proof[field] = value
    with pytest.raises(Fault, match="OAUTH_CONFORMANCE"):
        validate_permit(gate, proof, plan, cfg, account_digest="c" * 64)


def test_prechecks_and_no_game_are_mandatory(permit):
    gate, proof, plan, cfg, data, broker = permit
    for check in PRECHECKS:
        old = data[check]
        item = json.loads(old)
        item["result"] = "fail"
        data[check] = canonical(item)
        with pytest.raises(Fault, match="OAUTH_CONFORMANCE_EVIDENCE"):
            validate_permit(gate, proof, plan, cfg, account_digest="c" * 64)
        data[check] = old
    broker.write_text('{"worker_grant":"game.json"}')
    with pytest.raises(Fault, match="RECEIPT_GAME_FORBIDDEN"):
        require_receipt_profile(plan, cfg)


@pytest.mark.parametrize("receipt,closure,status", [("fail", "METERING_UNKNOWN", 1),
    ("pass", "RUNTIME_NOT_QUIESCENT", 1), ("pass", None, 0)])
def test_operator_command_failure_is_nonzero_without_dispatch(monkeypatch, capsys, receipt, closure, status):
    import runpy
    import sys
    tools = Path(__file__).resolve().parents[1] / "tools"
    monkeypatch.syspath_prepend(str(tools))
    main = runpy.run_path(str(tools / "native_oauth_conformance.py"))["main"]
    monkeypatch.setitem(main.__globals__, "run", lambda _: {"result": receipt, "closure_error": closure})
    monkeypatch.setattr(sys, "argv", ["probe"] + [arg for name in (
        "codex", "output", "database", "objects", "credentials", "preflight") for arg in ("--" + name, "unused")])
    if status:
        with pytest.raises(SystemExit) as error:
            main()
        assert error.value.code == status
    else:
        main()
    assert json.loads(capsys.readouterr().out)["result"] == receipt
