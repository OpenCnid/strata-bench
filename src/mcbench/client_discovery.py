"""Operator-only audit of the unqualified Forge client discovery export.

This validates a diagnostic file, not its producer's identity, input effects or
settings capability. It is never included in the gameplay tool package.
"""

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Digest, Id, Key, Positive, Strict, UInt
from .storage import reject_links, require

MAX_SNAPSHOT_BYTES = 524288
MAX_OPTIONS_BYTES = 1048576


def stable_id(owner: str, translation: str, occurrence: int) -> str:
    key = translation if re.fullmatch(r"[A-Za-z0-9_.:-]{1,48}", translation) else (
        "sha256-" + hashlib.sha256(translation.encode()).hexdigest()[:32])
    return f"{owner}:{key}:{occurrence}"


class DiscoveredBinding(Strict):
    translation_id: str = Field(min_length=1, max_length=2048)
    registration_occurrence: UInt
    label: str = Field(max_length=4096)
    category: str = Field(max_length=2048)
    owner_mod: Literal["minecraft", "unknown"]
    owner_basis: str = Field(max_length=256)
    owner_evidence: None
    ambiguous_occurrence: bool
    persisted_ambiguous: bool
    persisted_value: str | None = Field(max_length=2048)
    key: Key
    default_key: Key
    contexts: list[Literal["UNIVERSAL", "IN_GAME", "GUI", "CUSTOM"]] = Field(
        min_length=1, max_length=1)
    context_confidence: Literal["known", "unknown"]
    protected: bool
    consumer_tested: bool
    mutation_supported: bool

    @model_validator(mode="after")
    def diagnostic_only(self):
        require(self.protected is True and self.consumer_tested is False
                and self.mutation_supported is False, "UNQUALIFIED_CAPABILITY_CLAIM")
        require(self.key.backend == self.default_key.backend == "glfw", "BACKEND_MISMATCH")
        require((self.contexts == ["CUSTOM"]) == (self.context_confidence == "unknown"),
                "CONTEXT_EVIDENCE_MISMATCH")
        require(not self.persisted_ambiguous or self.persisted_value is None,
                "AMBIGUOUS_PERSISTED_VALUE")
        require(self.owner_basis == "unresolved" if self.owner_mod == "unknown"
                else self.owner_basis.startswith("minecraft:Options."), "OWNER_BASIS_MISMATCH")
        return self


class DiscoverySnapshot(Strict):
    wire_schema: Literal["strata/ForgeBindingDiscovery/1"] = Field(alias="schema")
    backend: Literal["glfw"]
    module: Literal["strata-forge1192-client/0.1.0"]
    supported: bool
    discovery_supported: bool
    atomic_cas: bool
    restart_tested: bool
    layout_verified: bool
    revision: Positive
    keymap_digest: Digest
    options_file_sha256: Digest | None
    persisted_file_present: bool
    bindings: dict[Id, DiscoveredBinding] = Field(min_length=1, max_length=2048)
    tested_pool: list = Field(max_length=0)
    operator_development_only: bool

    @model_validator(mode="after")
    def consistent_discovery(self):
        require(self.supported is False and self.atomic_cas is False
                and self.restart_tested is False and self.layout_verified is False
                and self.discovery_supported is True and self.operator_development_only is True,
                "UNQUALIFIED_CAPABILITY_CLAIM")
        require(self.persisted_file_present == (self.options_file_sha256 is not None),
                "PERSISTENCE_EVIDENCE_MISMATCH")
        totals = Counter(binding.translation_id for binding in self.bindings.values())
        seen = Counter()
        for identifier, binding in self.bindings.items():
            translation = binding.translation_id
            require(binding.registration_occurrence == seen[translation]
                    and identifier == stable_id(binding.owner_mod, translation, seen[translation]),
                    "BINDING_ID_MISMATCH")
            require(binding.ambiguous_occurrence == (totals[translation] != 1),
                    "AMBIGUOUS_OCCURRENCE_MISMATCH")
            require(self.persisted_file_present or (binding.persisted_value is None
                    and not binding.persisted_ambiguous), "PERSISTENCE_EVIDENCE_MISMATCH")
            seen[translation] += 1
        return self


def bounded_read(path: Path, limit: int) -> bytes:
    reject_links(path.absolute())
    require(path.is_file(), "DISCOVERY_FILE_UNAVAILABLE")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, "DISCOVERY_FILE_TOO_LARGE")
    return data


def unique_fields(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, "DUPLICATE_JSON_FIELD")
        result[name] = value
    return result


def inspect_discovery(path: Path, options: Path | None = None) -> dict:
    raw = bounded_read(path, MAX_SNAPSHOT_BYTES)
    snapshot = DiscoverySnapshot.model_validate(json.loads(raw, object_pairs_hook=unique_fields))
    mismatches = [name for name, binding in snapshot.bindings.items()
                  if binding.persisted_value is not None
                  and binding.persisted_value != binding.key.persisted]
    report = {
        "schema": "strata/ClientDiscoveryAudit/1", "operator_development_only": True,
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "binding_count": len(snapshot.bindings),
        "owner_counts": dict(Counter(b.owner_mod for b in snapshot.bindings.values())),
        "ambiguous_occurrences": [n for n, b in snapshot.bindings.items() if b.ambiguous_occurrence],
        "ambiguous_persistence": [n for n, b in snapshot.bindings.items() if b.persisted_ambiguous],
        "unknown_contexts": [n for n, b in snapshot.bindings.items()
                             if b.context_confidence == "unknown"],
        "runtime_persistence_mismatches": mismatches,
        "unknown_persisted_values": [n for n, b in snapshot.bindings.items()
                                     if b.persisted_value is None],
        "persisted_file_present_at_snapshot": snapshot.persisted_file_present,
        "options_file_sha256_at_snapshot": snapshot.options_file_sha256,
        "options_file_match_at_audit": None,
        "format_result": "pass", "keybinding_capability_qualified": False,
        "producer_authenticated": False, "effects_verified": False,
        "restart_verified": False, "gate_result": "not_run",
    }
    if options is not None:
        reject_links(options.absolute())
        actual = hashlib.sha256(bounded_read(options, MAX_OPTIONS_BYTES)).hexdigest() \
            if options.exists() else None
        report["options_file_match_at_audit"] = actual == snapshot.options_file_sha256
        report["options_file_sha256_at_audit"] = actual
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--options", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = inspect_discovery(args.snapshot, args.options)
    reject_links(args.output.absolute())
    with args.output.open("xb") as stream:
        stream.write((json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"status": "inspected", "binding_count": report["binding_count"],
                      "format_result": report["format_result"], "gate_result": "not_run"}))


if __name__ == "__main__":
    main()
