"""Private controller/native repair writes; verification producers and resume stay separate."""

import json

from .control_lock import profile_operation
from .native_control_plan import NativeControlTarget, native_key
from .native_settings import NativeSnapshot
from .native_settings_effects import NativeCommitDecision, NativeRepairAdmission, NativeSettingsEffectsClient
from .storage import Principal, canonical, digest, require
from .worker_repair import WorkerRepairClient


class NativeRepairFlow:
    def __init__(self, repairs):
        self.repairs, self.controls, self.database = repairs, repairs.controls, repairs.database
        with self.database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS repair_native_writes (id TEXT, operation TEXT, "
                       "request TEXT NOT NULL, verification_digest TEXT, phase TEXT NOT NULL "
                       "CHECK(phase IN ('INTENT','UNKNOWN','CONFIRMED')), source_ref TEXT, "
                       "PRIMARY KEY(id,operation))")
            db.execute("CREATE TABLE IF NOT EXISTS repair_native_restarts (id TEXT PRIMARY KEY, request TEXT NOT NULL, "
                       "restart_binding TEXT NOT NULL, old_binding TEXT NOT NULL, old_connection TEXT NOT NULL, "
                       "checkpoint TEXT, phase TEXT NOT NULL CHECK(phase IN "
                       "('PREPARING','PREPARED','DETACHING','DETACHED','ATTACHING','ADOPTED')), "
                       "new_binding TEXT, paths TEXT, source_ref TEXT)")

    def _put(self, value):
        return self.repairs.controller.cas.put(Principal("operator", "operator"),
            self.repairs.controller.evidence_namespace, "operator", canonical(value))

    def _timeout(self, repair, cleanup=False):
        if cleanup:
            return 1000
        request = repair["request"]
        remaining = min(request["deadline_unix"] - self.repairs.clock(),
                        request["deadline_mono"] - self.repairs.monotonic(), 1.0)
        require(remaining >= 0.1, "REPAIR_DEADLINE_EXPIRED")
        return int(remaining * 1000)

    def _context(self, transaction, owner, epoch, worker, native, cleanup, *, restart_operation=False, observe=True):
        require(isinstance(native, NativeSettingsEffectsClient) and isinstance(worker, WorkerRepairClient),
                "REPAIR_PROFILE_MISMATCH")
        with self.database.transaction() as db:
            repair = self.repairs.status(transaction)
            self.repairs._owned(db, repair, owner, epoch, unexpired=not cleanup)
            require(repair["phase"] in ({"RECONFIGURING", "APPLYING", "AWAITING_OBSERVATION", "RECOVERY_REQUIRED"}
                    if cleanup else {"RECONFIGURING", "APPLYING", "AWAITING_OBSERVATION"}), "REPAIR_RECOVERY_REQUIRED")
            if not cleanup:
                self.repairs._budget(db, repair["request"])
                require(self.repairs.budgets.status(repair["request"]["account"])["dispatch_allowed"], "BUDGET_EXHAUSTED")
            handoff = db.execute("SELECT * FROM repair_native_handoffs WHERE id=?", (transaction,)).fetchone()
            worker_row = db.execute("SELECT * FROM repair_worker_handoffs WHERE id=?", (transaction,)).fetchone()
            require(handoff is not None and handoff["phase"] == "CONFIRMED"
                    and worker_row is not None and (cleanup or worker_row["phase"] == "CONFIRMED"), "REPAIR_NATIVE_EVIDENCE_REQUIRED")
            target = NativeControlTarget.model_validate_json(handoff["target"])
            admission = NativeRepairAdmission.model_validate_json(handoff["admission"])
            connection = native.connection.model_dump(mode="json")
            connection["bearer_token"] = native.connection.bearer_token.get_secret_value()
            restart = db.execute("SELECT * FROM repair_native_restarts WHERE id=?", (transaction,)).fetchone()
            binding = handoff["binding_digest"]
            if restart is not None:
                require(restart["old_binding"] == binding, "REPAIR_NOT_OWNED")
                require(cleanup or restart_operation or restart["phase"] == "ADOPTED", "REPAIR_RESTART_IN_PROGRESS")
                if restart["phase"] == "ADOPTED" and not restart_operation:
                    binding = restart["new_binding"]
            require(digest({"connection": connection, "target": target.model_dump()}) == binding
                    and native.settings_fingerprint == target.settings_fingerprint
                    and worker.binding_digest == worker_row["binding_digest"]
                    and admission.worker_plan.model_dump() == json.loads(worker_row["plan"]), "REPAIR_NOT_OWNED")
            control = self.controls.status(transaction)
            require(digest(control["plan"]) == admission.worker_plan.plan_digest == repair["request"]["plan_digest"],
                    "REPAIR_NOT_OWNED")
        if not cleanup and observe:
            # These calls observe existing holds. They never redispatch pause/bind.
            try:
                reply = worker.call("status", admission.worker_plan, timeout_ms=self._timeout(repair))
                require(reply.result.phase == "paused" and reply.result.inputs_released, "INPUT_RELEASE_REQUIRED")
                state = native.call("settings_repair_status", {"transaction_id": transaction},
                    expected_repair=admission, timeout_ms=self._timeout(repair))
                require(state["phase"] == "bound" and state["body_fingerprint"] == target.body_fingerprint,
                        "REPAIR_NATIVE_UNAVAILABLE")
            except BaseException:
                self.repairs._fail(transaction, "NATIVE_REPAIR_UNAVAILABLE")
                raise
        return repair, control, admission

    @staticmethod
    def _head(plan, raw, *, applied, active):
        head = NativeSnapshot.model_validate(raw)
        expected = plan["backup"] | ({name: change["after"] for name, change in plan["changes"].items()} if applied else {})
        require(set(head.bindings) == set(expected) and head.active_transaction == active, "REPAIR_STATE_MISMATCH")
        require(all(not b.persisted_ambiguous and b.runtime_value == b.persisted_value == native_key(expected[name])
                    for name, b in head.bindings.items()), "REPAIR_STATE_MISMATCH")
        return head, expected

    def apply(self, transaction, owner, epoch, worker, native):
        return self._write("apply", transaction, owner, epoch, worker, native)

    def commit(self, transaction, owner, epoch, worker, native, verification):
        return self._write("commit", transaction, owner, epoch, worker, native, verification)

    def rollback(self, transaction, owner, epoch, worker, native):
        return self._write("rollback", transaction, owner, epoch, worker, native)

    def _write(self, operation, transaction, owner, epoch, worker, native, verification=None):
        cleanup = operation == "rollback"
        if operation == "commit":
            verification = json.loads(canonical(verification))
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            repair, control, admission = self._context(transaction, owner, epoch, worker, native, cleanup)
            plan = control["plan"]
            old = self.database.connection.execute("SELECT * FROM repair_native_writes WHERE id=? AND operation=?",
                                                   (transaction, operation)).fetchone()
            if operation == "commit":
                require(control["phase"] in ({"verifying", "committed"} if old else {"verifying"}), "REPAIR_RECOVERY_REQUIRED")
                self.controls.validate_verification(plan, verification)
                verification_digest = digest(verification)
            else:
                verification_digest = None
            if old:
                require(old["verification_digest"] == verification_digest, "IDEMPOTENCY_CONFLICT")
                request = json.loads(old["request"])
            else:
                if operation == "apply":
                    require(control["phase"] == "planned", "REPAIR_RECOVERY_REQUIRED")
                    request = admission.patch.model_dump()
                elif operation == "commit":
                    applied = self.database.connection.execute("SELECT phase FROM repair_native_writes WHERE id=? AND operation='apply'",
                                                               (transaction,)).fetchone()
                    require(applied is not None and applied[0] == "CONFIRMED", "REPAIR_NATIVE_EVIDENCE_REQUIRED")
                    raw = native.call("settings_snapshot", {}, timeout_ms=self._timeout(repair))
                    head, _ = self._head(plan, raw, applied=True, active=transaction)
                    require(head.active_phase == "applied_pending_verification", "REPAIR_RECOVERY_REQUIRED")
                    proof = self._put({"schema": "strata/NativeControlVerification/1",
                        "is_example": self.repairs.controller.simulation, "transaction_id": transaction,
                        "plan_digest": digest(plan), "verification": verification, "native_head": raw,
                        "admission": admission.model_dump()})
                    request = NativeCommitDecision.model_validate({"schema": "strata/NativeSettingsCommitDecision/1",
                        "transaction_id": transaction, "plan_digest": digest(plan), "expected_revision": head.revision,
                        "expected_digest": head.digest, "verification_ref": proof}).model_dump()
                else:
                    require(control["phase"] in {"applying", "verifying", "committed", "failed"}, "REPAIR_RECOVERY_REQUIRED")
                    request = {"transaction_id": transaction}
                with self.database.transaction() as db:
                    self.repairs._owned(db, self.repairs.status(transaction), owner, epoch, unexpired=not cleanup)
                    db.execute("INSERT INTO repair_native_writes VALUES (?,?,?,?,'INTENT',NULL)",
                               (transaction, operation, canonical(request).decode(), verification_digest))
                    if operation == "apply":
                        changed = db.execute("UPDATE control_transactions SET phase='applying' WHERE id=? AND phase='planned'", (transaction,))
                        require(changed.rowcount == 1, "REVISION_CONFLICT")
                        db.execute("UPDATE repairs SET phase='APPLYING',forward_started=1 WHERE id=?", (transaction,))
                    self.database.event(db, "repair.native_write_intent", {"transaction_id": transaction,
                        "operation": operation, "request": request, "verification_digest": verification_digest})
            result = None
            try:
                rpc = "settings_" + ("commit_status" if operation == "commit" else "status") if old else "settings_" + operation
                result = native.call(rpc, {"transaction_id": transaction} if old else request,
                    timeout_ms=self._timeout(repair, cleanup),
                    **({"expected_commit": NativeCommitDecision.model_validate(request)} if old and operation == "commit" else {}))
                expected_phase = {"apply": "applied_pending_verification", "commit": "committed", "rollback": "rolled_back"}[operation]
                require(result["phase"] == expected_phase, "REPAIR_NATIVE_WRITE_UNCONFIRMED")
                raw = native.call("settings_snapshot", {}, timeout_ms=self._timeout(repair, cleanup))
                head, expected = self._head(plan, raw, applied=not cleanup, active=transaction if operation == "apply" else None)
                if not cleanup:
                    self._context(transaction, owner, epoch, worker, native, False)
                source = self._put({"schema": "strata/NativeRepairWriteWitness/1",
                    "is_example": self.repairs.controller.simulation, "transaction_id": transaction,
                    "operation": operation, "request": request, "result": result, "native_head": raw})
                receipt = {"revision": head.revision, "keymap_digest": digest(expected), "native_source_ref": source}
                if operation == "commit":
                    receipt["verification"] = verification
                with self.database.transaction() as db:
                    self.repairs._owned(db, self.repairs.status(transaction), owner, epoch, unexpired=not cleanup)
                    phase = {"apply": "verifying", "commit": "committed", "rollback": "rolled_back"}[operation]
                    db.execute("UPDATE control_transactions SET phase=?,receipt=? WHERE id=?",
                               (phase, canonical(receipt).decode(), transaction))
                    db.execute("UPDATE repair_native_writes SET phase='CONFIRMED',source_ref=? WHERE id=? AND operation=?",
                               (source, transaction, operation))
                    if operation != "apply":
                        db.execute("UPDATE repairs SET phase='AWAITING_OBSERVATION',result=? WHERE id=?",
                            (canonical({"settings_finished_unix": self.repairs.clock()}).decode(), transaction))
                    self.database.event(db, "repair.native_write_observed", {"transaction_id": transaction,
                        "operation": operation, "source_ref": source, "control_phase": phase})
                return {"control": self.controls.status(transaction), "repair": self.repairs.status(transaction), "source_ref": source}
            except BaseException:
                with self.database.transaction() as db:
                    db.execute("UPDATE repair_native_writes SET phase='UNKNOWN' WHERE id=? AND operation=?", (transaction, operation))
                    self.database.event(db, "repair.native_write_uncertain", {"transaction_id": transaction, "operation": operation})
                if result is not None or old and old["phase"] == "CONFIRMED":
                    self.repairs._fail(transaction, "NATIVE_REPAIR_WRITE_UNAVAILABLE")
                raise
