from pathlib import Path

import pytest

from mcbench.authorization import Authorizations, ExecutionAuthorization, LegacyExecutionAuthorization
from mcbench.budgets import DIMENSIONS
from mcbench.records import BudgetLedger
from mcbench.storage import CAS, Fault, Principal, canonical, digest


def policy():
    source = Path(__file__).resolve().parents[1] / "configs/operator/live-validation.json"
    return ExecutionAuthorization.model_validate_json(source.read_text(encoding="utf-8"))


def install(service, approved):
    source = Path(__file__).resolve().parents[1] / "configs/operator/legacy/live-validation-v1.json"
    legacy = LegacyExecutionAuthorization.model_validate_json(source.read_text(encoding="utf-8"))
    service.install(legacy)
    cas = CAS(service.db, service.db.path.parent / "objects")
    ref = cas.put(Principal("operator", "operator"), "operator", "operator", b'synthetic audit')
    audit = {"schema":"strata/AuthorizationMigrationAudit/1",
        "authorization_id":approved.authorization_id,"decision_id":"D11",
        "source_authorization_digest":approved.legacy_authorization_digest,
        "snapshot_digest":service.snapshot(),"store_path_digest":digest(str(service.db.path)),
        "legacy_amount_semantics":"unknown_conservative","external_inventory_ref":ref,
        "decision_ref":ref,"policy":"preserve_all_accounts_operations_receipts_and_holds/1"}
    ref = cas.put(Principal("operator","operator"), "operator", "operator", canonical(audit))
    return service.migrate(approved, snapshot_digest=service.snapshot(), evidence_ref=ref,
                           legacy_amount_semantics="unknown_conservative", cas=cas)


def test_user_authorization_exact_oauth_luna_ten_dollars_no_reset(database, example):
    service = Authorizations(database)
    approved = policy()
    root = install(service, approved)
    assert approved.auth_mode == "chatgpt_oauth" and approved.models == ["gpt-5.6-luna"]
    assert approved.total_spend_microusd == 10_000_000
    assert service.install(approved) == root
    with pytest.raises(Fault, match="AUTHORIZATION_CONFLICT"):
        service.install(approved.model_copy(update={"total_spend_microusd": 11_000_000}))
    for category in ("training", "evaluation", "development"):
        service.budgets.create_account(category, dict.fromkeys(DIMENSIONS, 100_000_000),
                                        "c1", "a1", root, category=category)
        assert service.check(approved.authorization_id, category, "openai", "chatgpt_oauth",
                             "gpt-5.6-luna") == approved
    body = example("BudgetLedger")
    def reserve(category, spend):
        return BudgetLedger.model_validate(body | {"is_example": False, "posting": "reserve",
            "operation_id": category, "source_event_id": category, "parent_operation_id": None,
            "campaign_account": category, "usage": body["usage"] | {"spend_microusd": spend}})
    service.budgets.post("training", reserve("training", 6_000_000))
    service.budgets.post("evaluation", reserve("evaluation", 4_000_000))
    service.install(approved)  # Reinstall cannot reset consumed/reserved capacity.
    with pytest.raises(Fault, match="BUDGET_EXHAUSTED"):
        service.budgets.post("development", reserve("development", 1))
    assert service.status(approved.authorization_id)["budget"]["committed_and_reserved"][
        "spend_microusd"] == 10_000_000
    for provider, mode, model in (("openai", "api_key", "gpt-5.6-luna"),
                                   ("openai", "chatgpt_oauth", "gpt-6-astra"),
                                   ("another", "chatgpt_oauth", "gpt-5.6-luna")):
        with pytest.raises(Fault, match="UNAUTHORIZED_MODEL_OR_PROVIDER"):
            service.check(approved.authorization_id, "training", provider, mode, model)


def test_unparented_account_cannot_bypass_global_ceiling(database):
    service = Authorizations(database)
    approved = policy()
    install(service, approved)
    service.budgets.create_account("unparented", dict.fromkeys(DIMENSIONS, 100_000_000),
                                   "c1", "a1", category="training")
    with pytest.raises(Fault, match="UNAUTHORIZED_BUDGET_ACCOUNT"):
        service.check(approved.authorization_id, "unparented", "openai", "chatgpt_oauth",
                       "gpt-5.6-luna")
