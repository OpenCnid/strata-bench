"""Declared native-effect predicates and durable per-binding evidence production.

This does not qualify an input pool, infer an intended effect from its outcome,
or replace the independent essential-control/isolation acceptance checks.
"""

import json
import math
import time
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Digest, Strict
from .control_lock import profile_operation
from .native_repair_flow import NativeRepairFlow
from .native_restart import NativeRestartCheckpoint, NativeRestartState
from .native_settings import strict_json
from .native_settings_effects import ClassName, EffectRequest, EffectResult, NativeRepairState
from .storage import Principal, canonical, digest, require
from .worker_repair import WorkerRepairState
from .worker_restart import WorkerRestartState


class EffectExpectation(Strict):
    schema_: Literal["strata/NativeEffectExpectation/1", "strata/NativeEffectExpectation/2"] = Field(alias="schema")
    request: EffectRequest
    settings_fingerprint: Digest
    predicate: Literal["screen_transition", "screen_unchanged", "sneak_hold", "horizontal_motion", "attack_swing", "item_use_hold"]
    initial_screen: ClassName
    final_screen: ClassName
    required_openings: list[ClassName] = Field(max_length=16)
    forbidden_openings: list[ClassName] = Field(max_length=16)
    min_horizontal_distance: float = Field(ge=0, le=100)
    max_horizontal_distance: float = Field(gt=0, le=100)

    @model_validator(mode="after")
    def declared(self):
        require(self.predicate not in {"attack_swing", "item_use_hold"} or self.schema_.endswith("/2"),
                "EFFECT_EXPECTATION_VERSION_REQUIRED")
        require(len(set(self.required_openings)) == len(self.required_openings)
                and len(set(self.forbidden_openings)) == len(self.forbidden_openings)
                and not set(self.required_openings) & set(self.forbidden_openings)
                and self.min_horizontal_distance <= self.max_horizontal_distance, "EFFECT_EXPECTATION_INVALID")
        require((self.predicate == "horizontal_motion") == (self.min_horizontal_distance > 0), "EFFECT_EXPECTATION_INVALID")
        if self.predicate == "screen_transition":
            require(self.initial_screen != self.final_screen, "EFFECT_EXPECTATION_INVALID")
        else:
            require(self.initial_screen == self.final_screen, "EFFECT_EXPECTATION_INVALID")
        return self


def evaluate_effect(expectation, raw):
    """Evaluate exactly the declared predicate; raw observations are not authenticated here."""
    expected = EffectExpectation.model_validate(expectation)
    observed = EffectResult.model_validate(raw)
    require(observed.request == expected.request, "EFFECT_EVIDENCE_IDENTITY_MISMATCH")
    if expected.predicate in {"attack_swing", "item_use_hold"}:
        require(observed.wire_schema.endswith(("/4", "/5")), "EFFECT_ACTIVITY_EVIDENCE_REQUIRED")
    reasons = []
    if observed.state != "observed":
        reasons.append("EFFECT_NOT_OBSERVED")
    if observed.observations:
        require(observed.observations[0].value.settings_fingerprint == expected.settings_fingerprint,
                "EFFECT_EVIDENCE_IDENTITY_MISMATCH")
    states = [item.value for item in observed.observations if item.phase in {"before", "held", "released"}]
    released = [item.value for item in observed.observations if item.phase == "released"]
    held = [item.value for item in observed.observations if item.phase == "held"]
    openings = [item.value.requested_screen for item in observed.observations
                if item.phase == "screen_opening" and not item.value.cancelled_at_observer]
    if observed.state == "observed":
        require(states and released, "EFFECT_EVIDENCE_INVALID")
        if states[0].screen != expected.initial_screen:
            reasons.append("INITIAL_SCREEN_MISMATCH")
        if released[-1].screen != expected.final_screen:
            reasons.append("SETTLED_SCREEN_MISMATCH")
        if not all(item.window_active for item in states):
            reasons.append("WINDOW_INACTIVE")
        if not set(expected.required_openings) <= set(openings):
            reasons.append("REQUIRED_OPENING_MISSING")
        if set(expected.forbidden_openings) & set(openings):
            reasons.append("COMPETING_SCREEN_OPENED")
        distances = [math.hypot(item.x - states[0].x, item.z - states[0].z) for item in states]
        if max(distances) > expected.max_horizontal_distance:
            reasons.append("MOVEMENT_BOUND_EXCEEDED")
        if expected.predicate != "screen_transition" and any(item.screen != expected.initial_screen for item in states):
            reasons.append("UNEXPECTED_SCREEN_TRANSITION")
        if expected.predicate == "sneak_hold" and (not any(item.sneaking for item in held)
                or released[-1].sneaking or states[0].sneaking):
            reasons.append("SNEAK_PRESS_OR_RELEASE_MISSING")
        if expected.predicate == "horizontal_motion" and max(distances) < expected.min_horizontal_distance:
            reasons.append("MOVEMENT_EFFECT_MISSING")
        if expected.predicate == "attack_swing" and (states[0].swinging or not any(item.swinging for item in states[1:])):
            reasons.append("ATTACK_SWING_MISSING")
        if expected.predicate == "item_use_hold" and (states[0].using_item or not any(item.using_item for item in held)
                or released[-1].using_item):
            reasons.append("ITEM_USE_PRESS_OR_RELEASE_MISSING")
        if observed.wire_schema.endswith(("/4", "/5")):
            if released[-1].mouse_left or released[-1].mouse_right:
                reasons.append("MOUSE_RELEASE_UNCONFIRMED")
            receipt = next(item.value for item in observed.observations if item.phase == "input_release")
            if receipt.device == "mouse":
                field = "mouse_left" if receipt.key == 0 else "mouse_right"
                if not any(getattr(item, field) for item in held) or not states[0].mouse_grabbed:
                    reasons.append("MOUSE_PRESS_OR_CONTEXT_MISSING")
    return {"schema": "strata/NativeEffectVerdict/1", "expectation_digest": digest(expected.model_dump()),
        "result_digest": digest(observed.model_dump()), "status": "fail" if reasons else "pass", "reasons": reasons,
        "qualification_implied": False, "input_resume_authorized": False}


class NativeEffectEvidence:
    def __init__(self, repairs):
        self.flow = NativeRepairFlow(repairs)
        self.repairs, self.controls, self.database = repairs, repairs.controls, repairs.database
        with self.database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS repair_effect_plans (id TEXT PRIMARY KEY, manifest TEXT NOT NULL, source_ref TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS repair_effects (id TEXT, effect_id TEXT, binding_digest TEXT NOT NULL, "
                       "phase TEXT NOT NULL CHECK(phase IN ('INTENT','TERMINAL')), source_ref TEXT, check_ref TEXT, "
                       "PRIMARY KEY(id,effect_id))")

    @staticmethod
    def _slot(request):
        return request.binding_id, request.context, request.stage

    def register(self, transaction, owner, epoch, worker, native, expectations):
        require(isinstance(expectations, list) and 0 < len(expectations) <= 12288, "EFFECT_EXPECTATION_INVALID")
        values = [EffectExpectation.model_validate(e) for e in expectations]
        manifest = [value.model_dump() for value in sorted(values, key=lambda e: e.request.id)]
        require(len(canonical(manifest)) <= 4 * 1024 * 1024, "EFFECT_EVIDENCE_QUOTA")
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            _, control, admission = self.flow._context(transaction, owner, epoch, worker, native, False)
            require(control["phase"] == "verifying", "REPAIR_RECOVERY_REQUIRED")
            required = {(c["binding_id"], c["context"], c["stage"]) for c in control["plan"]["binding_checks"]}
            require(len({e.request.id for e in values}) == len(values)
                    and len({self._slot(e.request) for e in values}) == len(values)
                    and {self._slot(e.request) for e in values} == required
                    and all(e.request.transaction_id == transaction and e.request.plan_digest == admission.worker_plan.plan_digest
                            and e.settings_fingerprint == native.settings_fingerprint for e in values), "EFFECT_EXPECTATION_INCOMPLETE")
            old = self.database.connection.execute("SELECT * FROM repair_effect_plans WHERE id=?", (transaction,)).fetchone()
            if old:
                require(json.loads(old["manifest"]) == manifest, "IDEMPOTENCY_CONFLICT")
                return old["source_ref"]
            ref = self.flow._put({"schema": "strata/NativeEffectVerificationPlan/1",
                "transaction_id": transaction, "plan_digest": digest(control["plan"]),
                "is_example": self.repairs.controller.simulation or self.controls.simulation, "expectations": manifest})
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                db.execute("INSERT INTO repair_effect_plans VALUES (?,?,?)", (transaction, canonical(manifest).decode(), ref))
                self.database.event(db, "repair.effect_plan", {"transaction_id": transaction, "source_ref": ref})
            return ref

    def capture(self, transaction, owner, epoch, worker, native, effect_id):
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            repair, control, admission = self.flow._context(transaction, owner, epoch, worker, native, False)
            require(control["phase"] == "verifying", "REPAIR_RECOVERY_REQUIRED")
            declared = self.database.connection.execute("SELECT * FROM repair_effect_plans WHERE id=?", (transaction,)).fetchone()
            require(declared is not None, "EFFECT_EXPECTATION_REQUIRED")
            found = [e for e in json.loads(declared["manifest"]) if e["request"]["id"] == effect_id]
            require(len(found) == 1, "EFFECT_EXPECTATION_REQUIRED")
            expected = EffectExpectation.model_validate(found[0])
            request = expected.request
            require(expected.settings_fingerprint == native.settings_fingerprint, "EFFECT_EVIDENCE_IDENTITY_MISMATCH")
            raw_connection = native.connection.model_dump(mode="json")
            raw_connection["bearer_token"] = native.connection.bearer_token.get_secret_value()
            binding = digest(raw_connection)
            old = self.database.connection.execute("SELECT * FROM repair_effects WHERE id=? AND effect_id=?", (transaction, effect_id)).fetchone()
            if old:
                require(old["binding_digest"] == binding, "REPAIR_NOT_OWNED")
                if old["phase"] == "TERMINAL":
                    return self.status(transaction, effect_id)
            else:
                raw = native.call("settings_snapshot", {}, timeout_ms=self.flow._timeout(repair))
                head, _ = self.flow._head(control["plan"], raw, applied=True, active=transaction)
                require(head.revision == request.expected_revision and head.digest == request.expected_digest, "EFFECT_HEAD_CHANGED")
                with self.database.transaction() as db:
                    self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                    db.execute("INSERT INTO repair_effects VALUES (?,?,?,'INTENT',NULL,NULL)", (transaction, effect_id, binding))
                    self.database.event(db, "repair.effect_intent", {"transaction_id": transaction, "effect_id": effect_id,
                        "binding_digest": binding, "expectation_ref": declared["source_ref"]})
            operation = "settings_effect_status" if old else "settings_effect_start"
            result = native.call(operation, {"id": effect_id} if old else request.model_dump(),
                timeout_ms=self.flow._timeout(repair), **({"expected_effect": request} if old else {
                    "effect_deadline_unix_ms": self.flow._effect_deadline(repair, admission)}))
            while result["state"] in {"prepared", "running"}:
                time.sleep(.025)
                result = native.call("settings_effect_status", {"id": effect_id}, expected_effect=request,
                                     timeout_ms=self.flow._timeout(repair))
            verdict = evaluate_effect(expected.model_dump(), result)
            witness = self.flow._put({"schema": "strata/NativeEffectCheckWitness/1",
                "is_example": self.repairs.controller.simulation or self.controls.simulation,
                "transaction_id": transaction, "effect_id": effect_id, "binding_digest": binding,
                "expectation_ref": declared["source_ref"], "result": result, "verdict": verdict})
            slot = next(c for c in control["plan"]["binding_checks"]
                        if (c["binding_id"], c["context"], c["stage"]) == self._slot(request))
            proof = self.flow._put({"schema": "strata/ControlCheck/1", "transaction_id": transaction,
                "plan_digest": digest(control["plan"]), **slot, "status": verdict["status"],
                "is_example": self.repairs.controller.simulation or self.controls.simulation,
                "source_refs": [declared["source_ref"], witness]})
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                db.execute("UPDATE repair_effects SET phase='TERMINAL',source_ref=?,check_ref=? WHERE id=? AND effect_id=?",
                           (witness, proof, transaction, effect_id))
                self.database.event(db, "repair.effect_observed", {"transaction_id": transaction,
                    "effect_id": effect_id, "status": verdict["status"], "source_ref": witness, "check_ref": proof})
            return {"source_ref": witness, "check": dict(slot, status=verdict["status"], refs=[proof])}

    def status(self, transaction, effect_id):
        row = self.database.connection.execute("SELECT * FROM repair_effects WHERE id=? AND effect_id=?", (transaction, effect_id)).fetchone()
        require(row is not None and row["phase"] == "TERMINAL", "EFFECT_EVIDENCE_UNAVAILABLE")
        proof = self.repairs.controller.cas.json(Principal("operator", "operator"), self.repairs.controller.evidence_namespace, row["check_ref"])
        return {"source_ref": row["source_ref"], "check": {k: proof[k] for k in ("binding_id", "context", "stage", "check", "status")}
                | {"refs": [row["check_ref"]]}}

    def effect_checks(self, transaction, owner, epoch, worker, native):
        """Summarize the complete declared matrix; never supply essential-control proof."""
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            _, control, _ = self.flow._context(transaction, owner, epoch, worker, native, False)
            require(control["phase"] == "verifying", "REPAIR_RECOVERY_REQUIRED")
            plan = control["plan"]
            declared = self.database.connection.execute("SELECT * FROM repair_effect_plans WHERE id=?", (transaction,)).fetchone()
            require(declared is not None, "EFFECT_EXPECTATION_REQUIRED")
            expectations = [EffectExpectation.model_validate(e) for e in json.loads(declared["manifest"])]
            slots = {(c["binding_id"], c["context"], c["stage"]): c for c in plan["binding_checks"]}
            require(len(expectations) == len(slots) and {self._slot(e.request) for e in expectations} == set(slots),
                    "EFFECT_EXPECTATION_INCOMPLETE")
            simulation = self.repairs.controller.simulation or self.controls.simulation
            budget = plan["verification_byte_limit"]

            def read(ref, limit):
                nonlocal budget
                require(budget > 0, "EFFECT_EVIDENCE_QUOTA")
                raw = self.repairs.controller.cas.read(Principal("operator", "operator"),
                    self.repairs.controller.evidence_namespace, ref, max_bytes=min(limit, budget))
                budget -= len(raw)
                return strict_json(raw)

            require(read(declared["source_ref"], 4 * 1024 * 1024) == {
                "schema": "strata/NativeEffectVerificationPlan/1", "transaction_id": transaction,
                "plan_digest": digest(plan), "is_example": simulation, "expectations": json.loads(declared["manifest"])},
                "EFFECT_EVIDENCE_IDENTITY_MISMATCH")
            results, sources = [], []
            for expected in expectations:
                row = self.database.connection.execute("SELECT * FROM repair_effects WHERE id=? AND effect_id=?",
                    (transaction, expected.request.id)).fetchone()
                require(row is not None and row["phase"] == "TERMINAL", "EFFECT_EVIDENCE_INCOMPLETE")
                witness = read(row["source_ref"], 262144)
                require(isinstance(witness, dict) and set(witness) == {"schema", "is_example", "transaction_id",
                    "effect_id", "binding_digest", "expectation_ref", "result", "verdict"}
                    and witness["schema"] == "strata/NativeEffectCheckWitness/1" and witness["is_example"] is simulation
                    and witness["transaction_id"] == transaction and witness["effect_id"] == expected.request.id
                    and witness["binding_digest"] == row["binding_digest"] and witness["expectation_ref"] == declared["source_ref"],
                    "EFFECT_EVIDENCE_IDENTITY_MISMATCH")
                verdict = evaluate_effect(expected.model_dump(), witness["result"])
                require(verdict == witness["verdict"], "EFFECT_EVIDENCE_INVALID")
                observed = EffectResult.model_validate(witness["result"])
                require(observed.wire_schema.endswith(("/3", "/4", "/5")), "EFFECT_RELEASE_EVIDENCE_REQUIRED")
                release = [o.value for o in observed.observations if o.phase == "input_release"]
                require(all(not hasattr(item, "companion") for item in release), "ESSENTIAL_GESTURE_EVIDENCE_REQUIRED")
                key = plan["changes"].get(expected.request.binding_id, {}).get("after", plan["backup"][expected.request.binding_id])
                require(len(release) == 1 and key["backend"] == "glfw"
                        and key["representation"] == ("mouse_button" if getattr(release[0], "device", "keyboard") == "mouse" else "keysym")
                        and release[0].key == key["code"] and release[0].modifier == (key["modifiers"] or ["NONE"])[0],
                        "EFFECT_RELEASE_EVIDENCE_MISMATCH")
                slot = slots[self._slot(expected.request)]
                proof = read(row["check_ref"], 65536)
                require(proof == {"schema": "strata/ControlCheck/1", "transaction_id": transaction,
                    "plan_digest": digest(plan), **slot, "status": verdict["status"], "is_example": simulation,
                    "source_refs": [declared["source_ref"], row["source_ref"]]}, "EFFECT_EVIDENCE_INVALID")
                results.append(dict(slot, status=verdict["status"], refs=[row["check_ref"]]))
                sources.append(row["source_ref"])
            # One bounded summary witness avoids manufacturing independent generic verdicts.
            summary = self.flow._put({"schema": "strata/NativeEffectMatrixWitness/1", "transaction_id": transaction,
                "plan_digest": digest(plan), "is_example": simulation, "expectation_ref": declared["source_ref"],
                "effect_refs": sources, "binding_checks": results, "input_resume_authorized": False})
            checks = {}
            for name in ("intended-effect", "competing-effect", "keys-released"):
                relevant = results if name == "keys-released" else [r for r in results if r["check"] == name]
                # Empty effect categories are not manufactured as verified behavior.
                status = "pass" if relevant and all(r["status"] == "pass" for r in relevant) else "fail"
                proof = self.flow._put({"schema": "strata/ControlCheck/1", "transaction_id": transaction,
                    "plan_digest": digest(plan), "check": name, "binding_id": None, "context": None, "stage": None,
                    "status": status, "is_example": simulation, "source_refs": [summary]})
                checks[name] = {"status": status, "refs": [proof]}
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                self.database.event(db, "repair.effect_checks", {"transaction_id": transaction, "source_ref": summary})
            return {"checks": checks, "binding_checks": results}

    def restart_check(self, transaction, owner, epoch, worker, native):
        """Derive persistence only from an adopted, process-owned native checkpoint."""
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            repair, control, admission = self.flow._context(transaction, owner, epoch, worker, native, False)
            require(control["phase"] == "verifying", "REPAIR_RECOVERY_REQUIRED")
            row = self.database.connection.execute("SELECT * FROM repair_native_restarts WHERE id=?", (transaction,)).fetchone()
            require(row is not None and row["phase"] == "ADOPTED", "RESTART_ADOPTION_UNCONFIRMED")
            raw = self.repairs.controller.cas.read(Principal("operator", "operator"), self.repairs.controller.evidence_namespace,
                                                 row["source_ref"], max_bytes=1024 * 1024)
            witness = strict_json(raw)
            require(isinstance(witness, dict) and set(witness) == {"schema", "is_example", "transaction_id", "old_binding", "new_binding",
                "checkpoint", "worker_state", "native_state", "native_head", "native_hold", "worker_hold"}, "RESTART_EVIDENCE_INVALID")
            simulation = self.repairs.controller.simulation or self.controls.simulation
            require(witness["schema"] == "strata/ControllerRestartAdoptionWitness/1" and witness["is_example"] is simulation
                    and witness["transaction_id"] == transaction and witness["old_binding"] == row["old_binding"]
                    and witness["new_binding"] == row["new_binding"], "RESTART_EVIDENCE_INVALID")
            checkpoint = NativeRestartCheckpoint.model_validate(witness["checkpoint"])
            require(checkpoint == NativeRestartCheckpoint.model_validate_json(row["checkpoint"]), "RESTART_EVIDENCE_INVALID")
            replacement = WorkerRestartState.model_validate(witness["worker_state"])
            continuation = NativeRestartState.model_validate(witness["native_state"])
            native_hold = NativeRepairState.model_validate(witness["native_hold"])
            worker_hold = WorkerRepairState.model_validate(witness["worker_hold"])
            require(replacement.phase == "attached" and replacement.checkpoint == continuation.checkpoint == checkpoint
                    and replacement.plan == worker_hold.plan == admission.worker_plan
                    and continuation.phase == "continued" and continuation.expires_unix_ms == admission.worker_plan.expires_unix_ms
                    and native_hold.admission == admission and native_hold.phase == "bound"
                    and worker_hold.phase == "paused" and worker_hold.inputs_released
                    and native_hold.body_fingerprint == replacement.replacement.body_fingerprint, "RESTART_EVIDENCE_INVALID")
            head, _ = self.flow._head(control["plan"], witness["native_head"], applied=True, active=transaction)
            require(head.fingerprint == native.settings_fingerprint and head.revision == checkpoint.request.expected_revision
                    and head.digest == checkpoint.request.expected_digest
                    and checkpoint.request.transaction_id == transaction and checkpoint.request.plan_digest == digest(control["plan"]),
                    "RESTART_EVIDENCE_INVALID")
            require(native.call("settings_snapshot", {}, timeout_ms=self.flow._timeout(repair)) == witness["native_head"],
                    "RESTART_EVIDENCE_INVALID")
            # The native head digest binds runtime metadata/values and complete options bytes.
            proof = self.flow._put({"schema": "strata/ControlCheck/1", "transaction_id": transaction,
                "plan_digest": digest(control["plan"]), "check": "restart-persistence", "binding_id": None,
                "context": None, "stage": None, "status": "pass", "is_example": simulation, "source_refs": [row["source_ref"]]})
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                self.database.event(db, "repair.restart_check", {"transaction_id": transaction, "check_ref": proof})
            return {"status": "pass", "refs": [proof]}
