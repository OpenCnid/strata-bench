"""Frozen-skills packaging rules: synthetic authority and real CAS writes."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from mcbench.native_arm_policy import require_arm_policy
from mcbench.native_checkpoint import parse_retention_policy
from mcbench.native_note_policy import CLASSIFIER, classify_note, validate_tree
from mcbench.storage import Fault, Principal
from test_native_admission import begin, broker_meta
from test_native_checkpoint import admitted as checkpoint_admitted
from test_native_checkpoint import stage
from test_native_export import stopped


@pytest.fixture
def controlled(database, cas, tmp_path, example, configs):
    return checkpoint_admitted.__wrapped__(database, cas, tmp_path, example, configs,
        SimpleNamespace(param="frozen-skills"), note_classifier=True, model="gpt-6-luna")


@pytest.mark.parametrize("text", ["Health: 18. Nearby block: minecraft:stone.",
    "If hungry, inspect the available food.", "With a full inventory, return to the chest.",
    "# Notes\n- The crafting table is east.\n- Inspect its contents next.", "Coordinates: (12, 64, -3).",
    "Remember the recipe involved `minecraft:stone`.\nThe attempt failed.",
    "Observation receipt: cas:sha256:" + "a" * 64])
def test_ordinary_notes_and_implicit_prose_remain_permitted(text):
    assert classify_note("notes/observation.md", text) == {
        "classifier": CLASSIFIER, "verdict": "prose", "implicit_procedure_ambiguity": True}


@pytest.mark.parametrize("path,text", [
    ("notes/run.js", "Plain text."), ("handoff/task.json", '{"tool":"game"}'),
    ("notes/x.md", "```js\ntext(1)\n```"), ("notes/x.md", "~~~\nhello\n~~~"),
    ("notes/x.md", "    text(1)"), ("notes/x.md", "\ttext(1)"),
    ("notes/x.md", "#! /bin/sh\necho x"), ("notes/x.md", "<script>alert(1)</script>"),
    ("notes/x.md", "---\nname: hotkey\ntrigger: event\n---"),
    ("notes/x.md", "Use functions.exec to run it."), ("notes/x.md", "tools['game']"),
    ("notes/x.md", "const x = 1;"), ("notes/x.md", "def jump():\n return 1"),
    ("notes/x.md", "from os import environ"), ("notes/x.md", "if x:\n    pass"),
    ("notes/x.md", "text(1)"), ("notes/x.md", "python -c payload"),
    ("notes/x.md", 'globalThis["te"+"xt"](1)'), ("notes/x.md", 'store["key"]=1'),
    ("notes/x.md", 'Remember this payload: "arguments": {}'),
    ("notes/x.md", "ＡＬＬ＿ＴＯＯＬＳ"), ("notes/x.md", "foo\u200bbar"),
])
def test_executable_or_trigger_packaging_is_rejected(path, text):
    with pytest.raises(Fault, match="FROZEN_NOTE_FORMAT|FROZEN_NOTE_CODE"):
        classify_note(path, text)


@pytest.mark.parametrize("role", ["executor", "helper"])
def test_live_root_and_helper_writes_are_classified_before_cas_mutation(controlled, role):
    _, gate, broker, plan, request, _, _ = controlled
    begin(controlled, request("root-call"))
    if role == "helper":
        begin(controlled, request("child-call", "child", "/root/child", "root", child=True))
    metadata = broker_meta("child", "root", model=plan.model) if role == "helper" else broker_meta(model=plan.model)
    path = "results/advice.md" if role == "helper" else "notes/observation.md"
    before = gate.db.connection.execute("SELECT count(*) FROM objects").fetchone()[0]
    with pytest.raises(Fault, match="FROZEN_NOTE_CODE"):
        broker.call("artifact_write", {"path": path, "text": "```js\ntext(1)\n```", "expected_ref": None}, metadata)
    assert gate.db.connection.execute("SELECT count(*) FROM objects").fetchone()[0] == before
    assert gate.db.connection.execute("SELECT count(*) FROM broker_artifact_writes").fetchone()[0] == 0
    result = broker.call("artifact_write", {"path": path, "text": "The visible chest was empty.", "expected_ref": None}, metadata)
    assert broker.call("artifact_read", {"path": path}, metadata)["text"] == "The visible chest was empty."
    events = list(gate.db.connection.execute("SELECT body FROM outbox WHERE kind='broker.note_classified'"))
    assert len(events) == 1
    event = json.loads(events[0][0])
    assert event["ref"] == result["ref"] and event["classifier"] == CLASSIFIER and event["implicit_procedure_ambiguity"]
    write = gate.db.connection.execute("SELECT ref FROM broker_artifact_writes WHERE event=?", (event["source_event"],)).fetchone()
    assert write[0] == result["ref"]
    with pytest.raises(Fault, match="FROZEN_NOTE_CODE"):
        broker.call("artifact_write", {"path": path, "text": "tools.game", "expected_ref": result["ref"]}, metadata)
    assert broker.call("artifact_read", {"path": path}, metadata)["ref"] == result["ref"]


def test_frozen_skill_package_cannot_be_written_or_published(controlled):
    _, gate, broker, plan, request, _, _ = controlled
    begin(controlled, request("root-call"))
    for path in ("skills/new/SKILL.md", "skills/new/scripts/check.js", "skills/publish.json"):
        with pytest.raises(Fault, match="FROZEN_SKILL_WRITE"):
            broker.call("artifact_write", {"path": path, "text": "New procedure.", "expected_ref": None}, broker_meta(model=plan.model))
    assert gate.db.connection.execute("SELECT count(*) FROM broker_artifact_writes").fetchone()[0] == 0


def test_versioned_policy_is_strict_and_legacy_cannot_claim_campaign_coverage(controlled):
    _, gate, _, plan, _, _, put = controlled
    policy_ref = gate.db.checkpoint_fixture["agent"].memory_policy
    policy = gate.cas.json(Principal("operator", "operator"), "operator", policy_ref)
    parsed = parse_retention_policy(policy)
    assert parsed.note_classifier == CLASSIFIER
    for change in ({"note_classifier": "unknown"}, {"arm": "full"}, {"schema": "strata/NativeRetentionPolicy/1"}):
        with pytest.raises(ValidationError):
            parse_retention_policy(policy | change)
    assert require_arm_policy(gate.db.connection, gate.cas, plan.model_copy(update={"purpose": "campaign"})) == "frozen-skills"
    legacy = {k: v for k, v in policy.items() if k != "note_classifier"} | {
        "schema": "strata/NativeRetentionPolicy/1", "policy": "native-preregistered-retention-checkpoint/1"}
    assert parse_retention_policy(legacy).model_dump() == legacy
    ref = put(legacy)
    agent = gate.db.checkpoint_fixture["agent"].model_copy(update={"memory_policy": ref})
    gate.db.connection.execute("UPDATE native_retention_policies SET ref=?,agent_config=?", (ref, agent.model_dump_json()))
    gate.db.connection.execute("UPDATE campaigns SET agents=?", (json.dumps([agent.model_dump()]),))
    assert require_arm_policy(gate.db.connection, gate.cas, plan.model_copy(update={"purpose": "conformance"})) == "frozen-skills"
    with pytest.raises(Fault, match="NATIVE_NOTE_POLICY_REQUIRED"):
        require_arm_policy(gate.db.connection, gate.cas, plan.model_copy(update={"purpose": "campaign"}))


def test_checkpoint_tree_cannot_smuggle_a_changed_package_or_note(controlled):
    _, gate, _, _, _, _, _ = controlled
    operator = Principal("operator", "operator")
    fixture = gate.db.checkpoint_fixture
    policy = parse_retention_policy(gate.cas.json(operator, "operator", fixture["agent"].memory_policy))
    initial = fixture["initial"]
    validate_tree(policy, initial, initial, gate.cas)
    code = gate.cas.put(operator, "operator", "operator", b"text(1)")
    for path, error in (("notes/secret.md", "FROZEN_NOTE_CODE"), ("skills/new.md", "FROZEN_SKILL_WRITE"),
                        ("skills/seed.md", "FROZEN_SKILL_WRITE")):
        with pytest.raises(Fault, match=error):
            validate_tree(policy, initial | {path: code}, initial, gate.cas)


@pytest.mark.parametrize("boundary", ["episode", "recovery"])
def test_complete_versioned_checkpoint_retains_notes_but_activates_no_procedures(controlled, boundary, tmp_path):
    from mcbench.checkpoints import Checkpoints
    from mcbench.native_skill_activation import NativeSkillSets
    from mcbench.storage import CAS, Database
    from mcbench.native import NativeExec
    completed = stopped.__wrapped__(controlled)
    runtime, _, _ = completed
    before = runtime.budgets.status("a1")
    service, state, ref, manifest = stage(completed, boundary=boundary)
    fixture = runtime.db.checkpoint_fixture
    Checkpoints(runtime.db, runtime.cas).commit(fixture["config"], manifest, "operator")
    sets = NativeSkillSets(runtime)
    active = sets.load(sets.create(ref))
    assert not active["skills"]
    assert {"notes/root.md", "handoff/next.md"} <= active["workspace"].keys()
    assert not any(p.startswith("results/") for p in active["workspace"])
    assert state.session is None and state.runtime_cache is None
    database = Database(runtime.db.path)
    try:
        reopened = type(service)(NativeExec(database, CAS(database, runtime.cas.root), simulation=True))
        assert reopened.load(ref)[0] == state
    finally:
        database.close()
    assert runtime.budgets.status("a1") == before
    assert len(list(runtime.db.connection.execute("SELECT 1 FROM outbox WHERE kind='broker.note_classified'"))) == 3


def test_checkpoint_refuses_injected_unclassified_note(controlled):
    completed = stopped.__wrapped__(controlled)
    runtime, _, _ = completed
    namespace = runtime.db.connection.execute("SELECT namespace FROM broker_grants WHERE thread='root'").fetchone()[0]
    ref = runtime.cas.put(Principal(namespace, "executor"), namespace, "agent", b"text(1)", media_type="text/plain")
    runtime.db.connection.execute("UPDATE broker_files SET ref=? WHERE namespace=? AND path='notes/root.md'", (ref, namespace))
    with pytest.raises(Fault, match="FROZEN_NOTE_CODE"):
        stage(completed)
    assert runtime.db.connection.execute("SELECT count(*) FROM native_checkpoint_states").fetchone()[0] == 0


def test_exported_operator_policy_schemas_preserve_version_boundary():
    from mcbench.native_checkpoint import NativeRetentionPolicy, NativeRetentionPolicyV2
    for model in (NativeRetentionPolicy, NativeRetentionPolicyV2):
        path = Path(__file__).resolve().parents[1] / "schemas/v1/operator" / (model.__name__ + ".json")
        expected = model.model_json_schema() | {"$schema": "https://json-schema.org/draft/2020-12/schema"}
        assert json.loads(path.read_bytes()) == expected
        assert expected["additionalProperties"] is False
    assert "note_classifier" not in NativeRetentionPolicy.model_json_schema()["properties"]


def test_initial_note_classifier_refuses_changed_registration_without_policy_mutation(controlled):
    from mcbench.native_checkpoint import NativeCheckpointStates
    from mcbench.native import NativeExec
    _, gate, _, _, _, _, put = controlled
    fixture = gate.db.checkpoint_fixture
    bad = gate.cas.put(Principal("operator", "operator"), "operator", "operator", b"text(1)")
    baseline = put({"schema": "strata/NativeInitialArtifacts/1", "files": fixture["initial"] | {"notes/new.md": bad}})
    policy = gate.cas.json(Principal("operator", "operator"), "operator", fixture["agent"].memory_policy)
    updated = put(policy | {"initial_artifacts": baseline})
    agent = fixture["agent"].model_copy(update={"initial_skills": baseline, "memory_policy": updated})
    before = [tuple(row) for row in gate.db.connection.execute("SELECT * FROM native_retention_policies")]
    with pytest.raises(Fault, match="FROZEN_NOTE_CODE"):
        NativeCheckpointStates(NativeExec(gate.db, gate.cas, simulation=True)).register(fixture["config"], agent)
    assert [tuple(row) for row in gate.db.connection.execute("SELECT * FROM native_retention_policies")] == before
