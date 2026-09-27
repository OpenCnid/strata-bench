"""Prepared disk + real broker operations with simulation-only grant enrollment.

No NativeLaunch, provider, Minecraft or qualified runtime is used here. This
tests the projection hook independently of the deliberately closed probe gate.
"""

import sqlite3
from pathlib import Path

import pytest

from mcbench.broker import BrokerGrant, NativeBroker
from mcbench.native_admission import NativeAdmission
from mcbench.native_probe_artifacts import project_probe_artifacts, validate_probe_bootstrap
from mcbench.native_probe_binding import artifact_inputs
from mcbench.launch_integrity import snapshot
from mcbench.storage import Fault, Principal, canonical, digest
from test_native_probe_bindings import (
    bindings as _bindings,
    make_plan as _make_plan,
    plan_for,
    views as _views,
)
from test_native_probe_views import pair_source as _pair_source
from test_probe_pairs import EVALUATOR

bindings, make_plan, views, pair_source = _bindings, _make_plan, _views, _pair_source


def pin(plan, tmp_path, mutate=None):
    manifest = {
        "schema": "strata/NativeBootstrap/1",
        "inventory": snapshot([], [Path(plan.workspace)]),
    }
    if mutate:
        mutate(manifest)
    path = tmp_path / (plan.job_id + "-bootstrap.json")
    path.write_bytes(canonical(manifest))
    return plan.model_copy(
        update={"bootstrap_manifest": str(path), "bootstrap_digest": digest(manifest)}
    )


@pytest.fixture
def projected(bindings, make_plan, tmp_path):
    adapter, runtime, destinations = bindings
    refs = adapter.bind(EVALUATOR, "p1", destinations)
    plan, _ = plan_for(make_plan, adapter, refs)
    plan = pin(plan, tmp_path)
    broker = NativeBroker(
        adapter.db, adapter.cas, plan.job_id, plan.profile_digest(), clock=lambda: 100
    )
    # Existing broker fixture admission is possible ONLY in simulation. No
    # NativeBrokerAdmission/1, running probe or funded dispatch is fabricated.
    evidence = adapter.cas.put(
        Principal("operator", "operator"), "operator", "operator", canonical({"is_example": True})
    )
    root = BrokerGrant.model_validate(
        {
            "schema": "strata/NativeBrokerGrant/1",
            "runtime_id": plan.job_id,
            "session_id": "root",
            "thread_id": "root",
            "parent_thread_id": None,
            "profile_digest": plan.profile_digest(),
            "model": plan.model,
            "role": "executor",
            "namespace": "probe:root",
            "campaign_id": plan.campaign_id,
            "agent_id": plan.agent_id,
            "epoch": 1,
            "depth": 0,
            "expires_unix_ms": 200000,
            "tool_calls": 100,
            "admission_ref": evidence,
        }
    )
    broker.admit(root)
    helper = root.model_copy(
        update={
            "thread_id": "helper",
            "parent_thread_id": "root",
            "role": "helper",
            "namespace": "probe:helper",
            "depth": 1,
        }
    )
    if plan.helper_limit:
        broker.admit(helper)
    return adapter, plan, broker, root, helper


def meta(grant):
    return {
        "callId": "probe-call",
        "threadId": grant.thread_id,
        "x-codex-turn-metadata": {
            "thread_id": grant.thread_id,
            "session_id": grant.session_id,
            "parent_thread_id": grant.parent_thread_id,
            "codex_version": "0.154.0-alpha.6.2",
            "model": grant.model,
            "thread_source": "user" if grant.role == "executor" else "subagent",
            "subagent_kind": "thread_spawn",
        },
    }


def files(adapter, grant):
    return {
        r["path"]: (r["ref"], r["immutable"])
        for r in adapter.db.connection.execute(
            "SELECT * FROM broker_files WHERE namespace=?", (grant.namespace,)
        )
    }


@pytest.mark.parametrize(
    "pair_source",
    [False, True, {"arm": "frozen-persistence"}, {"arm": "frozen-skills"}, {"arm": "no-self-play"}],
    indirect=True,
)
def test_admission_projection_exact_roles_preserve_local_writes_and_private_sources(
    projected, tmp_path
):
    adapter, plan, broker, root, helper = projected
    admission = NativeAdmission(adapter.db, adapter.cas, clock=lambda: 100)
    for grant in [root] + ([helper] if plan.helper_limit else []):
        expected = artifact_inputs(adapter.db.connection, adapter.cas, plan, grant.role)
        admission._project_skills(plan, grant, broker)
        assert {p: v[0] for p, v in files(adapter, grant).items()} == expected
        assert all(
            v[1]
            for p, v in files(adapter, grant).items()
            if p.startswith(("initial/", "docs/", "supplied/", "active/"))
        )
        assert not any(p.startswith((".agents/", "views.json", "pair.json")) for p in expected)
        for path in expected:
            value = broker.call("artifact_read", {"path": path}, meta(grant))
            assert value["ref"] == expected[path]
        with pytest.raises(Fault, match="IMMUTABLE|FORBIDDEN"):
            broker.call(
                "artifact_write",
                {
                    "path": "active/revisions.json",
                    "text": "changed",
                    "expected_ref": expected["active/revisions.json"],
                },
                meta(grant),
            )
        path = "notes/local.md" if grant.role == "executor" else "results/local.md"
        broker.call(
            "artifact_write",
            {"path": path, "text": "Probe-local observation.", "expected_ref": None},
            meta(grant),
        )
        before = files(adapter, grant)
        admission._project_skills(plan, grant, broker)
        assert files(adapter, grant) == before
    if plan.helper_limit:
        assert not any(
            p.startswith(("notes/", "handoff/", "skills/")) for p in files(adapter, helper)
        )
        with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
            broker.call("artifact_read", {"path": "notes/local.md"}, meta(helper))
    assert adapter.db.connection.execute("SELECT count(*) FROM native_jobs").fetchone()[0] == 1
    assert not adapter.db.connection.execute(
        "SELECT 1 FROM operations WHERE account LIKE '%-evaluation'"
    ).fetchone()
    (tmp_path / "projection-result.json").write_bytes(
        canonical(
            {
                "is_example": True,
                "job": plan.job_id,
                "root": files(adapter, root),
                "helper": files(adapter, helper) if plan.helper_limit else None,
                "native_launched": False,
                "evaluation_cost": 0,
            }
        )
    )


@pytest.mark.parametrize(
    "change",
    [
        "file",
        "catalog",
        "extra",
        "empty_dir",
        "missing_pin",
        "tree_omitted",
        "tree_member_omitted",
        "pin_hash",
        "pin_size",
        "duplicate_pin",
    ],
)
def test_changed_or_unpinned_prepared_view_refuses_before_projection(projected, tmp_path, change):
    adapter, plan, broker, root, _ = projected
    workspace = Path(plan.workspace)
    if change in {"file", "catalog", "extra", "empty_dir"}:
        if change == "file":
            (workspace / "initial/SKILL.md").write_text("Changed initial procedure")
        elif change == "catalog":
            next((workspace / ".agents/skills").rglob("SKILL.md")).write_text("Changed catalog")
        elif change == "extra":
            (workspace / "operator-secret.txt").write_text("synthetic private canary")
        else:
            (workspace / "unapproved-empty").mkdir()
    else:

        def mutate(m):
            inv = m["inventory"]
            if change == "missing_pin":
                inv["files"].pop()
            elif change == "tree_omitted":
                inv["trees"] = []
            elif change == "tree_member_omitted":
                inv["trees"][0]["files"].pop()
            elif change == "pin_hash":
                inv["files"][0]["sha256"] = "a" * 64
            elif change == "pin_size":
                inv["files"][0]["bytes"] += 1
            else:
                inv["files"].append(inv["files"][0])

        plan = pin(plan, tmp_path, mutate)
        # Inventory verification is independently tested before broker scope.
    with pytest.raises(Fault, match="PROBE_ARTIFACT_"):
        validate_probe_bootstrap(adapter.db.connection, adapter.cas, plan)
    assert not files(adapter, root)


@pytest.mark.parametrize("change", ["job", "agent", "profile", "model", "revoked", "foreign_grant"])
def test_projection_authenticates_before_copying_into_namespace(projected, change):
    adapter, plan, broker, root, helper = projected
    if change == "revoked":
        broker.revoke(root.thread_id)
    elif change == "foreign_grant":
        root = root.model_copy(update={"namespace": helper.namespace})
    else:
        field = {
            "job": "runtime_id",
            "agent": "agent_id",
            "profile": "profile_digest",
            "model": "model",
        }[change]
        root = root.model_copy(update={field: "a" * 64 if change == "profile" else "foreign"})
    before = list(adapter.db.connection.iterdump())
    with pytest.raises(Fault, match="PROBE_PROJECTION_SCOPE|BROKER_FORBIDDEN"):
        project_probe_artifacts(adapter.db, adapter.cas, plan, root, broker)
    assert list(adapter.db.connection.iterdump()) == before


@pytest.mark.parametrize(
    "failure", ["file_insert", "journal", "revoked_during_copy", "source_during_copy", "nonfresh"]
)
def test_projection_commit_is_atomic_and_revalidates_after_copy(projected, monkeypatch, failure):
    adapter, plan, broker, root, _ = projected
    if failure == "file_insert":
        adapter.db.connection.execute(
            "CREATE TRIGGER projection_failure BEFORE INSERT ON broker_files "
            "WHEN NEW.path='notes/root.md' BEGIN SELECT RAISE(ABORT,'synthetic projection crash'); END"
        )
    elif failure == "journal":
        original = adapter.db.event

        def event(db, kind, body):
            if kind == "native.probe_artifacts_projected":
                raise OSError("synthetic journal failure")
            return original(db, kind, body)

        monkeypatch.setattr(adapter.db, "event", event)
    elif failure == "nonfresh":
        broker.project(root.thread_id, "supplied/foreign.md", "Foreign canary")
    else:
        original = adapter.cas.put

        def put(*args, **kwargs):
            ref = original(*args, **kwargs)
            if args[1] == root.namespace:
                if failure == "revoked_during_copy":
                    broker.revoke(root.thread_id)
                else:
                    adapter.db.connection.execute("UPDATE probe_native_views SET state='FAILED'")
            return ref

        monkeypatch.setattr(adapter.cas, "put", put)
    before = files(adapter, root)
    with pytest.raises((Fault, OSError, sqlite3.IntegrityError)):
        project_probe_artifacts(adapter.db, adapter.cas, plan, root, broker)
    assert files(adapter, root) == before
    if adapter.db.connection.execute(
        "SELECT 1 FROM sqlite_master WHERE name='native_probe_projections'"
    ).fetchone():
        assert not adapter.db.connection.execute(
            "SELECT 1 FROM native_probe_projections"
        ).fetchone()
    assert not adapter.db.connection.execute(
        "SELECT 1 FROM outbox WHERE kind='native.probe_artifacts_projected'"
    ).fetchone()


def test_projection_replay_refuses_changed_immutable_or_marker(projected):
    adapter, plan, broker, root, _ = projected
    project_probe_artifacts(adapter.db, adapter.cas, plan, root, broker)
    adapter.db.connection.execute(
        "UPDATE broker_files SET immutable=0 WHERE namespace=? AND path='active/revisions.json'",
        (root.namespace,),
    )
    with pytest.raises(Fault, match="PROBE_PROJECTION_CHANGED"):
        project_probe_artifacts(adapter.db, adapter.cas, plan, root, broker)


def test_prepared_projection_does_not_open_native_probe_start(projected, example):
    adapter, plan, broker, root, _ = projected
    project_probe_artifacts(adapter.db, adapter.cas, plan, root, broker)
    from mcbench.records import BudgetLedger

    before = list(adapter.db.connection.iterdump())
    with pytest.raises(Fault, match="NATIVE_PROBE_LAUNCH_CUSTODY_REQUIRED"):
        adapter.views.pairs.sets.runtime.start(
            plan, BudgetLedger.model_validate(example("BudgetLedger"))
        )
    assert list(adapter.db.connection.iterdump()) == before
