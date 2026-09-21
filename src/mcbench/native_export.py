"""Source-bound native component exports, not game checkpoints or restore permits."""

import json
from contextlib import nullcontext
from typing import Literal

from pydantic import Field

from .broker import MAX_TEXT, BrokerGrant
from .broker_lifecycle import require_drained
from .budgets import Budgets, vector
from .contracts import Digest, Id, Positive, Ref, Strict
from .native_cell_lifecycle import require_native_cells_drained
from .records import BudgetLedger
from .storage import Principal, canonical, digest, require, safe_relative

POLICY = "native-stopped-broker-component-export/1"
OPERATOR = Principal("operator", "operator")
MAX_METADATA = 4 * 1024 * 1024


class NativeStateV2(Strict):
    schema_: Literal["strata/NativeState/2"] = Field(alias="schema")
    policy: Literal["native-stopped-broker-component-export/1"]
    is_example: bool
    job_id: Id
    campaign_id: Id
    agent_id: Id
    source_epoch: Positive
    profile_digest: Digest
    source_digest: Digest
    source_ref: Ref
    accounting_ref: Ref
    root_artifacts: Ref
    helper_artifacts: dict[Id, Ref]
    resume_mode: Literal["fresh_handoff"]
    session: None
    runtime_cache: None
    cost_rollback: Literal[False]
    stage: Literal["stopped_native_component"]
    episode_retention_applied: Literal[False]
    restore_authorized: Literal[False]


def private_json(db, cas, ref):
    row = db.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?", (ref,)).fetchone()
    require(row is not None and row[0] == "operator", "NATIVE_EXPORT_PRIVATE")
    return json.loads(cas.read(OPERATOR, "operator", ref, max_bytes=MAX_METADATA))


def _inventory(db, cas, participant, grant):
    files = [dict(r) for r in db.execute("SELECT path,ref,immutable FROM broker_files WHERE namespace=? "
                                       "ORDER BY path", (grant.namespace,))]
    require(len(files) <= 1024, "ARTIFACT_QUOTA")
    folded = {r["path"].casefold() for r in files}
    require(len(folded) == len(files), "AMBIGUOUS_PATHS")
    for item in files:
        path = item["path"]
        relative = safe_relative(path)
        require(path.isascii() and len(path) <= 256 and len(relative.parts) > 1 and
                not any(str(p).casefold() in folded for p in relative.parents if str(p) != "."), "AMBIGUOUS_PATHS")
        prefix = relative.parts[0]
        immutable = prefix in {"initial", "docs", "supplied", "active"}
        allowed = {"initial", "docs", "supplied", "notes", "skills", "handoff", "active"} if grant.role == "executor" else {
            "initial", "docs", "supplied", "results", "active"}
        require(prefix in allowed and item["immutable"] in (0, 1) and bool(item["immutable"]) == immutable,
                "NATIVE_EXPORT_ARTIFACT_POLICY")
        require(not {p.casefold() for p in relative.parts} & {
            ".git", ".codex", ".ssh", ".aws", "auth.json", "credentials.json", "keys.json",
            "launcher_accounts.json", "launcher_msa_credentials.bin", "auth-cache", "auth_cache"},
            "SECRET_IN_SNAPSHOT")
        data = cas.read(Principal(grant.namespace, grant.role), grant.namespace, item["ref"], max_bytes=MAX_TEXT)
        data.decode("utf-8", errors="strict")
        require(prefix != "handoff" or len(data) <= 8000, "ARTIFACT_QUOTA")
        item.update(bytes=len(data), immutable=immutable, category={
            "notes": "note", "skills": "skill_draft", "active": "active_skill",
            "handoff": "handoff", "results": "helper_result"
        }.get(prefix, "immutable_projection"))
    return {"schema": "strata/NativeArtifactInventory/1", "thread_id": participant["thread"],
        "role": grant.role, "namespace": grant.namespace, "files": files, "activates_skills": False}


class NativeExports:
    def __init__(self, runtime):
        self.runtime, self.db, self.cas = runtime, runtime.db, runtime.cas
        require(runtime.namespace == "operator", "NATIVE_EXPORT_PRIVATE")
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_exports (job TEXT PRIMARY KEY, source_digest TEXT, ref TEXT)")

    def _capture(self, db, job):
        from .native import NativeLaunch
        row = db.execute("SELECT * FROM native_jobs WHERE id=?", (job,)).fetchone()
        require(row is not None and row["state"] == "FINALIZED" and job not in self.runtime.live and
                type(row["returncode"]) is int, "RUNTIME_NOT_QUIESCENT")
        plan = NativeLaunch.model_validate_json(row["plan"])
        require(plan.role == "executor" and plan.parent_job_id is None and plan.broker_policy is not None and
                plan.budget_mode == "per_dispatch", "NATIVE_EXPORT_PROFILE")
        require(db.execute("SELECT 1 FROM native_jobs WHERE parent=?", (job,)).fetchone() is None,
                "NATIVE_EXPORT_EXTERNAL_HELPERS")
        mode = db.execute("SELECT simulation FROM native_profile WHERE singleton=1").fetchone()
        require(mode is not None and mode[0] == int(self.runtime.simulation), "NATIVE_EXPORT_PROFILE")
        participants = [dict(r) for r in db.execute("SELECT * FROM native_participants WHERE job=? "
                                                   "ORDER BY depth,thread", (job,))]
        require(participants and sum(p["depth"] == 0 for p in participants) == 1 and
                all(p["state"] == "CLOSED" for p in participants), "NATIVE_EXPORT_PARTICIPANTS")
        attempts = [dict(r) for r in db.execute("SELECT a.operation,a.thread,a.request_digest,a.envelope,"
            "i.state,i.receipt_digest FROM native_request_admissions a LEFT JOIN inference_attempts i "
            "ON a.operation=i.operation WHERE a.job=? ORDER BY a.operation", (job,))]
        all_attempts = [r[0] for r in db.execute("SELECT operation FROM inference_attempts WHERE "
            "json_extract(request,'$.runtime_job_id')=? ORDER BY operation", (job,))]
        require(attempts and all(a["state"] == "SETTLED" and a["receipt_digest"] for a in attempts) and
                [a["operation"] for a in attempts] == all_attempts, "METERING_UNKNOWN")
        p_by_thread = {p["thread"]: p for p in participants}
        require({r[0] for r in db.execute("SELECT thread FROM broker_grants WHERE runtime=?", (job,))}
                == set(p_by_thread), "NATIVE_EXPORT_PARTICIPANTS")
        require(all(a["thread"] in p_by_thread and a["envelope"] == p_by_thread[a["thread"]]["envelope"]
                    for a in attempts), "NATIVE_EXPORT_PARTICIPANTS")
        envelopes = {p["envelope"] for p in participants}
        require(plan.operation_id in envelopes and len(envelopes) == len(participants), "OPERATION_LINEAGE")
        root = next(p for p in participants if p["depth"] == 0)
        require(root["parent"] is None and root["envelope"] == plan.operation_id and all(
            p["parent"] in p_by_thread and p_by_thread[p["parent"]]["depth"] == p["depth"] - 1
            for p in participants if p["depth"] > 0), "OPERATION_LINEAGE")
        parents = {p["envelope"]: p_by_thread[p["parent"]]["envelope"] if p["parent"] else None
                   for p in participants}
        require(not envelopes & {a["operation"] for a in attempts}, "OPERATION_LINEAGE")
        parents.update({a["operation"]: a["envelope"] for a in attempts})
        operation_ids = envelopes | {a["operation"] for a in attempts}
        operations = []
        ledgers = []
        for op in sorted(operation_ids):
            operation = db.execute("SELECT * FROM operations WHERE id=?", (op,)).fetchone()
            require(operation is not None and operation["account"] == plan.account and
                    operation["actual"] is not None and not operation["uncertain"], "METERING_UNKNOWN")
            require(operation["parent"] == parents[op], "OPERATION_LINEAGE")
            registered = db.execute("SELECT 1 FROM budget_envelopes WHERE operation=?", (op,)).fetchone()
            require(bool(registered) == (op in envelopes), "OPERATION_LINEAGE")
            operations.append(dict(operation))
            entries = db.execute("SELECT rowid cursor,body,digest FROM ledger WHERE "
                "json_extract(body,'$.operation_id')=? ORDER BY rowid", (op,)).fetchall()
            records = [BudgetLedger.model_validate_json(e["body"]) for e in entries]
            require(sum(r.posting == "reserve" for r in records) == 1 and
                    sum(r.posting == "settle" for r in records) == 1 and
                    all(r.posting in {"reserve", "settle"} for r in records), "NATIVE_EXPORT_LEDGER")
            for entry, record in zip(entries, records):
                require(entry["digest"] == digest({"account": plan.account, "body": record.model_dump()}) and
                        record.operation_id == op and record.parent_operation_id == parents[op] and
                        record.kind == operation["kind"] and record.campaign_id == plan.campaign_id and
                        record.agent_id == plan.agent_id and record.epoch == plan.epoch and
                        json.loads(operation["reserved" if record.posting == "reserve" else "actual"]) == vector(record),
                        "NATIVE_EXPORT_LEDGER")
                if record.raw_usage_ref:
                    private_json_or_bytes = db.execute("SELECT visibility FROM objects WHERE namespace='operator' "
                        "AND ref=?", (record.raw_usage_ref,)).fetchone()
                    require(private_json_or_bytes is not None and private_json_or_bytes[0] == "operator",
                            "NATIVE_EXPORT_PRIVATE")
                    self.cas.verify(OPERATOR, "operator", record.raw_usage_ref)
                ledgers.append({"cursor": entry["cursor"], "digest": entry["digest"], "record": record.model_dump()})
            if op in envelopes:
                settled = next(r for r in records if r.posting == "settle")
                require(all(v == 0 for v in vector(settled).values()) and settled.raw_usage_ref is not None,
                        "NATIVE_EXPORT_LEDGER")
            else:
                attempt = dict(db.execute("SELECT * FROM inference_attempts WHERE operation=?", (op,)).fetchone())
                reservation = next(r.model_dump() for r in records if r.posting == "reserve")
                request = json.loads(attempt["request"])
                admission = next(a for a in attempts if a["operation"] == op)
                require(attempt["account"] == plan.account and json.loads(attempt["reservation"]) == reservation and
                    attempt["fingerprint"] == digest({"account": plan.account, "attempt": request, "reserve": reservation})
                    and request["profile_digest"] == plan.profile_digest() and
                    request["request_digest"] == admission["request_digest"], "NATIVE_EXPORT_LEDGER")
                events = db.execute("SELECT body FROM outbox WHERE kind='inference.settled' AND "
                    "json_extract(body,'$.operation_id')=?", (op,)).fetchall()
                require(len(events) == 1 and json.loads(events[0][0]) == {
                    "operation_id": op, "provider_event_digest": attempt["provider_event"],
                    "receipt_digest": attempt["receipt_digest"]}, "NATIVE_EXPORT_LEDGER")
                valuation = db.execute("SELECT body FROM inference_valuations WHERE operation=?", (op,)).fetchone()
                require(self.runtime.simulation or valuation is not None, "VERSIONED_ESTIMATE_REQUIRED")
                admission.update(dispatch=attempt, valuation=json.loads(valuation[0]) if valuation else None)
        # A late reservation or accounting descendant cannot disappear from the
        # declared native request/envelope set simply because its response is absent.
        extra = db.execute("WITH RECURSIVE tree(id) AS (SELECT ? UNION SELECT o.id FROM operations o "
            "JOIN tree t ON o.parent=t.id) SELECT id FROM tree", (plan.operation_id,)).fetchall()
        require({r[0] for r in extra} == operation_ids, "NATIVE_EXPORT_LEDGER")
        closure = next(r["record"] for r in ledgers if r["record"]["operation_id"] == plan.operation_id and
                       r["record"]["posting"] == "settle")
        seal = private_json(db, self.cas, closure["raw_usage_ref"])
        require(seal.get("schema") == "strata/InferenceIngressSeal/1" and seal.get("is_example") is self.runtime.simulation
            and seal.get("job_id") == job and seal.get("profile_digest") == plan.profile_digest() and
            seal.get("attempt_ids") == all_attempts and seal.get("participant_threads") == sorted(p_by_thread) and
            all(seal.get(k) is True for k in ("process_tree_dead", "ingress_closed", "handlers_fenced")),
            "DISPATCH_SEAL_UNVERIFIED")
        if plan.ingress_policy is not None:
            ingress = db.execute("SELECT revoked FROM native_ingress WHERE job=?", (job,)).fetchone()
            require(ingress is not None and ingress[0] == 1, "INGRESS_NOT_FENCED")
        game_calls = [dict(r) for r in db.execute("SELECT * FROM broker_game_calls WHERE runtime=? "
                                                "ORDER BY thread,request", (job,))]
        require(all(c["state"] == "SETTLED" for c in game_calls), "NATIVE_EXPORT_GAME_UNKNOWN")
        require(all(c["thread"] in p_by_thread for c in game_calls), "NATIVE_EXPORT_PARTICIPANTS")
        inventories, summaries = {}, []
        for participant in participants:
            grant_row = db.execute("SELECT * FROM broker_grants WHERE runtime=? AND thread=?",
                                   (job, participant["thread"])).fetchone()
            require(grant_row is not None, "NATIVE_EXPORT_PARTICIPANTS")
            grant = BrokerGrant.model_validate_json(grant_row["body"])
            require(grant.runtime_id == job and grant.thread_id == participant["thread"] and
                grant_row["namespace"] == grant.namespace and grant_row["parent"] == participant["parent"] and
                grant_row["fingerprint"] == digest(grant.model_dump()) and
                grant.profile_digest == plan.profile_digest() and grant.epoch == plan.epoch and
                grant.campaign_id == plan.campaign_id and grant.agent_id == plan.agent_id and
                grant.parent_thread_id == participant["parent"] and grant.depth == participant["depth"] and
                grant.role == ("executor" if participant["depth"] == 0 else "helper"), "NATIVE_EXPORT_PARTICIPANTS")
            require_drained(db, job, participant["thread"])
            cells = require_native_cells_drained(db, self.cas, plan, participant["thread"])
            inventory = _inventory(db, self.cas, participant, grant)
            from .native_skill_activation import active_files, read_set, require_scope
            active_ref = plan.skill_activation_ref if grant.role == "executor" else plan.helper_skill_activation_ref
            expected_active = {}
            if active_ref:
                active = read_set(db, self.cas, active_ref)
                require_scope(active, plan)
                require(active["is_example"] is self.runtime.simulation, "NATIVE_SKILL_SCOPE")
                expected_active = active_files(active)
            require({f["path"]: f["ref"] for f in inventory["files"] if f["path"].startswith("active/")}
                    == expected_active, "NATIVE_SKILL_SCOPE")
            inventories[participant["thread"]] = inventory
            summaries.append({"participant": participant, "grant": dict(grant_row),
                              "inventory_digest": digest(inventory), "cells": cells})
        calls = [dict(r) for r in db.execute("SELECT o.cursor,o.body,l.state,l.ended_unix_ms,l.elapsed_ns,"
            "l.result_digest,l.fault FROM outbox o JOIN broker_call_lifecycle l ON o.cursor=l.event WHERE "
            "o.kind='broker.call' AND json_extract(o.body,'$.runtime')=? ORDER BY o.cursor", (job,))]
        require(all(json.loads(c["body"])["thread"] in p_by_thread for c in calls), "NATIVE_EXPORT_PARTICIPANTS")
        source = {"schema": "strata/NativeExportSource/1", "job": job, "plan_digest": digest(plan.model_dump()),
            "returncode": row["returncode"], "reason": row["reason"], "closure_ref": closure["raw_usage_ref"],
            "participants": summaries, "attempts": attempts, "operations": operations,
            "ledger": ledgers, "broker_calls": calls, "game_calls": game_calls,
            "account_identities": [dict(a) for a in Budgets.ancestors(db, plan.account)]}
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='broker_artifact_writes'").fetchone():
            writes = [dict(r) for r in db.execute("SELECT * FROM broker_artifact_writes WHERE runtime=? ORDER BY event", (job,))]
            # Legacy exports had no write provenance. Preserve their identity;
            # missing journals cannot later be invented to publish a revision.
            if writes:
                source["artifact_writes"] = writes
        return plan, source, inventories

    def export(self, job):
        with self.db.transaction() as db:
            plan, source, inventories = self._capture(db, job)
            source_digest = digest(source)
            old = db.execute("SELECT * FROM native_exports WHERE job=?", (job,)).fetchone()
            if old:
                require(old["source_digest"] == source_digest, "NATIVE_EXPORT_SOURCE_CHANGED")
                ref = old["ref"]
            else:
                ref = None
            accounts = []
            for account in Budgets.ancestors(db, plan.account):
                amounts, uncertain = Budgets.totals(db, account["id"])
                accounts.append({"identity": dict(account), "committed_and_reserved": amounts, "uncertain": uncertain})
            accounting = {"schema": "strata/NativeAccountingContinuity/1", "account": plan.account,
                "ledger_cursor": db.execute("SELECT coalesce(max(rowid),0) FROM ledger").fetchone()[0],
                "accounts": accounts, "cost_rollback": False, "grants_new_allowance": False,
                "usage_classes": sorted({a["valuation"]["kind"] if a["valuation"] else "synthetic_fixture"
                                         for a in source["attempts"]})}
        if ref:
            self.load(ref)
            return ref
        def put(body):
            return self.cas.put(OPERATOR, "operator", "operator", canonical(body), max_object_bytes=MAX_METADATA)
        inventory_refs = {thread: put(body) for thread, body in inventories.items()}
        root = next(thread for thread, value in inventories.items() if value["role"] == "executor")
        state = NativeStateV2.model_validate({"schema": "strata/NativeState/2", "policy": POLICY,
            "is_example": self.runtime.simulation, "job_id": job, "campaign_id": plan.campaign_id,
            "agent_id": plan.agent_id, "source_epoch": plan.epoch, "profile_digest": plan.profile_digest(),
            "source_digest": source_digest, "source_ref": put(source), "accounting_ref": put(accounting),
            "root_artifacts": inventory_refs[root], "helper_artifacts": {
                k: v for k, v in inventory_refs.items() if k != root}, "resume_mode": "fresh_handoff",
            "session": None, "runtime_cache": None, "cost_rollback": False,
            "stage": "stopped_native_component", "episode_retention_applied": False, "restore_authorized": False})
        ref = put(state.model_dump())
        with self.db.transaction() as db:
            _, current, _ = self._capture(db, job)
            require(digest(current) == source_digest, "NATIVE_EXPORT_SOURCE_CHANGED")
            old = db.execute("SELECT * FROM native_exports WHERE job=?", (job,)).fetchone()
            if old:
                require(old["source_digest"] == source_digest, "NATIVE_EXPORT_SOURCE_CHANGED")
                return old["ref"]
            db.execute("INSERT INTO native_exports VALUES(?,?,?)", (job, source_digest, ref))
            self.db.event(db, "native.export_committed", {"job": job, "policy": POLICY,
                "source_digest": source_digest, "ref": ref, "restore_authorized": False})
        return ref

    def load(self, ref):
        # Checkpoint commit may already hold the writer transaction so that the
        # source and the complete-set publication share one validation boundary.
        with (nullcontext(self.db.connection) if self.db.connection.in_transaction else self.db.transaction()) as db:
            state = NativeStateV2.model_validate(private_json(db, self.cas, ref))
            require(state.is_example is self.runtime.simulation, "NATIVE_EXPORT_PROFILE")
            stored = db.execute("SELECT * FROM native_exports WHERE job=?", (state.job_id,)).fetchone()
            require(stored is not None and stored["ref"] == ref and stored["source_digest"] == state.source_digest,
                    "NATIVE_EXPORT_UNCOMMITTED")
            plan, current, inventories = self._capture(db, state.job_id)
            require(digest(current) == state.source_digest and
                digest(private_json(db, self.cas, state.source_ref)) == state.source_digest and
                state.campaign_id == plan.campaign_id and state.agent_id == plan.agent_id and
                state.source_epoch == plan.epoch and state.profile_digest == plan.profile_digest(),
                "NATIVE_EXPORT_SOURCE_CHANGED")
            for thread, inventory in inventories.items():
                inventory_ref = state.root_artifacts if inventory["role"] == "executor" else state.helper_artifacts.get(thread)
                require(private_json(db, self.cas, inventory_ref) == inventory, "NATIVE_EXPORT_SOURCE_CHANGED")
            require(set(state.helper_artifacts) == {k for k, v in inventories.items() if v["role"] == "helper"},
                    "NATIVE_EXPORT_PARTICIPANTS")
            accounting = private_json(db, self.cas, state.accounting_ref)
            require(accounting.get("schema") == "strata/NativeAccountingContinuity/1" and
                accounting.get("account") == plan.account and accounting.get("cost_rollback") is False and
                accounting.get("grants_new_allowance") is False, "NATIVE_EXPORT_LEDGER")
            return state
