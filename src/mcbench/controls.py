"""Capability-tested settings transaction engine; stock Mineflayer is unsupported.

The settings adapter must implement atomic compare-and-swap on its client thread
or against fully stopped files. This engine never edits arbitrary options files.
The Forge adapter and real effect/restart conformance remain separate work.
"""

import hashlib
import json
import re
from typing import Protocol

from .control_lock import profile_operation
from .contracts import Key
from .storage import Database, Fault, canonical, digest, require

REQUIRED_CHECKS = {"intended-effect", "competing-effect", "keys-released", "essential-controls",
                   "restart-persistence"}
VERIFICATION_BYTE_LIMIT = 32 * 1024 * 1024


def key_identity(key):
    value = Key.model_validate(key)
    return (value.backend, value.representation, value.code, tuple(sorted(value.modifiers)))


def overlapping(left, right):
    if left["context_confidence"] != "known" or right["context_confidence"] != "known":
        return True
    # Forge UNIVERSAL explicitly conflicts with every context, rather than being
    # a separate screen in the set. Empty/custom contexts are not proven disjoint.
    standard = {"IN_GAME", "GUI"}
    if not left["contexts"] or not right["contexts"] or not (
            set(left["contexts"]) | set(right["contexts"])) <= standard:
        return True
    return bool(set(left["contexts"]) & set(right["contexts"]))


def physical_conflict(left, right):
    """Conservative ordinary-input overlap, including the keys in a chord.

    Forge 43.4.23 KeyModifier.NONE can remain active with modifiers in IN_GAME,
    and custom consumers may poll the main key independently. Different modifier
    lists alone are never evidence of exclusive effects. A key constant also does
    not establish keysym/scancode equivalence or a tested input route.
    """
    left, right = Key.model_validate(left), Key.model_validate(right)
    if "unbound" in (left.representation, right.representation):
        return False
    require(left.backend == right.backend, "BACKEND_MISMATCH")
    keyboard = {"keysym", "scancode"}
    if left.representation != right.representation and {
            left.representation, right.representation} <= keyboard:
        return True  # Unknown physical alias, not proof of separate keys.
    if (left.representation, left.code) == (right.representation, right.code):
        return True
    if left.modifiers or right.modifiers:
        if left.backend != "glfw" or "scancode" in (left.representation, right.representation):
            return True  # Other backend modifier layouts need their own conformance.
        modifier_keys = {"SHIFT": {340, 344}, "CONTROL": {341, 345}, "ALT": {342, 346}}
        for main, chord in ((left, right), (right, left)):
            if main.representation == "keysym" and any(
                    main.code in modifier_keys[modifier] for modifier in chord.modifiers):
                return True
    return False


class SettingsAdapter(Protocol):
    def snapshot(self) -> dict: ...
    def compare_and_swap(self, expected_revision: int, changes: dict, *,
                         transaction_id: str, rollback: bool = False) -> dict: ...
    def verify_and_restart(self, changes: dict, *, transaction_id: str,
                           plan_digest: str, binding_checks: list) -> dict: ...
    def stop_all(self) -> None: ...


class Controls:
    def __init__(self, database: Database, adapter: SettingsAdapter, *, evidence_reader=None,
                 simulation=False):
        self.database, self.adapter = database, adapter
        require(type(simulation) is bool, "INVALID_CONTROLS_MODE")
        self.evidence_reader, self.simulation = evidence_reader, simulation
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS control_profile (simulation INTEGER NOT NULL)")
            profile = db.execute("SELECT simulation FROM control_profile").fetchone()
            if profile is None:
                db.execute("INSERT INTO control_profile VALUES (?)", (int(simulation),))
            else:
                require(bool(profile[0]) == simulation, "PROFILE_MISMATCH")
            db.execute("CREATE TABLE IF NOT EXISTS control_transactions (id TEXT PRIMARY KEY, "
                       "agent TEXT, fingerprint TEXT, phase TEXT, plan TEXT, receipt TEXT, profile_id TEXT)")
            if "profile_id" not in {row[1] for row in db.execute("PRAGMA table_info(control_transactions)")}:
                db.execute("ALTER TABLE control_transactions ADD COLUMN profile_id TEXT")

    @staticmethod
    def _qualified(state):
        require(all(state.get(name) is True for name in ("supported", "atomic_cas", "restart_tested")),
                "CAPABILITY_MISSING")
        require(isinstance(state.get("profile_id"), str) and
                re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", state["profile_id"]), "SETTINGS_PROFILE_REQUIRED")

    @staticmethod
    def _policy(state):
        return digest({"backend": state["backend"], "fingerprint": state["fingerprint"],
            "profile_id": state["profile_id"], "tested_pool": state["tested_pool"],
            "qualification": {name: state.get(name) for name in ("supported", "atomic_cas", "restart_tested")},
            "additional_checks": state.get("additional_checks", []),
            "bindings": {name: {key: value for key, value in binding.items()
                                 if key not in {"key", "persisted_value"}}
                         for name, binding in state["bindings"].items()}})

    def _version(self, plan):
        require(plan.get("plan_version") == 2, "SETTINGS_PLAN_UPGRADE_REQUIRED")
        require(plan.get("simulation") is self.simulation, "PROFILE_MISMATCH")
        require(plan.get("verification_byte_limit") == VERIFICATION_BYTE_LIMIT,
                "SETTINGS_POLICY_CHANGED")

    @staticmethod
    def _idle(db, profile_id, transaction_id, agent):
        legacy = db.execute("SELECT id FROM control_transactions WHERE profile_id IS NULL AND "
                            "phase IN ('applying','verifying','failed')").fetchone()
        require(legacy is None, "SETTINGS_LEGACY_RECOVERY_REQUIRED")
        busy = db.execute("SELECT id FROM control_transactions WHERE (profile_id=? OR agent=?) AND id<>? "
                          "AND phase IN ('applying','verifying','failed')",
                          (profile_id, agent, transaction_id)).fetchone()
        require(busy is None, "SETTINGS_BUSY")

    def plan(self, agent, transaction_id, binding_ids):
        require(isinstance(agent, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", agent)
                and isinstance(transaction_id, str)
                and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", transaction_id), "INVALID_BINDINGS")
        require(isinstance(binding_ids, list) and 0 < len(binding_ids) <= 32
                and all(isinstance(name, str) for name in binding_ids)
                and len(binding_ids) == len(set(binding_ids)), "INVALID_BINDINGS")
        old = self.database.connection.execute("SELECT plan FROM control_transactions WHERE id=?",
                                               (transaction_id,)).fetchone()
        if old:
            plan = json.loads(old[0])
            self._version(plan)
            require(plan["agent"] == agent and plan["requested_bindings"] == sorted(binding_ids),
                    "IDEMPOTENCY_CONFLICT")
            return plan
        state = self.adapter.snapshot()
        self._qualified(state)
        bindings = state["bindings"]
        require(isinstance(bindings, dict) and 0 < len(bindings) <= 2048, "INVALID_BINDINGS")
        require(all(Key.model_validate(binding["key"]).backend == state["backend"]
                    for binding in bindings.values()), "BACKEND_MISMATCH")
        require(binding_ids and len(binding_ids) == len(set(binding_ids)), "INVALID_BINDINGS")
        current = {name: binding["key"] for name, binding in bindings.items()}
        proposed = dict(current)
        changes = {}
        # Pool order is part of the pinned backend policy, not Unicode enumeration.
        for name in sorted(binding_ids):
            require(name in bindings, "BINDING_MISSING")
            binding = bindings[name]
            require(not binding["protected"] and binding.get("owner_evidence") and
                    binding.get("consumer_tested") is True, "PROTECTED_OR_UNKNOWN_BINDING")
            conflict = any(other != name and physical_conflict(proposed[other], proposed[name])
                           and overlapping(binding, b) for other, b in bindings.items())
            if not conflict and Key.model_validate(proposed[name]).representation != "unbound":
                continue
            selected = None
            for candidate in state["tested_pool"]:
                key = Key.model_validate(candidate["key"])
                require(key.backend == state["backend"], "BACKEND_MISMATCH")
                if key.representation == "unbound" or not candidate.get("evidence_ref"):
                    continue
                if all(other == name or not physical_conflict(proposed[other], candidate["key"])
                       or not overlapping(binding, b) for other, b in bindings.items()):
                    selected = candidate["key"]
                    break
            require(selected is not None, "KEY_POOL_EXHAUSTED")
            proposed[name] = selected
            changes[name] = {"before": current[name], "after": selected}
        affected = set(changes)
        for name, change in changes.items():
            affected.update(other for other, binding in bindings.items() if other != name
                and overlapping(bindings[name], binding)
                and any(physical_conflict(binding["key"], value)
                        for value in (change["before"], change["after"])))
        binding_checks = []
        for name in sorted(affected):
            binding = bindings[name]
            contexts = set(binding["contexts"])
            if binding["context_confidence"] != "known" or not contexts <= {"IN_GAME", "GUI"} or not contexts:
                contexts = {"IN_GAME", "GUI", "CHAT"}
            elif "GUI" in contexts:
                contexts.add("CHAT")
            for context in sorted(contexts):
                for stage in ("before_restart", "after_restart"):
                    binding_checks.append({"binding_id": name, "context": context, "stage": stage,
                        "check": "intended-effect" if name in changes else "competing-effect"})
        plan = {"plan_version": 2, "profile_id": state["profile_id"], "simulation": self.simulation,
                "verification_byte_limit": VERIFICATION_BYTE_LIMIT,
                "requested_bindings": sorted(binding_ids), "policy_digest": self._policy(state),
                "binding_checks": binding_checks,
                "agent": agent, "transaction_id": transaction_id, "revision": state["revision"],
                "fingerprint": state["fingerprint"], "keymap_digest": digest(current),
                "backup": current, "changes": changes,
                "required_checks": sorted(REQUIRED_CHECKS | set(state.get("additional_checks", [])))}
        with self.database.transaction() as db:
            self._idle(db, plan["profile_id"], transaction_id, agent)
            old = db.execute("SELECT plan FROM control_transactions WHERE id=?", (transaction_id,)).fetchone()
            if old:
                retained = json.loads(old[0])
                self._version(retained)
                require(retained["agent"] == agent and retained["requested_bindings"] == sorted(binding_ids),
                        "IDEMPOTENCY_CONFLICT")
                return retained
            else:
                db.execute("INSERT INTO control_transactions (id,agent,fingerprint,phase,plan,receipt,profile_id) "
                           "VALUES (?,?,?,'planned',?,NULL,?)",
                           (transaction_id, agent, state["fingerprint"], canonical(plan).decode(), state["profile_id"]))
                self.database.event(db, "controls.planned", plan)
        return plan

    def status(self, transaction_id):
        row = self.database.connection.execute("SELECT * FROM control_transactions WHERE id=?",
                                               (transaction_id,)).fetchone()
        require(row is not None, "TRANSACTION_MISSING")
        return dict(row) | {"plan": json.loads(row["plan"]),
                            "receipt": json.loads(row["receipt"]) if row["receipt"] else None}

    def _phase(self, transaction_id, phase, receipt=None):
        with self.database.transaction() as db:
            row = db.execute("SELECT phase FROM control_transactions WHERE id=?", (transaction_id,)).fetchone()
            require(row is not None, "TRANSACTION_MISSING")
            allowed = {"planned": {"applying"}, "applying": {"verifying", "rolled_back", "failed"},
                "verifying": {"committed", "rolled_back", "failed"},
                "committed": {"rolled_back", "failed"}, "rolled_back": {"failed"},
                "failed": {"rolled_back", "failed"}}
            require(phase in allowed.get(row[0], set()), "INVALID_TRANSITION")
            result = db.execute("UPDATE control_transactions SET phase=?,receipt=? WHERE id=? AND phase=?",
                       (phase, canonical(receipt).decode() if receipt else None, transaction_id, row[0]))
            require(result.rowcount == 1, "REVISION_CONFLICT")
            self.database.event(db, "controls." + phase, {"transaction_id": transaction_id,
                                                         "receipt": receipt, "simulation": self.simulation})

    def apply(self, transaction_id):
        transaction = self.status(transaction_id)
        if transaction["phase"] in {"committed", "rolled_back", "failed"}:
            return transaction
        self._version(transaction["plan"])
        with profile_operation(self.database, transaction["plan"]["profile_id"]):
            return self._apply(transaction_id)

    def _apply(self, transaction_id):
        transaction = self.status(transaction_id)
        if transaction["phase"] in {"committed", "rolled_back", "failed"}:
            return transaction
        require(transaction["phase"] == "planned", "RECOVERY_REQUIRED")
        plan = transaction["plan"]
        require(bool(plan["changes"]), "NO_CHANGE_REQUIRED")
        state = self.adapter.snapshot()
        self._qualified(state)
        require(self._policy(state) == plan["policy_digest"], "SETTINGS_POLICY_CHANGED")
        require(state["fingerprint"] == plan["fingerprint"] and state["revision"] == plan["revision"]
                and digest({k: v["key"] for k, v in state["bindings"].items()}) == plan["keymap_digest"],
                "REVISION_CONFLICT")
        with self.database.transaction() as db:
            self._idle(db, plan["profile_id"], transaction_id, transaction["agent"])
            result = db.execute("UPDATE control_transactions SET phase='applying' WHERE id=? "
                                "AND phase='planned'", (transaction_id,))
            require(result.rowcount == 1, "REVISION_CONFLICT")
            self.database.event(db, "controls.applying", {"transaction_id": transaction_id})
        try:
            self.adapter.stop_all()
            after = {name: value["after"] for name, value in plan["changes"].items()}
            if after:
                self.adapter.compare_and_swap(plan["revision"], after, transaction_id=transaction_id)
            self._phase(transaction_id, "verifying")
            verification = self.adapter.verify_and_restart(after, transaction_id=transaction_id,
                plan_digest=digest(plan), binding_checks=plan["binding_checks"])
            require(isinstance(verification, dict) and verification.get("transaction_id") == transaction_id
                    and verification.get("plan_digest") == digest(plan), "EFFECT_VERIFICATION_FAILED")
            checks = verification.get("checks", {})
            evidence_budget = {"remaining": plan["verification_byte_limit"], "sources": set()}
            require(set(plan["required_checks"]) <= set(checks) and all(
                self._valid_check(checks[name], plan, {"check": name, "binding_id": None,
                                  "context": None, "stage": None}, evidence_budget)
                for name in plan["required_checks"]), "EFFECT_VERIFICATION_FAILED")
            effects = verification.get("binding_checks", [])
            require(isinstance(effects, list) and len(effects) == len(plan["binding_checks"]),
                    "EFFECT_VERIFICATION_FAILED")
            for expected_check in plan["binding_checks"]:
                matches = [item for item in effects if isinstance(item, dict) and
                           all(item.get(key) == value for key, value in expected_check.items())]
                require(len(matches) == 1 and self._valid_check(matches[0], plan, expected_check, evidence_budget),
                        "EFFECT_VERIFICATION_FAILED")
            current = self.adapter.snapshot()
            self._qualified(current)
            require(self._policy(current) == plan["policy_digest"], "SETTINGS_POLICY_CHANGED")
            expected = plan["backup"] | after
            require(current["fingerprint"] == plan["fingerprint"] and
                    {k: v["key"] for k, v in current["bindings"].items()} == expected,
                    "RESTART_MISMATCH")
            self.adapter.stop_all()
            self._phase(transaction_id, "committed", {"verification": verification,
                        "revision": current["revision"], "keymap_digest": digest(expected)})
        except Exception:
            self._rollback(transaction_id)
            raise
        return self.status(transaction_id)

    def _valid_check(self, check, plan, expected, evidence_budget):
        valid = (isinstance(check, dict) and check.get("status") == "pass"
            and isinstance(check.get("refs"), list) and 0 < len(check["refs"]) <= 128
            and all(isinstance(ref, str) and re.fullmatch(r"cas:sha256:[0-9a-f]{64}", ref)
                    for ref in check["refs"]))
        if not valid:
            return False
        require(self.evidence_reader is not None, "EVIDENCE_STORE_REQUIRED")

        def unique(pairs):
            require(len(pairs) == len(dict(pairs)), "EFFECT_EVIDENCE_INVALID")
            return dict(pairs)

        for ref in check["refs"]:
            try:
                raw = self.evidence_reader(ref, max_bytes=min(65536, evidence_budget["remaining"]))
                require(isinstance(raw, bytes) and len(raw) <= 65536
                        and "cas:sha256:" + hashlib.sha256(raw).hexdigest() == ref,
                        "EFFECT_EVIDENCE_INVALID")
                evidence_budget["remaining"] -= len(raw)
                require(evidence_budget["remaining"] >= 0, "EFFECT_EVIDENCE_INVALID")
                proof = json.loads(raw, object_pairs_hook=unique)
                require(isinstance(proof, dict) and set(proof) == {
                    "schema", "transaction_id", "plan_digest", "check", "binding_id", "context",
                    "stage", "status", "is_example", "source_refs"}, "EFFECT_EVIDENCE_INVALID")
                require(proof["schema"] == "strata/ControlCheck/1"
                        and proof["transaction_id"] == plan["transaction_id"]
                        and proof["plan_digest"] == digest(plan) and proof["status"] == "pass"
                        and type(proof["is_example"]) is bool
                        and (self.simulation or proof["is_example"] is False)
                        and all(proof[key] == value for key, value in expected.items()),
                        "EFFECT_EVIDENCE_INVALID")
                require(isinstance(proof["source_refs"], list) and 0 < len(proof["source_refs"]) <= 128
                        and all(isinstance(source, str) and re.fullmatch(r"cas:sha256:[0-9a-f]{64}", source)
                                for source in proof["source_refs"]), "EFFECT_EVIDENCE_INVALID")
                for source in proof["source_refs"]:
                    if source in evidence_budget["sources"]:
                        continue
                    source_bytes = self.evidence_reader(source, max_bytes=evidence_budget["remaining"])
                    require(isinstance(source_bytes, bytes)
                            and len(source_bytes) <= evidence_budget["remaining"]
                            and "cas:sha256:" + hashlib.sha256(source_bytes).hexdigest() == source,
                            "EFFECT_EVIDENCE_INVALID")
                    evidence_budget["remaining"] -= len(source_bytes)
                    evidence_budget["sources"].add(source)
            except Exception:
                raise Fault("EFFECT_EVIDENCE_INVALID") from None
        return True

    def rollback(self, transaction_id):
        transaction = self.status(transaction_id)
        if transaction["phase"] == "rolled_back":
            return transaction
        self._version(transaction["plan"])
        with profile_operation(self.database, transaction["plan"]["profile_id"]):
            with self.database.transaction() as db:
                self._idle(db, transaction["plan"]["profile_id"], transaction_id, transaction["agent"])
            return self._rollback(transaction_id)

    def _rollback(self, transaction_id):
        transaction = self.status(transaction_id)
        if transaction["phase"] == "rolled_back":
            return transaction
        require(transaction["phase"] in {"applying", "verifying", "committed", "failed"},
                "INVALID_TRANSITION")
        plan = transaction["plan"]
        receipt = transaction["receipt"] or {}
        committed_revision = (receipt["revision"] if transaction["phase"] == "committed"
                              else receipt.get("committed_revision"))
        try:
            self.adapter.stop_all()
            state = self.adapter.snapshot()
            require(state["fingerprint"] == plan["fingerprint"], "BACKEND_MISMATCH")
            if committed_revision is not None:
                require(state["revision"] == committed_revision, "ROLLBACK_CONFLICT")
            require(self._policy(state) == plan["policy_digest"], "ROLLBACK_CONFLICT")
            require(set(state["bindings"]) == set(plan["backup"]), "ROLLBACK_CONFLICT")
            require(all(binding["key"] == plan["backup"][name]
                        for name, binding in state["bindings"].items() if name not in plan["changes"]),
                    "ROLLBACK_CONFLICT")
            changes = {}
            for name, change in plan["changes"].items():
                current = state["bindings"][name]["key"]
                require(current in (change["before"], change["after"]), "ROLLBACK_CONFLICT")
                if current == change["after"]:
                    changes[name] = change["before"]
            if changes:
                self.adapter.compare_and_swap(state["revision"], changes,
                                              transaction_id=transaction_id, rollback=True)
            final = self.adapter.snapshot()
            require(self._policy(final) == plan["policy_digest"]
                    and {name: binding["key"] for name, binding in final["bindings"].items()} == plan["backup"],
                    "ROLLBACK_FAILED")
            self.adapter.stop_all()
            self._phase(transaction_id, "rolled_back", {"revision": final["revision"]})
        except Exception:
            try:
                self.adapter.stop_all()
            except Exception:
                pass  # Failed release is fenced by the same durable recovery hold.
            failure = {"code": "ROLLBACK_REQUIRES_OPERATOR"}
            if committed_revision is not None:
                # A failed retry retains the authority of its original commit.
                # It cannot adopt a newer revision just because its phase changed.
                failure["committed_revision"] = committed_revision
            self._phase(transaction_id, "failed", failure)
            raise Fault("ROLLBACK_REQUIRES_OPERATOR") from None
        return self.status(transaction_id)
