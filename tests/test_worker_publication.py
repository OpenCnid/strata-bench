"""Synthetic substitution/failure cases; the connected JVM test checks transport."""

import copy

import pytest

from mcbench.storage import Fault, digest
from mcbench.worker_publication import (WorkerControlPublication, WorkerControlPublicationGrant,
    WorkerControlPublicationState, WorkerPublicationClient, WorkerPublicationUnknown, WorkerRepairAccounting)
from mcbench.worker_resume import WorkerResumeClient, WorkerResumeGrant
from test_worker_resume import state


def publication(example):
    resumed = state(example)
    d = resumed["decision"]
    return {"schema": "strata/WorkerControlPublication/1", "policy": "verified-controls-after-settlement/1",
        "publication_id": "publication", "worker_plan": d["worker_plan"], "resume_digest": digest(d),
        "control_revision": d["expected_revision"], "keymap_digest": "d" * 64,
        "verification_ref": d["verification_ref"], "settlement_ref": "cas:sha256:" + "e" * 64,
        "primitive_events": 7}


def measured(example):
    d = state(example)["decision"]
    source = "native:" + "a" * 64 + ":" + "b" * 64
    return {"schema": "strata/WorkerRepairAccounting/1", "policy": "durable-worker-charge-interval/1",
        "worker_plan": d["worker_plan"], "clock_id": "worker-clock", "resume_digest": digest(d),
        "opening": {"cursor": 2, "mono_ms": 100, "unix_ms": 100000, "primitive_events": 2, "sources": {source: 2}},
        "closing": {"cursor": 9, "mono_ms": 125, "unix_ms": 100025, "primitive_events": 7, "sources": {source: 7}},
        "charged_primitive_events": 5, "elapsed_ms": 25, "complete_repair_accounting": False,
        "avatar_ticks": None, "model_usage": None, "publication_tail_included": False}


@pytest.mark.parametrize("path,value", [
    ("complete_repair_accounting", True), ("complete_repair_accounting", 0), ("avatar_ticks", 0),
    ("model_usage", {}), ("publication_tail_included", True), ("opening.primitive_events", 1),
    ("closing.primitive_events", 8), ("charged_primitive_events", 7), ("elapsed_ms", 24),
    ("closing.cursor", 2), ("closing.mono_ms", 99), ("opening.sources", {}),
    ("closing.sources", {"private-path": 7}), ("clock_id", ""), ("extra", True),
])
def test_measured_interval_rejects_invented_costs_and_wrong_arithmetic(example, path, value):
    valid = measured(example)
    assert WorkerRepairAccounting.model_validate(valid).charged_primitive_events == 5
    target = valid
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    with pytest.raises(ValueError):
        WorkerRepairAccounting.model_validate(valid)


def test_matching_total_cannot_hide_a_refunded_native_source(example):
    value = measured(example)
    key = next(iter(value["opening"]["sources"]))
    value["closing"]["sources"] = {key: 1, "native:" + "c" * 64 + ":" + "d" * 64: 6}
    with pytest.raises(ValueError, match="REPAIR_ACCOUNTING_MISMATCH"):
        WorkerRepairAccounting.model_validate(value)


@pytest.mark.parametrize("path,value", [
    ("published", 1), ("primitive_events", 6), ("observation.is_example", True),
    ("observation.keymap_digest", None), ("observation.control_revision", 0),
    ("observation.agent_id", "sibling"), ("observation.age_at_send_ms", 2001),
])
def test_publication_requires_matching_public_control_observation(example, path, value):
    d = publication(example)
    o = state(example)["observation"] | {"control_revision": d["control_revision"], "keymap_digest": d["keymap_digest"]}
    result = {"schema": "strata/WorkerControlPublicationState/1", "decision": d, "observation": o,
        "primitive_events": 7, "published": True}
    assert WorkerControlPublicationState.model_validate(result).published
    target = result
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    with pytest.raises(ValueError):
        WorkerControlPublicationState.model_validate(result)


def clients():
    resume = WorkerResumeClient(WorkerResumeGrant.model_validate({"schema": "strata/WorkerResumeGrant/1",
        "policy": "operator-owned-settings-resume/1", "repair_binding_digest": "a" * 64, "restart_binding_digest": "b" * 64,
        "url": "http://127.0.0.1:1234/v1/resume", "token": "c" * 64,
        "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "lease_id": "lease"}))
    grant = WorkerControlPublicationGrant.model_validate({"schema": "strata/WorkerControlPublicationGrant/1",
        "policy": "verified-controls-after-settlement/1", "resume_binding_digest": resume.binding_digest,
        "url": "http://127.0.0.1:1235/v1/publication", "token": "d" * 64,
        "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "lease_id": "lease"})
    return WorkerPublicationClient(grant), resume


def test_publication_grant_binds_exact_private_resume_capability():
    publisher, resume = clients()
    publisher.validate_resume(resume)
    other = copy.copy(resume)
    other.binding_digest = "0" * 64
    with pytest.raises(Fault, match="RESUME_WORKER_MISMATCH"):
        publisher.validate_resume(other)


def test_unusable_publish_reply_is_unknown_and_never_replayed(example, monkeypatch):
    publisher, _ = clients()
    calls = []
    def unusable(*args):
        calls.append(args)
        return {"schema": "strata/WorkerControlPublicationState/1", "published": True}
    monkeypatch.setattr(publisher, "_call", unusable)
    decision = WorkerControlPublication.model_validate(publication(example))
    with pytest.raises(WorkerPublicationUnknown):
        publisher.publish("publish", decision)
    assert len(calls) == 1 and calls[0][0] == "publish"
