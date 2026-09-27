"""Durable controller restart dispatch and replacement adoption; never input resume."""

from pathlib import Path

from .control_lock import profile_operation
from .forge_guard import implementation_digest
from .native_control_plan import NativeControlTarget
from .native_repair_flow import NativeRepairFlow
from .native_restart import NativeRestartCheckpoint, NativeRestartRequest
from .native_settings_effects import NativeSettingsEffectsClient
from .storage import canonical, digest, require
from .worker_restart import ReplacementPaths, WorkerRestartClient


def descriptor(native):
    value = native.connection.model_dump(mode="json")
    value["bearer_token"] = native.connection.bearer_token.get_secret_value()
    return value


class NativeRepairRestart:
    def __init__(self, repairs):
        self.flow = NativeRepairFlow(repairs)
        self.repairs, self.database, self.controls = repairs, repairs.database, repairs.controls

    def _row(self, transaction):
        return self.database.connection.execute("SELECT * FROM repair_native_restarts WHERE id=?", (transaction,)).fetchone()

    def _context(self, transaction, owner, epoch, worker, restart, original):
        repair, control, admission = self.flow._context(transaction, owner, epoch, worker, original, False,
                                                       restart_operation=True, observe=False)
        require(control["phase"] == "verifying", "REPAIR_RECOVERY_REQUIRED")
        require(isinstance(restart, WorkerRestartClient), "RESTART_WORKER_MISMATCH")
        restart.validate_worker(worker, admission.worker_plan)
        row = self._row(transaction)
        if row:
            require(row["restart_binding"] == restart.binding_digest
                    and row["old_connection"] == digest(descriptor(original)), "REPAIR_NOT_OWNED")
        return repair, control, admission, row

    def _timeout(self, repair, cap=6.0):
        request = repair["request"]
        remaining = min(request["deadline_unix"] - self.repairs.clock(),
                        request["deadline_mono"] - self.repairs.monotonic(), cap)
        require(remaining >= .1, "REPAIR_DEADLINE_EXPIRED")
        return int(remaining * 1000)

    def _phase(self, transaction, owner, epoch, phase, **values):
        require(set(values) <= {"checkpoint", "new_binding", "paths", "source_ref"}, "RESTART_STATE_INVALID")
        with self.database.transaction() as db:
            self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
            columns = {"phase": phase, **values}
            db.execute("UPDATE repair_native_restarts SET " + ",".join(k + "=?" for k in columns) + " WHERE id=?",
                       (*columns.values(), transaction))
            self.database.event(db, "repair.restart_phase", {"transaction_id": transaction, "phase": phase, **values})

    def prepare_and_detach(self, transaction, owner, epoch, worker, restart, original, restart_id):
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            repair, control, admission, row = self._context(transaction, owner, epoch, worker, restart, original)
            if row is None:
                self.flow._context(transaction, owner, epoch, worker, original, False)
                applied = self.database.connection.execute("SELECT phase FROM repair_native_writes WHERE id=? AND operation='apply'",
                                                           (transaction,)).fetchone()
                require(applied is not None and applied[0] == "CONFIRMED", "REPAIR_NATIVE_EVIDENCE_REQUIRED")
                head, _ = self.flow._head(control["plan"], original.call("settings_snapshot", {},
                    timeout_ms=self._timeout(repair, 1)), applied=True, active=transaction)
                request = NativeRestartRequest.model_validate({"schema": "strata/NativeSettingsRestartRequest/1",
                    "transaction_id": transaction, "plan_digest": admission.worker_plan.plan_digest, "restart_id": restart_id,
                    "expected_revision": head.revision, "expected_digest": head.digest})
                handoff = self.database.connection.execute("SELECT binding_digest FROM repair_native_handoffs WHERE id=?", (transaction,)).fetchone()
                with self.database.transaction() as db:
                    self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                    db.execute("INSERT INTO repair_native_restarts VALUES (?,?,?,?,?,NULL,'PREPARING',NULL,NULL,NULL)",
                        (transaction, canonical(request.model_dump()).decode(), restart.binding_digest, handoff[0], digest(descriptor(original))))
                    self.database.event(db, "repair.restart_prepare_intent", {"transaction_id": transaction,
                        "request": request.model_dump(), "old_binding": handoff[0], "restart_binding": restart.binding_digest})
                state = original.call("settings_restart_prepare", request.model_dump(), timeout_ms=self._timeout(repair, 1))
            else:
                request = NativeRestartRequest.model_validate_json(row["request"])
                require(request.restart_id == restart_id, "IDEMPOTENCY_CONFLICT")
                state = original.call("settings_restart_status", {"restart_id": restart_id}, expected_restart=request,
                    timeout_ms=self._timeout(repair, 1)) if row["phase"] == "PREPARING" else None
            row = self._row(transaction)
            if row["phase"] == "PREPARING":
                checkpoint = NativeRestartCheckpoint.model_validate(state["checkpoint"])
                require(checkpoint.request == request and state["phase"] == "prepared"
                        and state["current_instance"] == checkpoint.source_instance
                        and state["expires_unix_ms"] == admission.worker_plan.expires_unix_ms, "RESTART_CHECKPOINT_MISMATCH")
                source = self.flow._put({"schema": "strata/ControllerRestartPrepareWitness/1",
                    "is_example": self.repairs.controller.simulation, "transaction_id": transaction, "state": state})
                self._phase(transaction, owner, epoch, "PREPARED", checkpoint=canonical(checkpoint.model_dump()).decode(), source_ref=source)
                row = self._row(transaction)
            checkpoint = NativeRestartCheckpoint.model_validate_json(row["checkpoint"])
            if row["phase"] in {"DETACHED", "ATTACHING", "ADOPTED"}:
                return {"checkpoint": checkpoint.model_dump(), "phase": row["phase"], "source_ref": row["source_ref"]}
            new_dispatch = row["phase"] == "PREPARED"
            require(new_dispatch or row["phase"] == "DETACHING", "RESTART_STATE_INVALID")
            if new_dispatch:
                self._phase(transaction, owner, epoch, "DETACHING")
            result = restart.call("detach" if new_dispatch else "status", admission.worker_plan, checkpoint,
                                  timeout_ms=self._timeout(repair)).result
            require(result.phase == "detached" and result.old_connection_digest == row["old_connection"], "RESTART_DETACH_UNCONFIRMED")
            source = self.flow._put({"schema": "strata/ControllerRestartDetachWitness/1",
                "is_example": self.repairs.controller.simulation, "transaction_id": transaction, "state": result.model_dump()})
            self._phase(transaction, owner, epoch, "DETACHED", source_ref=source)
            return {"checkpoint": checkpoint.model_dump(), "phase": "DETACHED", "source_ref": source}

    def adopt(self, transaction, owner, epoch, worker, restart, original, replacement, paths):
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            repair, control, admission, row = self._context(transaction, owner, epoch, worker, restart, original)
            require(row is not None and row["phase"] in {"DETACHED", "ATTACHING", "ADOPTED"}, "RESTART_OLD_TERMINAL_REQUIRED")
            checkpoint = NativeRestartCheckpoint.model_validate_json(row["checkpoint"])
            target = NativeControlTarget.model_validate_json(self.database.connection.execute(
                "SELECT target FROM repair_native_handoffs WHERE id=?", (transaction,)).fetchone()[0])
            paths = ReplacementPaths.model_validate(paths)
            require(isinstance(replacement, NativeSettingsEffectsClient), "REPAIR_PROFILE_MISMATCH")
            loaded = NativeSettingsEffectsClient.from_file(Path(paths.connection_file), game_fingerprint=target.game_fingerprint,
                                                          settings_fingerprint=target.settings_fingerprint)
            connection = descriptor(replacement)
            require(descriptor(loaded) == connection and replacement.settings_fingerprint == target.settings_fingerprint
                    and connection["session_id"] != original.connection.session_id
                    and connection["fingerprint"] == target.game_fingerprint, "RESTART_CONNECTION_MISMATCH")
            binding = digest({"connection": connection, "target": target.model_dump()})
            paths_json = canonical(paths.model_dump()).decode()
            if row["new_binding"]:
                require(row["new_binding"] == binding and row["paths"] == paths_json, "IDEMPOTENCY_CONFLICT")
            new_dispatch = row["phase"] == "DETACHED"
            if new_dispatch:
                self._phase(transaction, owner, epoch, "ATTACHING", new_binding=binding, paths=paths_json)
            result = restart.call("attach" if new_dispatch else "status", admission.worker_plan, checkpoint,
                paths=paths.model_dump() if new_dispatch else None, timeout_ms=self._timeout(repair)).result
            require(result.phase == "attached" and result.old_connection_digest == row["old_connection"]
                    and result.replacement.connection_digest == digest(connection)
                    and result.replacement.body_fingerprint == target.body_fingerprint
                    and result.replacement.implementation_digest == implementation_digest(), "RESTART_ADOPTION_UNCONFIRMED")
            state = replacement.call("settings_restart_status", {"restart_id": checkpoint.request.restart_id},
                expected_restart=checkpoint, timeout_ms=self._timeout(repair, 1))
            require(state["phase"] == "continued" and state["expires_unix_ms"] == admission.worker_plan.expires_unix_ms,
                    "RESTART_ADOPTION_UNCONFIRMED")
            held = worker.call("status", admission.worker_plan, timeout_ms=self._timeout(repair, 1)).result
            require(held.phase == "paused" and held.inputs_released
                    and held.primitive_events >= result.primitive_events, "INPUT_RELEASE_REQUIRED")
            native_hold = replacement.call("settings_repair_status", {"transaction_id": transaction}, expected_repair=admission,
                                          timeout_ms=self._timeout(repair, 1))
            require(native_hold["phase"] == "bound" and native_hold["body_fingerprint"] == target.body_fingerprint, "REPAIR_NATIVE_UNAVAILABLE")
            raw = replacement.call("settings_snapshot", {}, timeout_ms=self._timeout(repair, 1))
            self.flow._head(control["plan"], raw, applied=True, active=transaction)
            if row["phase"] == "ADOPTED":
                return {"phase": "ADOPTED", "source_ref": row["source_ref"]}
            source = self.flow._put({"schema": "strata/ControllerRestartAdoptionWitness/1",
                "is_example": self.repairs.controller.simulation, "transaction_id": transaction,
                "old_binding": row["old_binding"], "new_binding": binding, "checkpoint": checkpoint.model_dump(),
                "worker_state": result.model_dump(), "native_state": state, "native_head": raw,
                "native_hold": native_hold, "worker_hold": held.model_dump()})
            self._phase(transaction, owner, epoch, "ADOPTED", source_ref=source)
            return {"phase": "ADOPTED", "source_ref": source}
