"""Private, immutable essential-input cases. Recovery qualification stays separate.

Missing natural prerequisites are durable unverified_context dispositions, never
passing control proofs. This module cannot produce the generic essential-controls
check until the independently destructive host-recovery path is qualified.
"""

import json
import math
import time
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Strict
from .control_lock import profile_operation
from .native_control_plan import FIXED_ESCAPE
from .native_effect_evidence import EffectExpectation, evaluate_effect
from .native_repair_flow import NativeRepairFlow
from .native_settings import strict_json
from .native_settings_effects import EffectResult, PairedInputRelease
from .storage import Principal, canonical, digest, require

ROLES = {"forward": "key.forward", "back": "key.back", "left": "key.left", "right": "key.right",
    "jump": "key.jump", "sneak": "key.sneak", "sprint": "key.sprint", "inventory": "key.inventory",
    "attack": "key.attack", "use": "key.use", "escape": None}
Role = Literal["forward", "back", "left", "right", "jump", "sneak", "sprint", "inventory", "attack", "use", "escape"]


class EssentialCase(Strict):
    role: Role
    context: Literal["IN_GAME", "GUI", "CHAT"]
    stage: Literal["before_restart", "after_restart"]
    expectation: EffectExpectation | None
    unverified_reason: str | None = Field(pattern=r"^[A-Z][A-Z0-9_]{1,95}$")
    motion_axis: list[float] | None = Field(min_length=3, max_length=3)
    minimum_motion: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def predicate(self):
        require((self.expectation is None) == (self.unverified_reason is not None), "ESSENTIAL_CASE_INVALID")
        moving = self.expectation is not None and self.context == "IN_GAME" and self.role in {"forward", "back", "left", "right", "jump", "sprint"}
        require(moving == (self.motion_axis is not None) and moving == (self.minimum_motion > 0), "ESSENTIAL_MOTION_REQUIRED")
        if self.motion_axis is not None:
            require(all(math.isfinite(x) for x in self.motion_axis)
                    and abs(sum(x * x for x in self.motion_axis) - 1) < 1e-6, "ESSENTIAL_MOTION_REQUIRED")
            require(self.motion_axis == [0.0, 1.0, 0.0] if self.role == "jump" else self.motion_axis[1] == 0,
                    "ESSENTIAL_MOTION_REQUIRED")
        if self.expectation is not None:
            require(self.expectation.request.context == self.context and self.expectation.request.stage == self.stage,
                    "ESSENTIAL_CASE_INVALID")
            allowed = {"attack": {"attack_swing"}, "use": {"item_use_hold"}, "sneak": {"sneak_hold"},
                "forward": {"horizontal_motion"}, "back": {"horizontal_motion"}, "left": {"horizontal_motion"},
                "right": {"horizontal_motion"}, "sprint": {"horizontal_motion"}, "jump": {"screen_unchanged"}}
            require(self.expectation.predicate in (allowed.get(self.role, {"screen_transition", "screen_unchanged"})
                    if self.context == "IN_GAME" else {"screen_transition", "screen_unchanged"}), "ESSENTIAL_PREDICATE_INVALID")
        return self


def evaluate_case(case, raw):
    case = EssentialCase.model_validate(case)
    require(case.expectation is not None, "ESSENTIAL_CONTEXT_UNVERIFIED")
    verdict = evaluate_effect(case.expectation.model_dump(), raw)
    result = EffectResult.model_validate(raw)
    require(result.wire_schema.endswith(("/4", "/5")), "ESSENTIAL_INPUT_EVIDENCE_REQUIRED")
    reasons = list(verdict["reasons"])
    states = [o.value for o in result.observations if o.phase in {"before", "held", "released"}]
    if result.state == "observed":
        if case.motion_axis is not None:
            origin = states[0]
            progress = [sum(a * d for a, d in zip(case.motion_axis,
                (s.x - origin.x, s.y - origin.y, s.z - origin.z))) for s in states]
            if max(progress) < case.minimum_motion:
                reasons.append("ESSENTIAL_DIRECTED_MOTION_MISSING")
        if case.role == "sprint" and case.context == "IN_GAME" and (states[0].sprinting or not any(
                o.value.sprinting for o in result.observations if o.phase == "held")):
            reasons.append("ESSENTIAL_SPRINT_EFFECT_MISSING")
    return {"schema": "strata/NativeEssentialCaseVerdict/1", "case_digest": digest(case.model_dump()),
        "effect_verdict": verdict, "status": "fail" if reasons else "pass", "reasons": reasons,
        "qualification_implied": False}


def require_release_identity(request, raw, plan, companion_binding=None):
    result = EffectResult.model_validate(raw)
    if result.state != "observed":
        return
    receipt = next(o.value for o in result.observations if o.phase == "input_release")
    require(isinstance(receipt, PairedInputRelease) == (companion_binding is not None), "ESSENTIAL_RELEASE_IDENTITY_MISMATCH")
    if companion_binding is not None:
        companion = plan["changes"].get(companion_binding, {}).get("after", plan["backup"][companion_binding])
        require(companion["backend"] == "glfw" and companion["representation"] == "keysym"
                and not companion["modifiers"] and companion["code"] == receipt.companion, "ESSENTIAL_RELEASE_IDENTITY_MISMATCH")
    key = ({"backend": "glfw", "representation": "keysym", "code": 256, "modifiers": []}
        if request.binding_id == FIXED_ESCAPE else plan["changes"].get(request.binding_id, {}).get(
            "after", plan["backup"][request.binding_id]))
    require(key["backend"] == "glfw" and key["representation"] == ("mouse_button" if receipt.device == "mouse" else "keysym")
            and key["code"] == receipt.key and receipt.modifier == (key["modifiers"] or ["NONE"])[0],
            "ESSENTIAL_RELEASE_IDENTITY_MISMATCH")


class NativeEssentialInputs:
    def __init__(self, repairs):
        self.flow = NativeRepairFlow(repairs)
        self.repairs, self.controls, self.database = repairs, repairs.controls, repairs.database
        with self.database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS repair_essential_plans (id TEXT PRIMARY KEY, body TEXT NOT NULL, source_ref TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS repair_essential_cases (id TEXT, case_id TEXT, binding TEXT NOT NULL, "
                       "phase TEXT NOT NULL CHECK(phase IN ('INTENT','TERMINAL')), source_ref TEXT, PRIMARY KEY(id,case_id))")

    @staticmethod
    def slot(case):
        return case.role, case.context, case.stage

    @staticmethod
    def companion(case, body):
        if case.role != "sprint" or case.context != "IN_GAME":
            return None
        bindings = {slot["binding_id"] for slot in body["requirements"] if slot["role"] == "forward"}
        require(len(bindings) == 1 and None not in bindings, "ESSENTIAL_CONTEXT_UNVERIFIED")
        return next(iter(bindings))

    def _read(self, ref):
        return strict_json(self.repairs.controller.cas.read(Principal("operator", "operator"),
            self.repairs.controller.evidence_namespace, ref, max_bytes=262144))

    def _plan(self, transaction):
        row = self.database.connection.execute("SELECT * FROM repair_essential_plans WHERE id=?", (transaction,)).fetchone()
        require(row is not None, "ESSENTIAL_PLAN_REQUIRED")
        body = self._read(row["source_ref"])
        require(body == json.loads(row["body"]) and body["transaction_id"] == transaction
                and body["is_example"] is self.repairs.controller.simulation
                and body["plan_digest"] == digest(self.controls.status(transaction)["plan"]), "ESSENTIAL_EVIDENCE_INVALID")
        return row, body

    def requirements(self, transaction, owner, epoch, worker, native):
        repair, control, admission = self.flow._context(transaction, owner, epoch, worker, native, False)
        require(control["phase"] == "verifying", "REPAIR_RECOVERY_REQUIRED")
        state = self.controls.adapter.snapshot()
        self.controls._qualified(state)
        require(self.controls._policy(state) == control["plan"]["policy_digest"], "SETTINGS_POLICY_CHANGED")
        head, _ = self.flow._head(control["plan"], native.call("settings_snapshot", {}, timeout_ms=self.flow._timeout(repair)),
                                  applied=True, active=transaction)
        slots = []
        for role, translation in ROLES.items():
            matches = [name for name, b in head.bindings.items() if b.translation == translation] if translation else []
            binding = matches[0] if len(matches) == 1 else None
            contexts = {"IN_GAME", "GUI", "CHAT"}
            if role == "escape":
                binding = FIXED_ESCAPE if FIXED_ESCAPE in admission.effect_bindings else None
            elif binding is not None:
                metadata = state["bindings"][binding]
                known = set(metadata["contexts"])
                if metadata["context_confidence"] == "known" and known and known <= {"IN_GAME", "GUI"}:
                    contexts = known | ({"CHAT"} if "GUI" in known else set())
            for context in sorted(contexts):
                for stage in ("before_restart", "after_restart"):
                    slots.append({"role": role, "binding_id": binding, "context": context, "stage": stage})
        return slots, control, head

    def register(self, transaction, owner, epoch, worker, native, cases):
        require(isinstance(cases, list) and 0 < len(cases) <= 66, "ESSENTIAL_CASE_INVALID")
        values = sorted((EssentialCase.model_validate(c) for c in cases), key=self.slot)
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            slots, control, head = self.requirements(transaction, owner, epoch, worker, native)
            require(len(values) == len(slots) and {self.slot(v) for v in values} == {
                (s["role"], s["context"], s["stage"]) for s in slots}, "ESSENTIAL_CASES_INCOMPLETE")
            requests = [v.expectation.request for v in values if v.expectation is not None]
            require(len({r.id for r in requests}) == len(requests), "ESSENTIAL_CASE_INVALID")
            by_slot = {(s["role"], s["context"], s["stage"]): s for s in slots}
            for value in values:
                if value.expectation is None:
                    continue
                self.companion(value, {"requirements": slots})
                e = value.expectation
                require(e.request.binding_id == by_slot[self.slot(value)]["binding_id"]
                        and e.request.transaction_id == transaction and e.request.plan_digest == digest(control["plan"])
                        and e.settings_fingerprint == native.settings_fingerprint
                        and e.request.expected_revision == head.revision and e.request.expected_digest == head.digest,
                        "ESSENTIAL_CASE_IDENTITY_MISMATCH")
            body = {"schema": "strata/NativeEssentialInputPlan/1", "transaction_id": transaction,
                "plan_digest": digest(control["plan"]), "is_example": self.repairs.controller.simulation,
                "requirements": slots, "cases": [v.model_dump() for v in values],
                "recovery_qualification_required": True}
            require(len(canonical(body)) <= 262144, "ESSENTIAL_EVIDENCE_QUOTA")
            old = self.database.connection.execute("SELECT * FROM repair_essential_plans WHERE id=?", (transaction,)).fetchone()
            if old:
                require(json.loads(old["body"]) == body, "IDEMPOTENCY_CONFLICT")
                return old["source_ref"]
            # Declare the complete input matrix before any controller-managed effect.
            exists = self.database.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='repair_effects'").fetchone()
            require(not exists or self.database.connection.execute("SELECT 1 FROM repair_effects WHERE id=?", (transaction,)).fetchone() is None,
                    "ESSENTIAL_PLAN_TOO_LATE")
            ref = self.flow._put(body)
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                db.execute("INSERT INTO repair_essential_plans VALUES (?,?,?)", (transaction, canonical(body).decode(), ref))
                self.database.event(db, "repair.essential_plan", {"transaction_id": transaction, "source_ref": ref})
            return ref

    def capture(self, transaction, owner, epoch, worker, native, role, context, stage):
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            repair, control, admission = self.flow._context(transaction, owner, epoch, worker, native, False)
            require(control["phase"] == "verifying", "REPAIR_RECOVERY_REQUIRED")
            declared, body = self._plan(transaction)
            matches = [EssentialCase.model_validate(c) for c in body["cases"] if (c["role"], c["context"], c["stage"]) == (role, context, stage)]
            require(len(matches) == 1 and matches[0].expectation is not None, "ESSENTIAL_CONTEXT_UNVERIFIED")
            case, case_id = matches[0], ":".join((role, context, stage))
            request = case.expectation.request
            connection = native.connection.model_dump(mode="json")
            connection["bearer_token"] = native.connection.bearer_token.get_secret_value()
            binding = digest(connection)
            old = self.database.connection.execute("SELECT * FROM repair_essential_cases WHERE id=? AND case_id=?", (transaction, case_id)).fetchone()
            if old:
                require(old["binding"] == binding, "REPAIR_NOT_OWNED")
                if old["phase"] == "TERMINAL":
                    return old["source_ref"]
            else:
                head, _ = self.flow._head(control["plan"], native.call("settings_snapshot", {}, timeout_ms=self.flow._timeout(repair)),
                                          applied=True, active=transaction)
                require(head.revision == request.expected_revision and head.digest == request.expected_digest, "EFFECT_HEAD_CHANGED")
                with self.database.transaction() as db:
                    self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                    db.execute("INSERT INTO repair_essential_cases VALUES (?,?,?,'INTENT',NULL)", (transaction, case_id, binding))
                    self.database.event(db, "repair.essential_intent", {"transaction_id": transaction, "case_id": case_id, "source_ref": declared["source_ref"]})
            result = native.call("settings_effect_status" if old else "settings_effect_start",
                {"id": request.id} if old else request.model_dump(), timeout_ms=self.flow._timeout(repair),
                **({"expected_effect": request} if old else {
                    "effect_deadline_unix_ms": self.flow._effect_deadline(repair, admission)}))
            while result["state"] in {"prepared", "running"}:
                time.sleep(.025)
                result = native.call("settings_effect_status", {"id": request.id}, expected_effect=request, timeout_ms=self.flow._timeout(repair))
            verdict = evaluate_case(case.model_dump(), result)
            require_release_identity(request, result, control["plan"], self.companion(case, body))
            source = self.flow._put({"schema": "strata/NativeEssentialInputWitness/1", "transaction_id": transaction,
                "is_example": self.repairs.controller.simulation, "case_id": case_id, "binding_digest": binding,
                "plan_ref": declared["source_ref"], "result": result, "verdict": verdict})
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                db.execute("UPDATE repair_essential_cases SET phase='TERMINAL',source_ref=? WHERE id=? AND case_id=?", (source, transaction, case_id))
                self.database.event(db, "repair.essential_observed", {"transaction_id": transaction, "case_id": case_id,
                    "status": verdict["status"], "source_ref": source})
            return source

    def coverage(self, transaction):
        declared, body = self._plan(transaction)
        plan = self.controls.status(transaction)["plan"]
        cases = []
        for raw in body["cases"]:
            case = EssentialCase.model_validate(raw)
            row = self.database.connection.execute("SELECT * FROM repair_essential_cases WHERE id=? AND case_id=?",
                (transaction, ":".join(self.slot(case)))).fetchone()
            status = "unverified_context" if case.expectation is None else "not_run"
            if row and row["phase"] == "TERMINAL":
                witness = self._read(row["source_ref"])
                verdict = evaluate_case(case.model_dump(), witness["result"])
                require_release_identity(case.expectation.request, witness["result"], plan, self.companion(case, body))
                require(witness["schema"] == "strata/NativeEssentialInputWitness/1"
                        and witness["is_example"] is self.repairs.controller.simulation and witness["binding_digest"] == row["binding"]
                        and witness["transaction_id"] == transaction and witness["case_id"] == ":".join(self.slot(case))
                        and witness["plan_ref"] == declared["source_ref"] and witness["verdict"] == verdict, "ESSENTIAL_EVIDENCE_INVALID")
                status = verdict["status"]
            cases.append({"role": case.role, "context": case.context, "stage": case.stage, "status": status,
                "unverified_reason": case.unverified_reason, "source_ref": row["source_ref"] if row else None})
        return {"schema": "strata/NativeEssentialInputCoverage/1", "plan_ref": declared["source_ref"], "cases": cases,
            "input_cases_complete": all(c["status"] == "pass" for c in cases), "recovery_qualification_required": True,
            "essential_controls_verified": False}
