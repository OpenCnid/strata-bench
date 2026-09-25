"""Disposable identity/catalog preparation; no native or provider execution."""

import json

import pytest
from pydantic import ValidationError

from mcbench.budgets import DIMENSIONS
from mcbench.native import NativeLaunch
from mcbench.native_probe_binding import artifact_inputs, read_binding, require_binding_scope, require_probe_catalog
from mcbench.storage import Fault, Principal, canonical, digest
from strata_evaluator.native_probe_bindings import ProbeNativeBindings
from test_native import command, make_plan as _make_plan
from test_native_probe_views import pair_source as _pair_source, views as _views
from test_probe_pairs import EVALUATOR

make_plan, pair_source, views = _make_plan, _pair_source, _views


@pytest.fixture
def bindings(views, tmp_path):
    service, runtime = views
    service.prepare(EVALUATOR, "p1", tmp_path / "native", max_bytes=1024*1024)
    adapter = ProbeNativeBindings(service)
    destinations = {}
    pair, _ = service._source("p1")
    for arm in ("initial", "experienced"):
        d = {"job_id": arm+"-job", "campaign_id": arm+"-probe", "agent_id": "avatar",
             "account": arm+"-evaluation", "operation_id": arm+"-operation",
             "supply_helper_artifacts": pair["common"]["members"]["a1"]["self_play"]}
        destinations[arm] = {"a1": d}
        runtime.budgets.create_account(d["account"], dict.fromkeys(DIMENSIONS, 100000),
                                       d["campaign_id"], d["agent_id"], category="evaluation")
    return adapter, runtime, destinations


def plan_for(make_plan, adapter, refs, arm="experienced"):
    ref = refs[arm]["a1"]
    body = read_binding(adapter.db.connection, adapter.cas, ref)
    d = body.destination.model_dump()
    helpers = d.pop("supply_helper_artifacts")
    plan, reserve = make_plan(purpose="probe", probe_binding_ref=ref,
        helper_probe_binding_ref=ref if helpers else None, budget_mode="per_dispatch",
        **d, workspace=body.workspace, profile_directory=body.profile_directory,
        helper_limit=body.helper_limit, model=body.model, provider=body.provider, prompt=body.public_goal)
    if not helpers:
        from mcbench.native_broker_policy import NO_HELPER_POLICY
        plan = plan.model_copy(update={"broker_policy": NO_HELPER_POLICY})
    return plan, reserve


def catalog(plan, body):
    root = __import__("pathlib").Path(plan.workspace).as_posix()
    text = "<skills_instructions>\n- `r0` = `"+root+"/.agents/skills`\n"
    text += "\n".join(f"- {name}: {v.description} (file: r0/{name}/SKILL.md)" for name, v in body.catalog.items())
    return {"input": [{"type": "message", "role": "developer", "content": [
        {"text": text+"\n</skills_instructions>"}]}]}


@pytest.mark.parametrize("pair_source", [False, True, {"arm": "no-self-play"}, {"arm": "frozen-skills"},
                                       {"arm": "frozen-persistence"}], indirect=True)
def test_whole_pair_binding_uses_fresh_evaluation_identities_and_exact_role_catalogs(bindings, make_plan):
    adapter, runtime, destinations = bindings
    before = {d["a1"]["account"]: runtime.budgets.status(d["a1"]["account"]) for d in destinations.values()}
    refs = adapter.bind(EVALUATOR, "p1", destinations)
    for arm in refs:
        plan, _ = plan_for(make_plan, adapter, refs, arm)
        body = require_binding_scope(adapter.db.connection, adapter.cas, plan)
        for role in body.broker_files:
            files = artifact_inputs(adapter.db.connection, adapter.cas, plan, role)
            assert files == body.broker_files[role]
            assert not {"pair.json", "views.json", "source.json"} & set(files)
            if role == "helper":
                assert all(p.startswith(("initial/", "docs/", "supplied/", "active/")) for p in files)
            require_probe_catalog(adapter.db.connection, adapter.cas, plan, catalog(plan, body), role)
            files.clear()
            assert artifact_inputs(adapter.db.connection, adapter.cas, plan, role)
        assert plan.skill_activation_ref is None and plan.resume_component_ref is None
        assert plan.model_dump()["probe_binding_ref"] == refs[arm]["a1"]
        assert plan.profile_digest() != plan.model_copy(update={"probe_binding_ref": refs[
            "initial" if arm == "experienced" else "experienced"]["a1"]}).profile_digest()
    assert all(runtime.budgets.status(a) == value for a, value in before.items())
    assert adapter.db.connection.execute("SELECT count(*) FROM native_jobs").fetchone()[0] == 1  # stopped seed only
    with pytest.raises(Fault, match="NATIVE_PROBE_BINDING_CONSUMED"):
        adapter.bind(EVALUATOR, "p1", destinations)


@pytest.mark.parametrize("change", ["missing_arm", "missing_member", "duplicate_job", "same_campaign",
                                   "training_account", "source_campaign", "missing_helpers"])
def test_incomplete_or_reused_identity_refuses_without_partial_binding(bindings, change):
    adapter, _, d = bindings
    if change == "missing_arm":
        del d["initial"]
    elif change == "missing_member":
        d["initial"] = {}
    elif change == "duplicate_job":
        d["initial"]["a1"]["job_id"] = d["experienced"]["a1"]["job_id"]
    elif change == "same_campaign":
        d["initial"]["a1"]["campaign_id"] = d["experienced"]["a1"]["campaign_id"]
    elif change == "training_account":
        adapter.db.connection.execute("UPDATE accounts SET category='training' WHERE id='initial-evaluation'")
    elif change == "source_campaign":
        d["initial"]["a1"]["campaign_id"] = "c1"
        adapter.db.connection.execute("UPDATE accounts SET campaign='c1' WHERE id='initial-evaluation'")
    else:
        d["initial"]["a1"]["supply_helper_artifacts"] = False
    with pytest.raises(Fault, match="NATIVE_PROBE_"):
        adapter.bind(EVALUATOR, "p1", d)
    assert adapter.db.connection.execute("SELECT count(*) FROM native_probe_bindings").fetchone()[0] == 0
    assert adapter.db.connection.execute("SELECT count(*) FROM native_probe_binding_sets").fetchone()[0] == 0


@pytest.mark.parametrize("principal", [Principal("evaluation:other", "evaluator"), Principal("a1", "executor"),
                                      Principal("a1", "helper")])
def test_auth_refusal_precedes_view_verification_or_identity_registration(bindings, principal):
    adapter, _, d = bindings
    before = list(adapter.db.connection.iterdump())
    with pytest.raises(Fault, match="FORBIDDEN"):
        adapter.bind(principal, "p1", d)
    assert list(adapter.db.connection.iterdump()) == before


@pytest.mark.parametrize("change", ["wrong_job", "wrong_account", "root_as_helper", "prompt", "omitted_helper_set",
                                   "reclassified_account", "missing_sibling", "failed_views", "edited_source"])
def test_native_consumer_rejects_cross_scope_or_changed_committed_sources(bindings, make_plan, change):
    adapter, _, d = bindings
    refs = adapter.bind(EVALUATOR, "p1", d)
    plan, _ = plan_for(make_plan, adapter, refs)
    db = adapter.db.connection
    if change in {"wrong_job", "wrong_account", "root_as_helper", "prompt", "omitted_helper_set"}:
        updates = {"wrong_job": {"job_id": "foreign"}, "wrong_account": {"account": "initial-evaluation"},
            "root_as_helper": {"role": "helper"}, "prompt": {"prompt": "Hidden objective leaked"},
            "omitted_helper_set": {"helper_probe_binding_ref": None}}
        plan = plan.model_copy(update=updates[change])
    elif change == "reclassified_account":
        db.execute("UPDATE accounts SET category='training' WHERE id='experienced-evaluation'")
    elif change == "missing_sibling":
        db.execute("DELETE FROM native_probe_bindings WHERE arm='initial'")
    elif change == "failed_views":
        db.execute("UPDATE probe_native_views SET state='FAILED'")
    else:
        row = db.execute("SELECT plan FROM probe_pair_staging").fetchone()[0]
        value = json.loads(row)
        value["common"]["public_goal"] = "Changed goal"
        db.execute("UPDATE probe_pair_staging SET plan=?", (canonical(value).decode(),))
    with pytest.raises(Fault, match="NATIVE_PROBE_"):
        artifact_inputs(db, adapter.cas, plan, "executor")


@pytest.mark.parametrize("change", ["foreign_skill", "wrong_description", "wrong_path", "duplicate", "extra_block",
                                   "duplicate_root", "missing_skill"])
def test_native_catalog_requires_exact_reviewed_entries_including_no_host_skills(bindings, make_plan, change):
    adapter, _, d = bindings
    refs = adapter.bind(EVALUATOR, "p1", d)
    plan, _ = plan_for(make_plan, adapter, refs)
    body = read_binding(adapter.db.connection, adapter.cas, plan.probe_binding_ref)
    request = catalog(plan, body)
    part = request["input"][0]["content"][0]
    if change == "foreign_skill":
        part["text"] = part["text"].replace("</skills", "- operator: Hidden operator instructions (file: C:/operator/SKILL.md)\n</skills")
    elif change == "wrong_description":
        part["text"] = part["text"].replace(next(iter(body.catalog.values())).description, "Unreviewed text")
    elif change == "wrong_path":
        part["text"] = part["text"].replace("r0/learned-crafting/", "C:/foreign/")
    elif change == "duplicate":
        entry = next(line for line in part["text"].splitlines() if line.startswith("- learned-crafting:"))
        part["text"] = part["text"].replace("</skills", entry+"\n</skills")
    elif change == "duplicate_root":
        part["text"] = part["text"].replace("</skills", "- `r0` = `C:/other`\n</skills")
    elif change == "missing_skill":
        part["text"] = "\n".join(line for line in part["text"].splitlines() if not line.startswith("- learned-crafting:"))
    else:
        part["text"] += "<skills_instructions></skills_instructions>"
    with pytest.raises(Fault, match="NATIVE_PROBE_CATALOG"):
        require_probe_catalog(adapter.db.connection, adapter.cas, plan, request, "executor")


def test_valid_binding_still_cannot_start_a_native_process_or_reserve_costs(bindings, make_plan, tmp_path):
    adapter, runtime, d = bindings
    refs = adapter.bind(EVALUATOR, "p1", d)
    plan, reserve = plan_for(make_plan, adapter, refs)
    before = list(adapter.db.connection.iterdump())
    marker = tmp_path / "must-not-start"
    with pytest.raises(Fault, match="NATIVE_PROBE_LAUNCH_CUSTODY_REQUIRED"):
        runtime.start(plan, reserve, fixture_argv=command("from pathlib import Path; Path("+repr(str(marker))+").touch()"))
    assert not marker.exists() and not runtime.live
    assert list(adapter.db.connection.iterdump()) == before


@pytest.mark.parametrize("patch", [{"purpose": "campaign"}, {"session_storage": "private_profile"},
    {"resume_component_ref": "cas:sha256:"+"a"*64}, {"skill_activation_ref": "cas:sha256:"+"a"*64},
    {"epoch": 2}, {"probe_binding_ref": None}])
def test_probe_launch_schema_cannot_borrow_campaign_or_recovery_authority(bindings, make_plan, patch):
    adapter, _, d = bindings
    refs = adapter.bind(EVALUATOR, "p1", d)
    plan, _ = plan_for(make_plan, adapter, refs)
    with pytest.raises(ValidationError):
        NativeLaunch.model_validate(plan.model_dump() | patch)


def test_absent_extension_preserves_existing_plan_and_profile_hash(make_plan):
    plan, _ = make_plan()
    assert "probe_binding_ref" not in plan.model_dump() and "helper_probe_binding_ref" not in plan.model_dump()
    assert digest(plan.model_dump()) == digest(NativeLaunch.model_validate(plan.model_dump()).model_dump())
    assert plan.profile_digest() == NativeLaunch.model_validate(plan.model_dump()).profile_digest()


def test_aggregate_account_cannot_masquerade_as_a_fresh_leaf(bindings):
    adapter, runtime, d = bindings
    runtime.budgets.create_account("old-child", dict.fromkeys(DIMENSIONS, 1000), "initial-probe", "other",
                                   parent="initial-evaluation", category="evaluation")
    with pytest.raises(Fault, match="NATIVE_PROBE_IDENTITY_REUSED"):
        adapter.bind(EVALUATOR, "p1", d)
    assert adapter.db.connection.execute("SELECT count(*) FROM native_probe_bindings").fetchone()[0] == 0


def test_private_content_without_atomic_registration_has_no_native_authority(bindings, monkeypatch):
    adapter, _, d = bindings
    original, refs = adapter.cas.put, []
    def interrupted(*args, **kwargs):
        if refs:
            raise OSError("synthetic registration interruption")
        ref = original(*args, **kwargs)
        refs.append(ref)
        return ref
    monkeypatch.setattr(adapter.cas, "put", interrupted)
    with pytest.raises(OSError, match="synthetic registration interruption"):
        adapter.bind(EVALUATOR, "p1", d)
    assert len(refs) == 1
    with pytest.raises(Fault, match="NATIVE_PROBE_UNCOMMITTED"):
        read_binding(adapter.db.connection, adapter.cas, refs[0])
    assert adapter.db.connection.execute("SELECT count(*) FROM native_probe_binding_sets").fetchone()[0] == 0


def test_late_registration_failure_rolls_back_the_entire_roster(bindings, monkeypatch):
    adapter, _, d = bindings
    original = adapter.db.event
    def interrupted(db, kind, body):
        if kind == "probe.native_artifacts_bound":
            assert db.execute("SELECT count(*) FROM native_probe_bindings").fetchone()[0] == 2
            raise KeyboardInterrupt("synthetic journal interruption")
        return original(db, kind, body)
    monkeypatch.setattr(adapter.db, "event", interrupted)
    with pytest.raises(KeyboardInterrupt, match="synthetic journal interruption"):
        adapter.bind(EVALUATOR, "p1", d)
    assert adapter.db.connection.execute("SELECT count(*) FROM native_probe_bindings").fetchone()[0] == 0
    assert adapter.db.connection.execute("SELECT count(*) FROM native_probe_binding_sets").fetchone()[0] == 0


def test_changed_artifact_tree_fails_before_any_native_identity_registration(bindings):
    adapter, _, d = bindings
    row = adapter.db.connection.execute("SELECT target,plan FROM probe_native_views").fetchone()
    view = json.loads(row["plan"])["views"]["experienced"]["a1"]
    root = __import__("pathlib").Path(row["target"]) / view["directory"] / "workspace"
    (root / "notes/root.md").write_text("Unregistered probe canary", encoding="utf-8")
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE"):
        adapter.bind(EVALUATOR, "p1", d)
    assert adapter.db.connection.execute("SELECT state FROM probe_native_views").fetchone()[0] == "FAILED"
    assert adapter.db.connection.execute("SELECT count(*) FROM native_probe_bindings").fetchone()[0] == 0
