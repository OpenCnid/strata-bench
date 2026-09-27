"""Synthetic committed-source probe selection; no actual clone admission."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault, Principal, canonical, digest
from strata_evaluator.native_probe_projection import (
    POLICY, NativeProbeArtifactProjection, NativeProbeArtifactSelection, project_native_checkpoint,
)
from test_native_selected_activation import selected_seed

EVALUATOR = Principal("evaluation", "evaluator")
OPERATOR = Principal("operator", "operator")


def selection(sets, ref, **patch):
    body = sets.load(ref)
    state, _ = sets.components.load(body["checkpoint_ref"])
    policy = sets.cas.json(OPERATOR, "operator", state.retention_policy)
    initial = sets.cas.json(OPERATOR, "operator", policy["initial_artifacts"])["files"]
    return {"schema": "strata/NativeProbeArtifactSelection/1", "policy": POLICY,
        "is_example": True, "skill_set_ref": ref, "initial_paths": sorted(initial),
        "retained_paths": [], "skill_names": [], **patch}


@pytest.fixture
def source(database, cas, tmp_path, example, configs):
    return selected_seed(database, cas, tmp_path, example, configs)


@pytest.mark.parametrize("arm", ["full", "frozen-persistence", "frozen-skills", "no-self-play"])
def test_committed_projection_keeps_costs_and_exact_admissible_bytes(
        database, cas, tmp_path, example, configs, arm):
    runtime, sets, ref = selected_seed(database, cas, tmp_path, example, configs, arm=arm)
    note_paths = [] if arm == "frozen-persistence" else ["notes/root.md", "handoff/next.md"]
    names = ["learned-crafting"] if arm in {"full", "no-self-play"} else []
    chosen = selection(sets, ref, retained_paths=note_paths, skill_names=names)
    before = list(database.connection.iterdump())
    result = project_native_checkpoint(EVALUATOR, sets, chosen)
    assert list(database.connection.iterdump()) == before
    assert result.selection_digest == digest(chosen) and result.arm == arm
    assert result.model_identity == "gpt-6-luna" and result.actual_active_s == 3600
    assert result.session is result.runtime_cache is None
    assert not result.dispatch_authorized and not result.campaign_feedback_allowed
    assert set(result.experienced_files) == set(chosen["initial_paths"]) | set(note_paths)
    for path in note_paths:
        assert result.experienced_files[path] == sets.load(ref)["workspace"][path]
    for name in names:
        skill = result.experienced_skills[name]
        assert skill.files == sets.load(ref)["skills"][name]["files"]
        assert "provenance_refs" not in skill.model_dump()
        assert skill.kind == "executable"
    assert not any(p.startswith(("results/", "active/")) or p == "skills/publish.json"
                   for p in result.experienced_files)
    assert "skills/draft.md" not in result.experienced_files
    assert result.experienced_files["initial/SKILL.md"] == result.initial_files["initial/SKILL.md"]
    if arm == "frozen-persistence":
        assert result.experienced_files == result.initial_files
    assert NativeProbeArtifactProjection.model_validate_json(canonical(result.model_dump())) == result
    assert runtime[0].budgets.status("a1")["uncertain"] is False


@pytest.mark.parametrize("path", ["results/private.md", "skills/draft.md", "skills/publish.json",
    "active/revisions.json", "docs/allowed.md", "notes/absent.md"])
def test_nonretained_and_unavailable_artifacts_refuse(source, path):
    _, sets, ref = source
    with pytest.raises(Fault, match="PROBE_RETAINED_SOURCE"):
        project_native_checkpoint(EVALUATOR, sets, selection(sets, ref, retained_paths=[path]))


@pytest.mark.parametrize("path", ["notes/../secret", "C:/secret", "notes/auth.json",
    "notes/keymap.json", "notes/options.txt", "notes/runtime_state.json"])
def test_traversal_credentials_and_personal_configuration_refuse(source, path):
    _, sets, ref = source
    with pytest.raises(Fault, match="UNSAFE_PATH|PROBE_STATE_FORBIDDEN"):
        project_native_checkpoint(EVALUATOR, sets, selection(sets, ref, retained_paths=[path]))


def test_selection_cannot_downgrade_initial_procedures_or_select_candidate_as_active(source):
    _, sets, ref = source
    chosen = selection(sets, ref)
    chosen["initial_paths"].remove("initial/SKILL.md")
    with pytest.raises(Fault, match="PROBE_INITIAL_PROCEDURES_REQUIRED"):
        project_native_checkpoint(EVALUATOR, sets, chosen)
    with pytest.raises(Fault, match="PROBE_ACTIVE_SKILL_REQUIRED"):
        project_native_checkpoint(EVALUATOR, sets, selection(sets, ref, skill_names=["draft"]))
    with pytest.raises(Fault, match="PROBE_INITIAL_SOURCE"):
        project_native_checkpoint(EVALUATOR, sets, selection(sets, ref, initial_paths=["initial/absent.md"]))


@pytest.mark.parametrize("role", ["executor", "helper"])
def test_gameplay_cannot_use_private_projection_service(source, role):
    _, sets, ref = source
    with pytest.raises(Fault, match="FORBIDDEN"):
        project_native_checkpoint(Principal("campaign:c1:agent:a1", role), sets, selection(sets, ref))


def test_substituted_uncommitted_source_is_not_an_approval(source):
    _, sets, ref = source
    body = sets.load(ref) | {"model_identity": "substituted"}
    forged = sets.cas.put(OPERATOR, "operator", "operator", canonical(body))
    with pytest.raises(Fault):
        project_native_checkpoint(EVALUATOR, sets, selection(sets, ref, skill_set_ref=forged))


def test_evaluation_account_cannot_be_relabeled_as_campaign_knowledge(
        database, cas, tmp_path, example, configs, monkeypatch):
    from mcbench.budgets import Budgets
    original = Budgets.create_account
    def evaluation_account(self, *args, **kwargs):
        return original(self, *args, **(kwargs | {"category": "evaluation"}))
    def evaluation_example(name):
        value = example(name)
        return value | {"campaign_account": "evaluation"} if name == "BudgetLedger" else value
    monkeypatch.setattr(Budgets, "create_account", evaluation_account)
    # Admission now assigns the campaign posting category explicitly. Relabeling
    # its account is refused before a campaign checkpoint can even be produced.
    with pytest.raises(Fault, match="^FORBIDDEN$"):
        selected_seed(database, cas, tmp_path, evaluation_example, configs, arm="frozen-skills")
    assert database.connection.execute("SELECT count(*) FROM native_jobs").fetchone()[0] == 0
    assert database.connection.execute("SELECT count(*) FROM ledger").fetchone()[0] == 0


def test_projection_independently_rejects_evaluation_source_identity(source, monkeypatch):
    """Synthetic decoded identity tests the downstream guard independently."""
    from strata_evaluator import native_probe_projection as projection
    _, sets, ref = source
    chosen = selection(sets, ref, retained_paths=["notes/root.md"])
    body = sets.load(ref)
    state, _ = sets.components.load(body["checkpoint_ref"])
    exported = sets.publications.exports.load(state.source_export)
    original = projection.private_json
    intercepted = []

    def evaluation_identity(db, cas, reference):
        value = original(db, cas, reference)
        if reference == exported.source_ref:
            intercepted.append(reference)
            return value | {"account_identities": [
                identity | {"category": "evaluation"} for identity in value["account_identities"]]}
        return value

    before = list(sets.db.connection.iterdump())
    monkeypatch.setattr(projection, "private_json", evaluation_identity)
    with pytest.raises(Fault, match="PROBE_IMPORT_FORBIDDEN"):
        project_native_checkpoint(EVALUATOR, sets, chosen)
    assert intercepted == [exported.source_ref]
    assert list(sets.db.connection.iterdump()) == before


@pytest.mark.parametrize("patch", [
    {"origin": "campaign"}, {"files": {"notes/root.md": "cas:sha256:" + "a"*64}},
    {"at_t0": True}, {"is_example": 1}, {"skill_names": "all"}, {"schema": "strata/NativeProbeArtifactSelection/2"},
])
def test_no_caller_origin_raw_refs_or_unproven_time_zero(source, patch):
    _, sets, ref = source
    with pytest.raises(ValidationError):
        project_native_checkpoint(EVALUATOR, sets, selection(sets, ref, **patch))


@pytest.mark.parametrize("arm,boundary,patch,fault", [
    ("frozen-persistence", "recovery", {"retained_paths": ["notes/root.md"]}, "PROBE_FROZEN_PERSISTENCE"),
    ("frozen-persistence", "episode", {"skill_names": ["learned-crafting"]}, "PROBE_FROZEN_PERSISTENCE"),
    ("frozen-skills", "episode", {"skill_names": ["learned-crafting"]}, "PROBE_FROZEN_SKILLS"),
])
def test_arm_rules_cannot_be_evaded_with_recovery_or_skill_selection(
        database, cas, tmp_path, example, configs, arm, boundary, patch, fault):
    _, sets, ref = selected_seed(database, cas, tmp_path, example, configs, arm=arm, boundary=boundary)
    with pytest.raises(Fault, match=fault):
        project_native_checkpoint(EVALUATOR, sets, selection(sets, ref, **patch))


@pytest.mark.parametrize("model", [NativeProbeArtifactSelection, NativeProbeArtifactProjection])
def test_projection_schemas_are_evaluator_only(model):
    root = Path(__file__).resolve().parents[1] / "schemas/v1"
    name = model.__name__ + ".json"
    assert json.loads((root / "evaluator" / name).read_bytes()) == model.model_json_schema() | {
        "$schema": "https://json-schema.org/draft/2020-12/schema"}
    assert not (root / "public" / name).exists() and not (root / "operator" / name).exists()
