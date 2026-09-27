"""Production admission code with synthetic attestations in a temporary CAS.

These fixtures authorize no process and do not establish authentic conformance.
"""
import copy
import json
import shutil
import sqlite3
import time

import pytest
from typer.testing import CliRunner

from mcbench.cli import app
from mcbench.controller import Controller
from mcbench.records import AgentConfig, CampaignConfig
from mcbench.storage import Fault, canonical


@pytest.fixture
def admission(database, cas, operator, example, configs):
    refs = {}

    def put(name, value=None):
        raw = canonical({"fixture": name} if value is None else value)
        ref = cas.put(operator, "operator", "operator", raw)
        refs[name] = ref
        return ref

    c, agents = configs(n=2)
    c, agents = c.model_dump(), [a.model_dump() for a in agents]
    for field in ("training_team_limits", "evaluation_limits"):
        c[field]["spend_microusd"] = 1000  # Fixture ceiling, never an execution authorization.
    lock = example("PackLock") | {"is_example": False, "status": "sealed",
        "java": {"version": "fixture", "digest": "a" * 64},
        "launcher": {"version": "fixture", "digest": "b" * 64},
        "installed_root_digest": "c" * 64, "sealed_at": "2026-09-27T00:00:00Z"}
    for field in ("resolved_inventory", "launch_profile", "expert_assertions", "acquisition_report"):
        lock[field] = put("lock." + field)
    for field in ("distribution_refs", "harness_additions"):
        lock[field] = [put("lock." + field)]
    # Distribution evidence can include authorized binary assets.
    raw_ref = cas.put(operator, "operator", "operator", b"\x00binary fixture\xff", "application/octet-stream")
    lock["distribution_refs"].append(raw_ref)
    refs["lock.binary"] = raw_ref
    c["pack_lock"] = put("pack_lock", lock)
    protocol = example("EvaluationProtocol") | {"is_example": False, "system_digests": [c["system_digest"]]}
    for field in ("sealed_instances", "scorer", "artifact_projection", "control_keymap",
                  "sample_plan", "randomization_plan", "censoring_plan", "analysis_plan", "access_log"):
        protocol[field] = put("protocol." + field)
    c["protocol_ref"] = put("protocol_ref", protocol)
    for field in ("world_baseline", "information_policy", "communication_policy"):
        c[field] = put(field)
    c["backend"]["capability_manifest"] = put("backend.capability_manifest")
    for a in agents:
        for field in ("inference_config", "initial_skills", "learned_overlay", "memory_policy", "capability_profile"):
            a[field] = put(a["agent_id"] + "." + field)
    checks = {name: put("check." + name, {"result": "pass", "is_example": False,
                                        "system_digest": c["system_digest"]}) for name in (
        "official_acquisition", "body_conformance", "native_host", "isolation",
        "all_call_metering", "telemetry", "hard_budget_reservation")}
    profile = {"schema": "strata/AdmissionEvidence/1", "is_example": False,
               "system_digest": c["system_digest"], "pack_lock": c["pack_lock"],
               "expires_at_unix": 200, "checks": checks}
    c["runtime_profile"] = put("runtime_profile", profile)
    controller = Controller(database, cas=cas, clock=lambda: 100)
    return controller, c, agents, refs, put, lock, protocol, profile


def state(database):
    return {name: [tuple(r) for r in database.connection.execute('SELECT * FROM "' + name + '"')]
            for name in ("campaigns", "avatar_lanes", "workers", "reservations", "account_leases", "grants", "outbox")}


def test_complete_reference_fixture_is_read_only_and_preserves_inputs(admission, database):
    controller, c, agents, *_ = admission
    before, inputs = state(database), copy.deepcopy((c, agents))
    controller.validate_admission(c, agents)
    assert state(database) == before and (c, agents) == inputs
    # Optional overlays and control keymap can be absent, not unresolved.
    for a in agents:
        a["learned_overlay"] = None
    controller.validate_admission(c, agents)


REFERENCE_NAMES = ["pack_lock", "protocol_ref", "runtime_profile", "world_baseline", "information_policy",
    "communication_policy", "backend.capability_manifest", "lock.binary",
    *["lock." + f for f in ("resolved_inventory", "launch_profile", "expert_assertions", "acquisition_report",
                            "distribution_refs", "harness_additions")],
    *["protocol." + f for f in ("sealed_instances", "scorer", "artifact_projection", "control_keymap", "sample_plan",
                                "randomization_plan", "censoring_plan", "analysis_plan", "access_log")],
    *[a + "." + f for a in ("a1", "a2") for f in
      ("inference_config", "initial_skills", "learned_overlay", "memory_policy", "capability_profile")]]


@pytest.mark.parametrize("name", REFERENCE_NAMES)
def test_every_declared_reference_must_resolve_before_admission(admission, database, name):
    controller, c, agents, refs, *_ = admission
    controller.create(CampaignConfig.model_validate(c), [AgentConfig.model_validate(a) for a in agents])
    epoch = controller.claim(c["campaign_id"], "owner", 0)
    for target in ("PROVISIONING", "VALIDATING"):
        controller.transition(c["campaign_id"], "owner", epoch,
                              controller.status(c["campaign_id"])["revision"], target, "fixture")
    # The bytes still exist; a reference from another namespace confers no access.
    with database.transaction() as db:
        db.execute("UPDATE objects SET namespace='unrelated' WHERE namespace='operator' AND ref=?", (refs[name],))
    before = state(database)
    with pytest.raises(Fault, match="FORBIDDEN"):
        controller.admit(c["campaign_id"], "owner", epoch,
                         controller.status(c["campaign_id"])["revision"], "missing-worker", "fp",
                         {"bodies": 2, "memory_mib": 1, "disk_bytes": 1, "model_slots": 1})
    assert state(database) == before


@pytest.mark.parametrize("mutation,code", [
    ("missing-agent", "ROSTER_MISMATCH"), ("duplicate-agent", "ROSTER_MISMATCH"),
    ("wrong-agent", "ROSTER_MISMATCH"), ("wrong-system", "SYSTEM_MISMATCH"),
    ("same-account", "ACCOUNT_CONFLICT"), ("example-agent", "EXAMPLE_NOT_EXECUTABLE"),
    ("example-campaign", "EXAMPLE_NOT_EXECUTABLE"), ("unknown-field", "SCHEMA_UNSUPPORTED"),
])
def test_preflight_enforces_create_identity_checks(admission, database, mutation, code):
    controller, c, agents, *_ = admission
    if mutation == "missing-agent":
        agents.pop()
    elif mutation == "duplicate-agent":
        agents[1] = copy.deepcopy(agents[0])
    elif mutation == "wrong-agent":
        agents[1]["agent_id"] = "unrelated"
    elif mutation == "wrong-system":
        agents[1]["system_digest"] = "f" * 64
    elif mutation == "same-account":
        agents[1]["account_ref"] = agents[0]["account_ref"]
    elif mutation == "example-agent":
        agents[1]["is_example"] = True
    elif mutation == "example-campaign":
        c["is_example"] = True
    else:
        c["allow_admin"] = True
    before = state(database)
    with pytest.raises(Fault, match=code):
        controller.validate_admission(c, agents)
    assert state(database) == before


@pytest.mark.parametrize("component,patch,code", [
    ("protocol", {"system_digests": ["f" * 64]}, "PROTOCOL_MISMATCH"),
    ("protocol", {"is_example": True}, "PROTOCOL_MISMATCH"),
    ("protocol", {"schema": "mcbench/EvaluationProtocol/2"}, "SCHEMA_UNSUPPORTED"),
    ("lock", {"status": "candidate"}, "PACK_NOT_SEALED"),
    ("lock", {"is_example": True}, "PACK_NOT_SEALED"),
    ("lock", {"allow_missing": True}, "SCHEMA_UNSUPPORTED"),
    ("profile", {"pack_lock": "cas:sha256:" + "f" * 64}, "ADMISSION_EVIDENCE_REQUIRED"),
    ("profile", {"system_digest": "f" * 64}, "ADMISSION_EVIDENCE_REQUIRED"),
    ("profile", {"expires_at_unix": 100}, "ADMISSION_EVIDENCE_REQUIRED"),
    ("profile", {"checks": {}}, "ADMISSION_EVIDENCE_REQUIRED"),
])
def test_cross_record_refusal(admission, database, component, patch, code):
    controller, c, agents, _, put, lock, protocol, profile = admission
    field, record = {"protocol": ("protocol_ref", protocol), "lock": ("pack_lock", lock),
                     "profile": ("runtime_profile", profile)}[component]
    c[field] = put("bad-" + component, record | patch)
    before = state(database)
    with pytest.raises(Fault, match=code):
        controller.validate_admission(c, agents)
    assert state(database) == before


@pytest.mark.parametrize("raw", [b"[]", b"null", b"not json", b"\xff"])
def test_wrong_evidence_type_is_a_typed_refusal(admission, cas, operator, raw):
    controller, c, agents, *_ = admission
    c["runtime_profile"] = cas.put(operator, "operator", "operator", raw)
    with pytest.raises(Fault, match="EVIDENCE_SCHEMA_INVALID"):
        controller.validate_admission(c, agents)


@pytest.mark.parametrize("field", ["lock.binary", "backend.capability_manifest", "a1.learned_overlay"])
def test_hash_corruption_is_refused(admission, cas, field):
    controller, c, agents, refs, *_ = admission
    (cas.root / refs[field][11:]).write_bytes(b"changed bytes")
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE"):
        controller.validate_admission(c, agents)


@pytest.mark.parametrize("field", ["training_team_limits", "evaluation_limits"])
def test_reference_resolution_does_not_replace_spending_ceiling(admission, field):
    controller, c, agents, *_ = admission
    c[field]["spend_microusd"] = None
    with pytest.raises(Fault, match="SPENDING_CEILING_REQUIRED"):
        controller.validate_admission(c, agents)


@pytest.mark.parametrize("wrong_roster", [False, True])
def test_real_preflight_cli_resolves_fixture_without_admitting(admission, database, cas, tmp_path, wrong_roster):
    _, c, agents, _, put, _, _, profile = admission
    # The CLI uses the real clock, unlike the controller fixture's clock of 100.
    c["runtime_profile"] = put("cli-profile", profile | {"expires_at_unix": time.time() + 60})
    store = tmp_path / "cli-store"
    store.mkdir()
    with sqlite3.connect(store / "controller.sqlite") as copy_db:
        database.connection.backup(copy_db)
    shutil.copytree(cas.root, store / "objects")
    if wrong_roster:
        agents.pop()
    config_file, agents_file = tmp_path / "config.json", tmp_path / "agents.json"
    config_file.write_text(json.dumps(c), encoding="utf-8")
    agents_file.write_text(json.dumps(agents), encoding="utf-8")
    result = CliRunner().invoke(app, ["campaign", "preflight", "--config", str(config_file),
                                    "--agents", str(agents_file), "--store", str(store)])
    expected = ({"status": "blocked", "code": "ROSTER_MISMATCH", "started": False} if wrong_roster
                else {"status": "prerequisites_resolved", "admitted": False})
    assert result.exit_code == (2 if wrong_roster else 0), result.output
    assert json.loads(result.output) == expected
    with sqlite3.connect((store / "controller.sqlite").as_uri() + "?mode=ro", uri=True) as current:
        for table in ("campaigns", "reservations", "grants"):
            assert current.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0] == 0
