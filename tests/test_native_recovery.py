"""Recovery projection from stopped synthetic state; no game/model dispatch."""

import pytest

from mcbench.broker import BrokerGrant, NativeBroker
from mcbench.native_recovery import NativeRecovery
from mcbench.storage import Fault, Principal, canonical
from test_native_broker import meta
from test_native_game_retention import package as _package, stopped_retention as _stopped_retention

package = _package
stopped_retention = _stopped_retention


@pytest.fixture
def recovery(stopped_retention):
    retention, runtime, source = stopped_retention
    report = retention.finish()
    plan = source.model_copy(update={"job_id": "resume", "operation_id": "resume-envelope",
        "epoch": 2, "purpose": "conformance", "provider": "strata_local_fixture",
        "resume_component_ref": report["component_ref"], "config_overrides": source.config_overrides |
        {"model_providers.strata_local_fixture.base_url": "http://127.0.0.1:12345/v1"}})
    service = NativeRecovery(runtime)
    broker = NativeBroker(runtime.db, runtime.cas, plan.job_id, plan.profile_digest(), clock=lambda: 100)
    evidence = runtime.cas.put(Principal("operator", "operator"), "operator", "operator", canonical({"is_example": True}))
    root = BrokerGrant.model_validate({"schema": "strata/NativeBrokerGrant/1", "runtime_id": plan.job_id,
        "session_id": "root", "thread_id": "root", "parent_thread_id": None,
        "profile_digest": plan.profile_digest(), "model": plan.model, "role": "executor",
        "namespace": "resumed-root", "campaign_id": plan.campaign_id, "agent_id": plan.agent_id,
        "epoch": 2, "depth": 0, "expires_unix_ms": 200000, "tool_calls": 100, "admission_ref": evidence})
    broker.admit(root)
    child = root.model_copy(update={"thread_id": "child", "parent_thread_id": "root", "role": "helper",
                                   "depth": 1, "namespace": "resumed-child"})
    broker.admit(child)
    return runtime, service, plan, broker, root, child


def test_root_restores_once_helpers_stay_empty_and_costs_stay_consumed(recovery):
    runtime, service, plan, broker, root, child = recovery
    before = runtime.budgets.status("a1")
    service.project(plan, child, broker)
    assert broker.call("artifact_list", {}, meta("child"))["files"] == []
    service.project(plan, root, broker)
    note = broker.call("artifact_read", {"path": "notes/root.md"}, meta())
    assert note["text"] == "Before the stop."
    broker.call("artifact_write", {"path": "notes/root.md", "text": "After recovery.", "expected_ref": note["ref"]}, meta())
    service.project(plan, root, broker)
    assert broker.call("artifact_read", {"path": "notes/root.md"}, meta())["text"] == "After recovery."
    with pytest.raises(Fault, match="BROKER_WRITE_FORBIDDEN"):
        broker.call("artifact_write", {"path": "initial/skill.md", "text": "overwrite", "expected_ref": None}, meta())
    with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
        broker.call("artifact_read", {"path": "notes/root.md"}, meta("child"))
    assert runtime.budgets.status("a1") == before
    assert runtime.db.connection.execute("SELECT count(*) FROM native_recovery_projections").fetchone()[0] == 1


@pytest.mark.parametrize("field,value,code", [
    ("epoch", 1, "NATIVE_RECOVERY_SCOPE"), ("account", "fresh", "NATIVE_RECOVERY_SCOPE"),
    ("campaign_id", "other", "NATIVE_RECOVERY_SCOPE"), ("agent_id", "other", "NATIVE_RECOVERY_SCOPE"),
    ("model", "different", "NATIVE_RECOVERY_SCOPE"), ("job_id", "job", "NATIVE_RECOVERY_SCOPE"),
    ("purpose", "campaign", "NATIVE_RECOVERY_PROFILE"), ("provider", "openai", "NATIVE_RECOVERY_PROFILE"),
    ("role", "helper", "NATIVE_RECOVERY_PROFILE"),
    ("skill_activation_ref", "cas:sha256:" + "a" * 64, "NATIVE_RECOVERY_PROFILE")])
def test_wrong_recovery_scope_cannot_seed(recovery, field, value, code):
    runtime, service, plan, broker, root, _ = recovery
    with pytest.raises(Fault, match=code):
        service.project(plan.model_copy(update={field: value}), root, broker)
    assert runtime.db.connection.execute("SELECT count(*) FROM broker_files WHERE namespace='resumed-root'").fetchone()[0] == 0


def test_unqualified_real_provider_and_nonlocal_endpoint_reject(recovery):
    runtime, service, plan, _, _, _ = recovery
    runtime.simulation = False
    with pytest.raises(Fault, match="NATIVE_RECOVERY_PROFILE"):
        service.validate_launch(plan)
    runtime.simulation = True
    for endpoint in ("https://api.example.invalid/v1", "http://127.0.0.1:12345/v1?redirect=other"):
        with pytest.raises(Fault, match="NATIVE_RECOVERY_PROFILE"):
            service.validate_launch(plan.model_copy(update={"config_overrides": plan.config_overrides |
                {"model_providers.strata_local_fixture.base_url": endpoint}}))


def test_later_state_and_nonempty_destination_are_not_silently_replaced(recovery):
    runtime, service, plan, broker, root, _ = recovery
    broker.project("root", "docs/existing.md", "Later content.")
    with pytest.raises(Fault, match="NATIVE_RECOVERY_NOT_FRESH"):
        service.project(plan, root, broker)
    runtime.db.connection.execute("INSERT INTO native_jobs(id,campaign,agent,role) VALUES('later','c1','a1','executor')")
    with pytest.raises(Fault, match="NATIVE_LATER_STATE"):
        service.validate_launch(plan)


def test_absent_resume_extension_preserves_historical_plan_and_profile(stopped_retention):
    _, _, plan = stopped_retention
    assert "resume_component_ref" not in plan.model_dump()
    assert plan.model_copy(update={"resume_component_ref": None}).profile_digest() == plan.profile_digest()


def test_existing_retention_attaches_without_reregistering_or_refunding(recovery, stopped_retention):
    retention = stopped_retention[0]
    runtime, _, plan, _, _, _ = recovery
    before = runtime.budgets.status("a1")
    count = runtime.db.connection.execute("SELECT count(*) FROM native_retention_policies").fetchone()[0]
    retention.attach_existing(runtime, plan)
    assert retention.plan == plan
    assert runtime.budgets.status("a1") == before
    assert runtime.db.connection.execute("SELECT count(*) FROM native_retention_policies").fetchone()[0] == count
