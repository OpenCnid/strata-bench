"""Purpose/account gates with synthetic process and broker records, no provider."""

from types import SimpleNamespace

import pytest

from mcbench.budgets import DIMENSIONS
from mcbench.native_account_policy import require_native_account
from mcbench.storage import CAS, Database, Fault
from test_native import command, make_plan as _make_plan, runtime as _runtime
from test_native_admission import admitted as _admitted, begin, broker_meta

make_plan, runtime, admitted = _make_plan, _runtime, _admitted


@pytest.mark.parametrize("role", ["executor", "helper"])
@pytest.mark.parametrize("reserve_category", ["training", "evaluation"])
def test_evaluation_cannot_start_under_campaign_label(runtime, make_plan, tmp_path, role, reserve_category):
    runtime.budgets.create_account("evaluation", dict.fromkeys(DIMENSIONS, 100000), "c1", "a1",
                                   category="evaluation")
    plan, reserve = make_plan(role=role, parent="parent" if role == "helper" else None, account="evaluation")
    reserve = reserve.model_copy(update={"campaign_account": reserve_category})
    marker = tmp_path / "must-not-start"
    fixture = command("from pathlib import Path; Path(" + repr(str(marker)) + ").write_text('started')")
    before = runtime.budgets.status("evaluation")
    with pytest.raises(Fault, match="NATIVE_ACCOUNT_PURPOSE"):
        runtime.start(plan, reserve, fixture_argv=fixture)
    assert not marker.exists() and not runtime.live
    assert runtime.budgets.status("evaluation") == before
    assert runtime.db.connection.execute("SELECT count(*) FROM native_jobs").fetchone()[0] == 0
    assert runtime.db.connection.execute("SELECT count(*) FROM operations").fetchone()[0] == 0


@pytest.mark.parametrize("purpose,category,allowed", [
    ("campaign", "training", True), ("campaign", "development", True),
    ("campaign", "evaluation", False), ("campaign", None, False),
    ("conformance", "development", True), ("conformance", "training", False),
    ("conformance", "evaluation", False), ("development_piloting", "development", True),
    ("development_piloting", "evaluation", False), ("probe", "evaluation", False),
])
def test_durable_purpose_matrix_does_not_invent_probe_authority(runtime, purpose, category, allowed):
    runtime.budgets.create_account("aggregate", dict.fromkeys(DIMENSIONS, 100000), "*", category=None)
    runtime.budgets.create_account("leaf", dict.fromkeys(DIMENSIONS, 100000), "c1", "a1",
                                   parent="aggregate", category=category)
    plan = SimpleNamespace(purpose=purpose, account="leaf", campaign_id="c1", agent_id="a1")
    plan.operation_id = "not-yet-started"
    reserve = SimpleNamespace(campaign_account=category, campaign_id="c1", agent_id="a1",
                              operation_id=plan.operation_id)
    if allowed:
        require_native_account(runtime.db.connection, plan, reserve)
    else:
        with pytest.raises(Fault, match="NATIVE_ACCOUNT_PURPOSE|CONFORMANCE_ACCOUNT_REQUIRED"):
            require_native_account(runtime.db.connection, plan)


@pytest.mark.parametrize("change", ["leaf_campaign", "leaf_agent", "aggregate_category", "aggregate_campaign",
                                   "reservation_category"])
def test_scope_and_ancestry_are_read_from_actual_accounts(runtime, make_plan, change):
    runtime.budgets.create_account("aggregate", dict.fromkeys(DIMENSIONS, 100000), "*", category=None)
    runtime.budgets.create_account("leaf", dict.fromkeys(DIMENSIONS, 100000), "c1", "a1",
                                   parent="aggregate", category="training")
    plan, reserve = make_plan(account="leaf")
    db = runtime.db.connection
    if change == "leaf_campaign":
        db.execute("UPDATE accounts SET campaign='other' WHERE id='leaf'")
    elif change == "leaf_agent":
        db.execute("UPDATE accounts SET agent='other' WHERE id='leaf'")
    elif change == "aggregate_category":
        db.execute("UPDATE accounts SET category='evaluation' WHERE id='aggregate'")
    elif change == "aggregate_campaign":
        db.execute("UPDATE accounts SET campaign='other' WHERE id='aggregate'")
    else:
        reserve = reserve.model_copy(update={"campaign_account": "development"})
    with pytest.raises(Fault, match="NATIVE_ACCOUNT_SCOPE"):
        require_native_account(db, plan, reserve)


@pytest.mark.parametrize("helper", [False, True])
@pytest.mark.parametrize("category", ["evaluation", "development"])
def test_running_job_cannot_admit_new_root_or_helper_after_account_reclassification(admitted, helper, category):
    _, gate, _, _, request, prepare, _ = admitted
    begin(admitted, request("first"))
    db = gate.db.connection
    db.execute("UPDATE accounts SET category=?", (category,))
    before = {t: db.execute("SELECT count(*) FROM " + t).fetchone()[0] for t in (
        "operations", "native_participants", "native_request_admissions", "inference_attempts")}
    value = request("next", "child", "/root/child", "root", child=True) if helper else request("next")
    with pytest.raises(Fault, match="NATIVE_ACCOUNT_PURPOSE|NATIVE_ACCOUNT_SCOPE"):
        prepare(value)
    assert all(db.execute("SELECT count(*) FROM " + t).fetchone()[0] == count for t, count in before.items())


@pytest.mark.parametrize("category", ["evaluation", "development"])
def test_prepared_request_cannot_dispatch_after_account_reclassification(admitted, category):
    _, gate, _, _, request, prepare, _ = admitted
    value = request("one")
    prepare(value)
    before = gate.budgets.status("a1")
    gate.db.connection.execute("UPDATE accounts SET category=?", (category,))
    with pytest.raises(Fault, match="NATIVE_ACCOUNT_PURPOSE|NATIVE_ACCOUNT_SCOPE"):
        gate._begin("a1", value[0], value[1])
    assert gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0
    assert gate.budgets.status("a1")["committed_and_reserved"] == before["committed_and_reserved"]


@pytest.mark.parametrize("helper", [False, True])
def test_mislabeled_reservation_cannot_enroll_or_reserve_a_helper(admitted, helper):
    _, gate, _, _, request, prepare, _ = admitted
    begin(admitted, request("first"))
    a, r, raw, child = request("next", "child", "/root/child", "root", child=True) if helper else request("next")
    r = r.model_copy(update={"campaign_account": "evaluation"})
    before = gate.budgets.status("a1")
    count = gate.db.connection.execute("SELECT count(*) FROM native_participants").fetchone()[0]
    with pytest.raises(Fault, match="NATIVE_ACCOUNT_SCOPE"):
        prepare((a, r, raw, child))
    assert gate.db.connection.execute("SELECT count(*) FROM native_participants").fetchone()[0] == count
    assert gate.budgets.status("a1") == before


@pytest.mark.parametrize("helper", [False, True])
@pytest.mark.parametrize("category", ["evaluation", "development"])
def test_existing_broker_grants_stop_artifact_effects_after_restart(admitted, helper, category):
    _, gate, _, plan, request, _, _ = admitted
    begin(admitted, request("one"))
    if helper:
        begin(admitted, request("two", "child", "/root/child", "root", child=True))
    gate.db.connection.execute("UPDATE accounts SET category=?", (category,))
    before = gate.budgets.status("a1")["committed_and_reserved"]
    restored = Database(gate.db.path)
    try:
        from mcbench.broker import NativeBroker
        broker = NativeBroker(restored, CAS(restored, gate.cas.root), "job", plan.profile_digest())
        meta = broker_meta("child", "root") if helper else broker_meta()
        for name, args in (("artifact_list", {}), ("artifact_write", {
            "path": "results/private.md" if helper else "notes/private.md", "text": "probe canary",
            "expected_ref": None})):
            with pytest.raises(Fault, match="NATIVE_ACCOUNT_PURPOSE|NATIVE_ACCOUNT_SCOPE"):
                broker.call(name, args, meta)
        assert restored.connection.execute("SELECT count(*) FROM broker_files").fetchone()[0] == 0
    finally:
        restored.close()
    assert gate.budgets.status("a1")["committed_and_reserved"] == before


def test_permitted_campaign_still_adapts_with_local_artifacts_and_private_helper_output(admitted):
    _, _, broker, _, request, _, _ = admitted
    begin(admitted, request("one"))
    begin(admitted, request("two", "child", "/root/child", "root", child=True))
    for path, text in (("notes/local.md", "Observed ordinary gameplay."),
                       ("skills/local/SKILL.md", "A locally revised procedure.")):
        written = broker.call("artifact_write", {"path": path, "text": text, "expected_ref": None}, broker_meta())
        assert broker.call("artifact_read", {"path": path}, broker_meta())["ref"] == written["ref"]
    result = broker.call("artifact_write", {"path": "results/local.md", "text": "Local advice.",
        "expected_ref": None}, broker_meta("child", "root"))
    assert result["ref"]
    with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
        broker.call("artifact_read", {"path": "results/local.md"}, broker_meta())
