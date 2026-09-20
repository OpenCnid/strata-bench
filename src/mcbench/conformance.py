"""Exact-target preflight; missing files remain blockers, never synthetic compatibility passes."""

import hashlib
from pathlib import Path
from typing import Literal

from mcbench.contracts import Digest, Strict

TARGETS = {
    "vanilla": {"minecraft": "1.19.2", "provider": "curseforge", "loader": "none"},
    "e9e": {
        "minecraft": "1.19.2",
        "provider": "curseforge",
        "loader": "forge",
        "release": "1.27.0",
        "client_file_id": 8161120,
        "server_file_id": 8161123,
    },
}
CASES = {
    "vanilla": [
        "official_vanilla_workflow",
        "authentic_server_and_identity",
        "observe_and_filter",
        "move_mine_place_equip_use",
        "single_recipe_craft",
        "container_transaction",
        "cancel_disconnect_reconnect",
        "private_milestone_controls",
        "complete_costs_and_clocks",
    ],
    "e9e": [
        "official_archives_and_bootstrap",
        "cold_start_expert_config_recipe_quest",
        "forge_handshake_required_channels",
        "namespaced_registry_metadata",
        "collision_navigation",
        "expert_altered_recipe",
        "modded_container_transaction",
        "operating_machine_energy_fluid",
        "player_recipe_quest_surface",
        "server_evidence_and_reference_parity",
    ],
}


class Artifact(Strict):
    path: str
    sha256: Digest
    role: Literal["client", "server"]
    file_id: int | None


class AcquisitionInputs(Strict):
    target: Literal["vanilla", "e9e"]
    is_example: bool
    provider: Literal["curseforge"]
    artifacts: list[Artifact]


def preflight(target: str, inputs: AcquisitionInputs | None = None) -> dict:
    if target not in TARGETS:
        raise ValueError("CAPABILITY_MISSING")
    reasons = []
    verified_hashes = []
    if inputs is None or not inputs.artifacts:
        reasons.append("AWAITING_ARTIFACT")
    else:
        if inputs.is_example:
            reasons.append("EXAMPLE_NOT_EXECUTABLE")
        if inputs.target != target:
            reasons.append("RELEASE_MISMATCH")
        roles = [a.role for a in inputs.artifacts]
        if sorted(roles) != ["client", "server"]:
            reasons.append("AWAITING_ARTIFACT")
        for artifact in inputs.artifacts:
            if target == "e9e" and artifact.file_id != TARGETS[target][f"{artifact.role}_file_id"]:
                reasons.append("RELEASE_MISMATCH")
            path = Path(artifact.path)
            if not path.is_absolute() or not path.is_file():
                reasons.append("AWAITING_ARTIFACT")
                continue
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != artifact.sha256:
                reasons.append("HASH_MISMATCH")
            else:
                verified_hashes.append({"role": artifact.role, "sha256": actual})
    reasons += [
        "OFFICIAL_ACQUISITION_RECEIPT_UNVERIFIED",
        "INSTALLED_INVENTORY_UNVERIFIED",
        "AWAITING_OPERATOR_AUTH",
        "ISOLATION_UNVERIFIED",
    ]
    if target == "e9e":
        reasons.append("MECHANIC_UNSUPPORTED")
    return {
        "schema": "strata/ConformancePreflight/1",
        "target": target,
        "candidate": TARGETS[target],
        "status": "blocked",
        "gate": "G0",
        "gate_result": "not_run",
        "blockers": list(dict.fromkeys(reasons)),
        "verified_distribution_hashes": verified_hashes,
        "cases": [
            {"id": f"M0.{'3' if target == 'e9e' else '2'}.{i}", "case": case, "result": "not_run"}
            for i, case in enumerate(CASES[target], start=1)
        ],
        "compatibility_claim": None,
    }
