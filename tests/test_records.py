import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.records import (
    AGENT_RECORDS, CANONICAL_RECORDS, EVALUATOR_RECORDS, OPERATOR_RECORDS, AgentConfig,
    BudgetLedger, CampaignConfig, EvaluationProtocol, KeybindingPatch, PackLock,
)
from mcbench.authorization import ExecutionAuthorization
from mcbench.native import NativeLaunch
from mcbench.provisioning import (
    AcquisitionReceipt, LaunchProfile, ProvisioningCheck, ProvisioningEvidence, RoleInventoryInput,
)


@pytest.mark.parametrize("model", [ExecutionAuthorization, NativeLaunch, AcquisitionReceipt,
                                  LaunchProfile, ProvisioningCheck, ProvisioningEvidence,
                                  RoleInventoryInput])
def test_operator_api_schemas_stay_private_and_match_models(model):
    root = Path(__file__).resolve().parents[1] / "schemas/v1"
    path = root / "operator" / (model.__name__ + ".json")
    schema = json.loads(path.read_text(encoding="utf-8"))
    assert schema == model.model_json_schema() | {"$schema": "https://json-schema.org/draft/2020-12/schema"}
    assert not (root / "public" / path.name).exists()


@pytest.mark.parametrize("model", CANONICAL_RECORDS)
def test_all_thirteen_examples_and_partitioned_schemas(example, model):
    body = example(model.__name__)
    assert model.model_validate(body).model_dump() == body
    domain = "public" if model in AGENT_RECORDS else (
        "operator" if model in OPERATOR_RECORDS else "evaluator")
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/v1" / domain /
                         f"{model.__name__}.json").read_text())
    assert schema == model.model_json_schema() | {"$schema": "https://json-schema.org/draft/2020-12/schema"}
    with pytest.raises(ValidationError):
        model.model_validate(body | {"unexpected": True})
    with pytest.raises(ValidationError):
        model.model_validate(body | {"schema": f"mcbench/{model.__name__}/2"})
    assert len(CANONICAL_RECORDS) == 13
    assert not set(EVALUATOR_RECORDS) & set(AGENT_RECORDS)


@pytest.mark.parametrize("n", [0, -1, 1.5, True, 2**53, "2"])
def test_invalid_team_size(example, n):
    with pytest.raises(ValidationError):
        CampaignConfig.model_validate(example("CampaignConfig") | {"n": n})


def test_roster_schedule_identity_and_large_n(example, configs):
    for patch in ({"n": 2, "agent_ids": ["a1", "a1"]}, {"checkpoints_active_s": [1, 2]},
                  {"checkpoints_active_s": [0, 1, 1]}, {"checkpoints_active_s": [0, 86401]}):
        with pytest.raises(ValidationError):
            CampaignConfig.model_validate(example("CampaignConfig") | patch)
    config, _ = configs(10000)
    assert config.n == 10000  # no arbitrary small parser cap; scheduler checks resources
    with pytest.raises(ValidationError):
        AgentConfig.model_validate(example("AgentConfig") | {"identity_assurance": "immutable"})


def test_seal_keybinding_budget_and_protocol_semantics(example):
    for model, name, patch in (
        (PackLock, "PackLock", {"status": "sealed"}),
        (PackLock, "PackLock", {"sealed_at": "2026-02-31T01:00:00Z"}),
        (KeybindingPatch, "KeybindingPatch", {"phase": "committed"}),
        (EvaluationProtocol, "EvaluationProtocol", {"family_weights": {"craft": 0.0}}),
        (EvaluationProtocol, "EvaluationProtocol", {"alpha": float("nan")}),
        (EvaluationProtocol, "EvaluationProtocol", {"primary_checkpoint_s": 22}),
    ):
        with pytest.raises(ValidationError):
            model.model_validate(example(name) | patch)
    body = example("BudgetLedger")
    for patch in ({"input_tokens": -1}, {"cached_input_tokens": 1001}, {"reasoning_tokens": 101}):
        with pytest.raises(ValidationError):
            BudgetLedger.model_validate(body | {"usage": body["usage"] | patch})
