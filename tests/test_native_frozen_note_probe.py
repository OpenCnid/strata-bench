"""Synthetic prerequisites for actual selected native frozen-note verification."""

import json

import pytest

from mcbench.storage import Fault, Principal
from test_native_selected_activation import selected_seed
from native_frozen_note_probe import FrozenNoteProbe, DENIED, native_call_results
from native_fixture_checkpoint import next_checkpoint
from native_mcp_identity_probe import run


@pytest.mark.parametrize("boundary", ["episode", "recovery"])
def test_selected_frozen_seed_has_no_learned_package_and_is_not_frozen_persistence(
        database, cas, tmp_path, example, configs, boundary):
    source, service, ref = selected_seed(database, cas, tmp_path, example, configs,
                                         arm="frozen-skills", boundary=boundary)
    body = service.load(ref)
    state, _ = service.components.load(body["checkpoint_ref"])
    policy = cas.json(Principal("operator", "operator"), "operator", state.retention_policy)
    assert policy["schema"] == "strata/NativeRetentionPolicy/2" and policy["arm"] == "frozen-skills"
    assert not body["skills"] and "notes/root.md" in body["workspace"]
    assert database.connection.execute("SELECT count(*) FROM native_skill_publications").fetchone()[0] == 0
    probe = object.__new__(FrozenNoteProbe)
    probe.ref, probe.output = ref, tmp_path
    plan = probe.prepare(source[0], source[1])
    assert plan.purpose == "campaign" and plan.helper_skill_activation_ref == plan.skill_activation_ref == ref
    assert not probe.reset and not probe.publish_code()
    assert len(probe.cases("/root")) == len(DENIED)+5
    assert len(probe.cases("/root/identity_child")) == len(DENIED)+2
    assert source[0].budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 56


@pytest.mark.parametrize("arm", ["full", "frozen-skills"])
def test_complete_fixture_checkpoint_only_omits_publication_for_versioned_frozen_arm(
        database, cas, tmp_path, example, configs, arm, monkeypatch):
    from mcbench.native_revisions import NativeSkillPublications
    source, _, _ = selected_seed(database, cas, tmp_path, example, configs, arm=arm)
    calls = []
    original = NativeSkillPublications.publish
    def tracked(service, export):
        calls.append(export)
        assert arm == "full"
        return original(service, export)
    monkeypatch.setattr(NativeSkillPublications, "publish", tracked)
    result = next_checkpoint(source[0], "job", "cp1", "cp2", boundary="episode")
    assert bool(calls) is (arm == "full")
    assert (result["publication"] is None) is (arm == "frozen-skills")
    assert bool(result["active_skills"]) is (arm == "full")
    assert result["costs_unchanged"] and result["budget"]["committed_and_reserved"]["spend_microusd"] == 56


@pytest.mark.parametrize("flag", [True, 1, None, "true"])
def test_frozen_native_mode_requires_explicit_selected_checkpoint_profile(tmp_path, flag):
    with pytest.raises(Fault, match="FROZEN_NOTE_PROFILE_REQUIRED"):
        run(tmp_path / "absent.exe", tmp_path, frozen_notes=flag)
    assert not list(tmp_path.iterdir())


def test_native_result_decoder_never_accepts_issued_arguments_as_return():
    response = {"name": "artifact_write", "result": {"isError": True, "content": [{"type": "text", "text": "FROZEN_NOTE_CODE"}]}}
    assert native_call_results([{"type": "input_text", "text": "Script completed\nOutput:\n" + json.dumps(response)}]) == [response]
    assert native_call_results([{"type": "custom_tool_call", "input": json.dumps(response)}]) == []
