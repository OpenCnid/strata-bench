"""Private qualified native settings reader; writes use the owned repair flow.

Qualification reports are operator-issued evidence, not inferred from a native
snapshot, a successful launch, or this parser. No report producer or gameplay
capability is installed here. A real profile without actual reports is blocked.
"""

import hashlib
import time
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Digest, Id, Key, Positive, Ref, Strict
from .controls import Controls
from .native_control_plan import KEYSYMS, NativeEssentialTarget, native_key
from .native_settings import NativeSnapshot, strict_json
from .native_settings_effects import NativeSettingsEffectsClient
from .native_game import NativeGameClient
from .storage import Fault, digest, require

CHECKS = {"atomic_cas", "restart_persistence", "essential_controls", "isolated_settings", "binding_metadata"}
LIMIT = 4 * 1024 * 1024


class SettingsIdentity(Strict):
    profile_id: Id
    game_fingerprint: Digest
    settings_fingerprint: Digest
    body_fingerprint: Digest
    input_policy: Literal["native-window-key-mouse-fixed-escape/5", "native-window-key-mouse-sprint-companion/6"]
    layout_digest: Digest


class BindingPolicy(Strict):
    translation: str = Field(min_length=1, max_length=256)
    contexts: list[Literal["IN_GAME", "GUI", "UNIVERSAL", "CUSTOM"]] = Field(min_length=1, max_length=4)
    context_confidence: Literal["known", "unknown"]
    protected: bool
    consumer_tested: bool
    owner_evidence: Ref | None

    @model_validator(mode="after")
    def conservative(self):
        require(len(self.contexts) == len(set(self.contexts)), "SETTINGS_QUALIFICATION_INVALID")
        require("CUSTOM" not in self.contexts or self.context_confidence == "unknown", "SETTINGS_QUALIFICATION_INVALID")
        require(self.protected or self.consumer_tested and self.owner_evidence is not None,
                "SETTINGS_QUALIFICATION_INVALID")
        return self


class PoolEntry(Strict):
    key: Key
    evidence_ref: Ref


class SettingsQualification(Strict):
    schema_: Literal["strata/NativeSettingsQualification/1"] = Field(alias="schema")
    is_example: bool
    identity: SettingsIdentity
    expires_unix_ms: Positive
    bindings: dict[Id, BindingPolicy] = Field(min_length=1, max_length=2048)
    tested_pool: list[PoolEntry] = Field(min_length=1, max_length=128)
    checks: dict[str, Ref]
    consumers: dict[Id, Ref]

    @model_validator(mode="after")
    def complete(self):
        require(set(self.checks) == CHECKS and set(self.consumers) == {
            name for name, binding in self.bindings.items() if binding.consumer_tested}, "SETTINGS_QUALIFICATION_INCOMPLETE")
        keys = [native_key(entry.key.model_dump()) for entry in self.tested_pool]
        require(len(keys) == len(set(keys)) and all(entry.key.representation != "unbound" for entry in self.tested_pool),
                "SETTINGS_QUALIFICATION_INVALID")
        return self


class SettingsCheck(Strict):
    schema_: Literal["strata/NativeSettingsQualificationCheck/1"] = Field(alias="schema")
    is_example: bool
    identity_digest: Digest
    check: Literal["atomic_cas", "restart_persistence", "essential_controls", "isolated_settings", "binding_metadata",
                   "consumer", "physical_key", "owner"]
    subject_digest: Digest
    result: Literal["pass", "fail", "blocked", "not_run"]
    source_refs: list[Ref] = Field(min_length=1, max_length=32)


def decode_native_key(value):
    """Exact inverse encoding; names are persisted identifiers, never localized labels."""
    require(isinstance(value, str), "SETTINGS_KEY_ENCODING_UNSUPPORTED")
    parts = value.split(":")
    require(1 <= len(parts) <= 2 and (len(parts) == 1 or parts[1] in {"SHIFT", "CONTROL", "ALT"}),
            "SETTINGS_KEY_ENCODING_UNSUPPORTED")
    base, modifiers = parts[0], parts[1:]
    if base == "key.keyboard.unknown":
        representation, code = "unbound", None
    elif base.startswith("key.keyboard."):
        inverse = {name: code for code, name in KEYSYMS.items()}
        require(base[13:] in inverse, "SETTINGS_KEY_ENCODING_UNSUPPORTED")
        representation, code = "keysym", inverse[base[13:]]
    elif base.startswith("key.mouse."):
        inverse = {"left": 0, "right": 1, "middle": 2, **{str(i + 1): i for i in range(3, 8)}}
        require(base[10:] in inverse, "SETTINGS_KEY_ENCODING_UNSUPPORTED")
        representation, code = "mouse_button", inverse[base[10:]]
    else:
        require(base.startswith("scancode.") and base[9:].isascii() and base[9:].isdecimal(), "SETTINGS_KEY_ENCODING_UNSUPPORTED")
        representation, code = "scancode", int(base[9:])
    key = Key.model_validate({"backend": "glfw", "representation": representation, "code": code,
        "name": base, "modifiers": modifiers, "persisted": value}).model_dump()
    require(native_key(key) == value, "SETTINGS_KEY_ENCODING_MISMATCH")
    return key


class NativeSettingsProjection:
    """Reads exact native state using a pinned operator qualification and CAS reader.

    Rebinding must be performed only after the controller adopts the replacement;
    construct a new reader with the same qualification. This object never launches
    a client, discovers credentials, writes settings, or releases an input hold.
    """

    def __init__(self, client, qualification_ref, evidence_reader, *, simulation=False, clock=time.time):
        require(isinstance(client, NativeSettingsEffectsClient) and type(simulation) is bool, "SETTINGS_PROFILE_MISMATCH")
        self.client, self.qualification_ref, self.evidence_reader = client, qualification_ref, evidence_reader
        self.game = NativeGameClient(client.connection)
        self.simulation, self.clock = simulation, clock

    def read_evidence(self, ref, *, max_bytes):
        return self.evidence_reader(ref, max_bytes=max_bytes)

    def _read(self, ref, budget):
        require(isinstance(ref, str) and ref.startswith("cas:sha256:") and len(ref) == 75, "SETTINGS_EVIDENCE_INVALID")
        if ref not in budget["cache"]:
            try:
                raw = self.evidence_reader(ref, max_bytes=min(524288, budget["remaining"]))
            except (OSError, KeyError):
                raise Fault("SETTINGS_EVIDENCE_UNAVAILABLE") from None
            require(isinstance(raw, bytes) and len(raw) <= min(524288, budget["remaining"])
                    and hashlib.sha256(raw).hexdigest() == ref[11:], "SETTINGS_EVIDENCE_INVALID")
            budget["remaining"] -= len(raw)
            budget["cache"][ref] = raw
        return budget["cache"][ref]

    def _qualified(self):
        budget = {"remaining": LIMIT, "cache": {}}
        proof = SettingsQualification.model_validate(strict_json(self._read(self.qualification_ref, budget)))
        identity = proof.identity
        require(proof.is_example is self.simulation and proof.expires_unix_ms > self.clock() * 1000
                and identity.game_fingerprint == self.client.connection.fingerprint
                and identity.settings_fingerprint == self.client.settings_fingerprint, "SETTINGS_UNQUALIFIED")
        identity_digest = digest(identity.model_dump())

        def check(ref, name, subject):
            item = SettingsCheck.model_validate(strict_json(self._read(ref, budget)))
            require(item.is_example is self.simulation and item.result == "pass" and item.identity_digest == identity_digest
                    and item.check == name and item.subject_digest == digest(subject), "SETTINGS_UNQUALIFIED")
            for source in item.source_refs:
                self._read(source, budget)

        catalog = {name: b.model_dump() for name, b in proof.bindings.items()}
        for name, ref in proof.checks.items():
            check(ref, name, catalog if name == "binding_metadata" else identity.model_dump())
        for name, binding in proof.bindings.items():
            subject = {"binding_id": name, "translation": binding.translation}
            if binding.owner_evidence:
                check(binding.owner_evidence, "owner", subject)
            if binding.consumer_tested:
                check(proof.consumers[name], "consumer", {"binding_id": name, "policy": binding.model_dump()})
        for entry in proof.tested_pool:
            check(entry.evidence_ref, "physical_key", entry.key.model_dump())
        return proof

    def snapshot(self):
        proof = self._qualified()  # Missing authority fails before contacting a client.
        identity = self.game.call("identity", {}, timeout_ms=1000)
        require(identity["body_fingerprint"] == proof.identity.body_fingerprint, "SETTINGS_PROFILE_MISMATCH")
        head = NativeSnapshot.model_validate(self.client.call("settings_snapshot", {}, timeout_ms=1000))
        require(self.game.call("identity", {}, timeout_ms=1000) == identity, "SETTINGS_PROFILE_MISMATCH")
        require(head.fingerprint == proof.identity.settings_fingerprint and set(head.bindings) == set(proof.bindings),
                "SETTINGS_PROFILE_MISMATCH")
        bindings = {}
        for name, native in head.bindings.items():
            policy = proof.bindings[name]
            require(native.translation == policy.translation and not native.persisted_ambiguous
                    and native.persisted_value == native.runtime_value and (policy.protected or native.operator_mutable),
                    "SETTINGS_STATE_MISMATCH")
            bindings[name] = policy.model_dump(exclude={"translation"}) | {"key": decode_native_key(native.runtime_value)}
        require(proof.expires_unix_ms > self.clock() * 1000, "SETTINGS_UNQUALIFIED")
        return {"supported": True, "atomic_cas": True, "restart_tested": True, "backend": "glfw",
            "profile_id": proof.identity.profile_id, "fingerprint": digest({"identity": proof.identity.model_dump(),
                "qualification_ref": self.qualification_ref}), "revision": head.revision, "bindings": bindings,
            "tested_pool": [entry.model_dump() for entry in proof.tested_pool]}

    def target(self):
        state = self.snapshot()
        proof = self._qualified()
        return NativeEssentialTarget.model_validate({"schema": "strata/NativeControlTarget/2",
            "profile_id": state["profile_id"], "control_fingerprint": state["fingerprint"],
            "policy_digest": Controls._policy(state), "game_fingerprint": proof.identity.game_fingerprint,
            "settings_fingerprint": proof.identity.settings_fingerprint, "body_fingerprint": proof.identity.body_fingerprint,
            "fixed_controls": ["escape"]})

    def compare_and_swap(self, *args, **kwargs):
        require(False, "NATIVE_SETTINGS_ADAPTER_REQUIRED")

    def verify_and_restart(self, *args, **kwargs):
        require(False, "NATIVE_SETTINGS_ADAPTER_REQUIRED")

    def stop_all(self):
        require(False, "NATIVE_SETTINGS_ADAPTER_REQUIRED")
