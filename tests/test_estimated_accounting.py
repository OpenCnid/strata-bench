"""D11 arithmetic and migration tests; all usage and audit inputs are synthetic."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.accounting import EstimateBasis, FiniteExposure, TokenUsage
from mcbench.authorization import (
    Authorizations,
    ExecutionAuthorization,
    LegacyExecutionAuthorization,
)
from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceDispatches
from mcbench.records import BudgetLedger
from mcbench.storage import CAS, Database, Fault, Principal, canonical, digest

ROOT = Path(__file__).resolve().parents[1]


def policy():
    return ExecutionAuthorization.model_validate_json(
        (ROOT / "configs/operator/legacy/live-validation-d11.json").read_text(encoding="utf-8")
    )


def tokens(**updates):
    return (
        dict(
            model="gpt-5.6-luna",
            input_tokens=1_000_000,
            cached_input_tokens=200_000,
            cache_write_tokens=100_000,
            output_tokens=100_000,
            reasoning_tokens=20_000,
        )
        | updates
    )


def test_price_schedule_context_cache_subsets_and_rounding():
    basis = policy().accounting_basis
    # Full long-context request: .28 ordinary + .008 cache + .05 write + .18 output.
    assert basis.estimate(tokens()) == 518_000
    assert (
        basis.estimate(
            tokens(
                input_tokens=272000,
                cached_input_tokens=0,
                cache_write_tokens=0,
                output_tokens=100000,
            )
        )
        == 174400
    )
    assert (
        basis.estimate(
            tokens(
                input_tokens=272001,
                cached_input_tokens=0,
                cache_write_tokens=0,
                output_tokens=100000,
            )
        )
        == 288801
    )
    assert (
        basis.estimate(
            tokens(
                input_tokens=1,
                cached_input_tokens=0,
                cache_write_tokens=0,
                output_tokens=0,
                reasoning_tokens=0,
            )
        )
        == 1
    )
    # Unobserved writes conservatively price the entire uncached subset as writes.
    assert basis.estimate(tokens(cache_write_tokens=None)) == 588000
    assert basis.maximum_request(max_input_tokens=1050000, max_output_tokens=128000) == 755400
    assert basis.estimate(tokens(reasoning_tokens=None)) == basis.estimate(tokens())
    assert EstimateBasis.model_validate_json(basis.model_dump_json()) == basis


@pytest.mark.parametrize(
    "change",
    [
        {"cached_input_tokens": 900001},
        {"reasoning_tokens": 100001},
        {"input_tokens": True},
        {"output_tokens": -1},
        {"audio_tokens": 1},
        {"tool_calls": 1},
    ],
)
def test_invalid_or_unpriced_categories_fail_closed(change):
    with pytest.raises(ValidationError):
        TokenUsage.model_validate(tokens(**change))


def test_unknown_model_tier_and_unjustified_exposure_reject():
    basis = policy().accounting_basis
    with pytest.raises(Fault, match="PRICE_MODEL_MISMATCH"):
        basis.estimate(tokens(model="other"))
    with pytest.raises(ValidationError):
        EstimateBasis.model_validate(basis.model_dump() | {"reference_tier": "auto"})
    exposure = dict(
        schema="strata/FiniteInferenceExposure/1",
        basis_digest=basis.fingerprint(),
        max_input_tokens=1050000,
        max_output_tokens=128000,
        max_requests=1,
        input_bound_method="provider_context_limit",
        output_bound_method="provider_model_limit",
        enforcement_ref="cas:sha256:" + "a" * 64,
    )
    assert FiniteExposure.model_validate(exposure).amount(basis) == 755400
    with pytest.raises(ValidationError):
        FiniteExposure.model_validate(exposure | {"output_bound_method": "kill_after_10_seconds"})
    with pytest.raises(Fault, match="EXPOSURE_RANGE"):
        FiniteExposure.model_validate(exposure | {"max_output_tokens": 100}).amount(basis)


@pytest.fixture
def legacy_store(database, cas, example):
    auth = Authorizations(database)
    old = LegacyExecutionAuthorization.model_validate_json(
        (ROOT / "configs/operator/legacy/live-validation-v1.json").read_text(encoding="utf-8")
    )
    root = auth.install(old)
    auth.budgets.create_account(
        "a1", dict.fromkeys(DIMENSIONS, 100000000), "c1", "a1", root, category="training"
    )
    base = example("BudgetLedger")
    for op, spend in (("settled", 2000000), ("unknown", 3000000)):
        body = base | dict(
            is_example=False,
            operation_id=op,
            parent_operation_id=None,
            source_event_id=op + ":reserve",
            posting="reserve",
            usage=base["usage"] | {"spend_microusd": spend},
        )
        auth.budgets.post("a1", BudgetLedger.model_validate(body))
        if op == "settled":
            auth.budgets.post(
                "a1",
                BudgetLedger.model_validate(
                    body | {"posting": "settle", "source_event_id": op + ":settle"}
                ),
            )
        else:
            auth.budgets.hold_uncertain("a1", op, "synthetic missing receipt")
    ref = cas.put(Principal("operator", "operator"), "operator", "operator", b"synthetic audit")
    audit = {
        "schema": "strata/AuthorizationMigrationAudit/1",
        "authorization_id": old.authorization_id,
        "decision_id": "D11",
        "source_authorization_digest": policy().legacy_authorization_digest,
        "snapshot_digest": auth.snapshot(),
        "store_path_digest": digest(str(auth.db.path)),
        "legacy_amount_semantics": "unknown_conservative",
        "external_inventory_ref": ref,
        "decision_ref": ref,
        "policy": "preserve_all_accounts_operations_receipts_and_holds/1",
    }
    ref = cas.put(Principal("operator", "operator"), "operator", "operator", canonical(audit))
    args = dict(
        snapshot_digest=auth.snapshot(),
        evidence_ref=ref,
        legacy_amount_semantics="unknown_conservative",
        cas=cas,
    )
    return auth, old, root, args


def test_explicit_migration_preserves_settled_unknowns_and_restart(legacy_store):
    auth, old, root, args = legacy_store
    before = auth.budgets.status(root)
    with pytest.raises(Fault, match="LEGACY_ACCOUNTING_UNMIGRATED"):
        auth.check(old.authorization_id, "a1", "openai", "chatgpt_oauth", "gpt-5.6-luna")
    assert auth.migrate(policy(), **args) == root
    assert auth.snapshot() == args["snapshot_digest"]
    assert auth.budgets.status(root) == before
    assert before["committed_and_reserved"]["spend_microusd"] == 5000000
    assert before["uncertain"] and not before["dispatch_allowed"]
    second = Database(auth.db.path)
    try:
        restored = Authorizations(second)
        assert restored.migrate(policy(), **(args | {"cas": CAS(second, args["cas"].root)})) == root
        assert restored.budgets.status(root) == before
        status = restored.status(old.authorization_id)
        assert status["accounting_kind"] == "api_equivalent_estimate"
        assert not status["actual_charge_implied"] and not status["qualification_implied"]
    finally:
        second.close()


@pytest.mark.parametrize(
    "updates,code",
    [
        ({"total_spend_microusd": 11000000}, "MIGRATION_AUTHORITY_MISMATCH"),
        ({"models": ["gpt-6-astra"]}, "MIGRATION_AUTHORITY_MISMATCH"),
        ({"first_trial_max_microusd": 1000001}, "MIGRATION_AUTHORITY_MISMATCH"),
        ({"legacy_authorization_digest": "f" * 64}, "MIGRATION_AUDIT_MISMATCH"),
    ],
)
def test_incompatible_migration_cannot_change_any_accounting(legacy_store, updates, code):
    auth, old, root, args = legacy_store
    with pytest.raises(Fault, match=code):
        auth.migrate(policy().model_copy(update=updates), **args)
    assert auth.snapshot() == args["snapshot_digest"]
    assert auth.status(old.authorization_id)["accounting_kind"] == "legacy_unclassified"


def test_stale_snapshot_and_synthetic_store_never_promote(legacy_store):
    auth, old, root, args = legacy_store
    with pytest.raises(Fault, match="MIGRATION_AUDIT_MISMATCH"):
        auth.migrate(policy(), **(args | {"snapshot_digest": "a" * 64}))
    InferenceDispatches(auth.db, args["cas"], simulation=True)
    with pytest.raises(Fault, match="SIMULATION_STORE"):
        auth.migrate(policy(), **args)
    with pytest.raises(Fault, match="MIGRATION_SEMANTICS"):
        auth.migrate(policy(), **(args | {"legacy_amount_semantics": "synthetic_fixture_units"}))
    assert auth.snapshot() == args["snapshot_digest"]


def test_v2_install_cannot_allocate_a_fresh_ten_dollars(database):
    service = Authorizations(database)
    with pytest.raises(Fault, match="EXPLICIT_AUTHORIZATION_MIGRATION_REQUIRED"):
        service.install(policy())
    assert database.connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0


def test_snapshot_race_and_incomplete_audit_reject(legacy_store):
    auth, _, root, args = legacy_store
    auth.budgets.create_account("new-child", dict.fromkeys(DIMENSIONS, 100),
                                "c2", "a2", root, category="development")
    with pytest.raises(Fault, match="MIGRATION_SNAPSHOT_CHANGED"):
        auth.migrate(policy(), **args)
    bad_ref = args["cas"].put(Principal("operator", "operator"), "operator", "operator", b'{}')
    with pytest.raises(ValidationError):
        auth.migrate(policy(), **(args | {"evidence_ref": bad_ref}))


def test_migrated_live_authority_cannot_accept_simulated_dispatch_store(legacy_store):
    auth, _, _, args = legacy_store
    auth.migrate(policy(), **args)
    with pytest.raises(Fault, match="SIMULATION_AUTHORITY_MIX"):
        InferenceDispatches(auth.db, args["cas"], simulation=True)


def test_migration_write_failure_is_atomic(legacy_store):
    auth, old, root, args = legacy_store
    auth.db.connection.execute(
        "CREATE TRIGGER reject_migrate BEFORE UPDATE ON "
        "execution_authorizations BEGIN SELECT RAISE(ABORT,'fixture failure'); END"
    )
    with pytest.raises(Exception, match="fixture failure"):
        auth.migrate(policy(), **args)
    assert auth.snapshot() == args["snapshot_digest"]
    assert (
        auth.db.connection.execute("SELECT COUNT(*) FROM authorization_migrations").fetchone()[0]
        == 0
    )
    body = auth.db.connection.execute("SELECT body FROM execution_authorizations").fetchone()[0]
    assert digest(json.loads(body)) == policy().legacy_authorization_digest
