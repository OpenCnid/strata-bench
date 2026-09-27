"""Private, read-only projection from a committed native campaign checkpoint.

This establishes artifact provenance only. A projection is not a clone manifest,
launch permit, isolation certificate or authority to return probe work to training.
"""

from typing import Literal

from pydantic import Field

from mcbench.contracts import Digest, Id, Ref, Strict, UInt
from mcbench.native_checkpoint import InitialArtifacts, check_files, parse_retention_policy
from mcbench.native_export import private_json
from mcbench.storage import digest, require, safe_relative

POLICY = "native-checkpoint-probe-artifact-projection/1"


class NativeProbeArtifactSelection(Strict):
    schema_: Literal["strata/NativeProbeArtifactSelection/1"] = Field(alias="schema")
    policy: Literal["native-checkpoint-probe-artifact-projection/1"]
    is_example: bool
    skill_set_ref: Ref
    initial_paths: list[str] = Field(min_length=1, max_length=1024)
    retained_paths: list[str] = Field(max_length=1024)
    skill_names: list[str] = Field(max_length=32)


class ProbeSkill(Strict):
    name: str
    description: str
    revision_id: Id
    kind: Literal["procedure", "executable"]
    files: dict[str, Ref]


class NativeProbeArtifactProjection(Strict):
    schema_: Literal["strata/NativeProbeArtifactProjection/1"] = Field(alias="schema")
    policy: Literal["native-checkpoint-probe-artifact-projection/1"]
    is_example: bool
    selection_digest: Digest
    skill_set_ref: Ref
    checkpoint_ref: Ref
    checkpoint_id: Id
    checkpoint_manifest_digest: Digest
    scheduled_active_s: UInt | None
    actual_active_s: UInt
    source_export: Ref
    campaign_id: Id
    agent_id: Id
    system_digest: Digest
    model_identity: str
    arm: Literal["full", "frozen-persistence", "frozen-skills", "no-self-play"]
    initial_files: dict[str, Ref]
    experienced_files: dict[str, Ref]
    experienced_skills: dict[str, ProbeSkill]
    session: None
    runtime_cache: None
    dispatch_authorized: Literal[False]
    campaign_feedback_allowed: Literal[False]


def _paths(paths):
    require(len(set(p.casefold() for p in paths)) == len(paths), "PROBE_PROJECTION_PATHS")
    for path in paths:
        parts = safe_relative(path).parts
        require(len(parts) > 1 and path.isascii() and len(path) <= 256, "PROBE_PROJECTION_PATHS")
        # These are state/configuration surfaces, not cognitive artifacts. This
        # structural check does not detect secrets or keymaps encoded as prose.
        require(not {p.casefold() for p in parts} & {
            "keymap.json", "options.txt", "session.json", "runtime_cache.json",
            "backend_state.json", "runtime_state.json", "auth.json", "credentials.json",
        }, "PROBE_STATE_FORBIDDEN")


def project_native_checkpoint(principal, sets, selection):
    """Derive refs/origins from source evidence, never caller-provided labels.

    The evaluator supplies an explicit reviewed path/name selection. Review of
    artifact contents and the protocol's permitted corpus remains necessary.
    All metadata in this result is private; only its admitted file/skill surface
    may be used by the later, separately gated clone builder.
    """
    require(principal.role in {"operator", "evaluator"}, "FORBIDDEN")
    selection = NativeProbeArtifactSelection.model_validate(selection)
    require(selection.is_example is sets.runtime.simulation, "PROBE_PROJECTION_MODE")
    _paths(selection.initial_paths)
    _paths(selection.retained_paths)
    require(len(set(selection.skill_names)) == len(selection.skill_names), "PROBE_PROJECTION_SKILLS")
    body = sets.load(selection.skill_set_ref)  # Reconstruct complete committed provenance.
    state, config = sets.components.load(body["checkpoint_ref"])
    manifest, namespace = sets.checkpoints.load(state.checkpoint_id, _native=sets.components)
    require(namespace == "operator" and config.system_digest == body["system_digest"], "PROBE_PROJECTION_SCOPE")
    exported = sets.publications.exports.load(state.source_export)
    source = private_json(sets.db.connection, sets.cas, exported.source_ref)
    require(source["account_identities"][0]["category"] in {"training", "development"}, "PROBE_IMPORT_FORBIDDEN")
    policy = parse_retention_policy(private_json(sets.db.connection, sets.cas, state.retention_policy))
    initial = InitialArtifacts.model_validate(private_json(sets.db.connection, sets.cas, policy.initial_artifacts)).files
    require(set(selection.initial_paths) <= set(initial), "PROBE_INITIAL_SOURCE")
    require({p for p in initial if p.startswith(("initial/", "skills/"))} <= set(selection.initial_paths),
            "PROBE_INITIAL_PROCEDURES_REQUIRED")
    require(all(p.startswith(("initial/", "skills/", "docs/", "supplied/", "notes/", "handoff/"))
                for p in selection.initial_paths), "PROBE_PROJECTION_PATHS")
    baseline = {p: initial[p] for p in selection.initial_paths}
    files = dict(baseline)
    if policy.arm == "frozen-persistence":
        # Recovery may contain short-term knowledge. It is never a permitted
        # experienced probe advantage for this arm.
        require(not selection.retained_paths and not selection.skill_names, "PROBE_FROZEN_PERSISTENCE")
    if policy.arm == "frozen-skills":
        require(policy.schema_ == "strata/NativeRetentionPolicy/2" and not selection.skill_names,
                "PROBE_FROZEN_SKILLS")
    require(all(p.startswith(("notes/", "handoff/")) and p in body["workspace"]
                for p in selection.retained_paths), "PROBE_RETAINED_SOURCE")
    files.update({p: body["workspace"][p] for p in selection.retained_paths})
    require(set(selection.skill_names) <= set(body["skills"]), "PROBE_ACTIVE_SKILL_REQUIRED")
    skills = {}
    for name in selection.skill_names:
        value = body["skills"][name]
        revision = value["revision"]
        require(revision["origin"] == "campaign" and revision["status"] == "active", "PROBE_IMPORT_FORBIDDEN")
        skills[name] = ProbeSkill(name=name, description=value["metadata"]["description"],
            revision_id=revision["revision_id"], kind=revision["kind"], files=value["files"])
    # The union can exceed quotas or introduce case aliases even when the two
    # independently valid source inventories did not. Recheck the final surface.
    learned = {"active/" + name + "/" + p: r for name, value in skills.items() for p, r in value.files.items()}
    _paths(list(baseline))
    _paths(list(files | learned))
    check_files(sets.cas, baseline)
    check_files(sets.cas, files | learned)
    return NativeProbeArtifactProjection.model_validate({
        "schema": "strata/NativeProbeArtifactProjection/1", "policy": POLICY,
        "is_example": selection.is_example, "selection_digest": digest(selection.model_dump()),
        "skill_set_ref": selection.skill_set_ref, "checkpoint_ref": body["checkpoint_ref"],
        "checkpoint_id": state.checkpoint_id, "checkpoint_manifest_digest": manifest.manifest_digest,
        "scheduled_active_s": manifest.scheduled_active_s, "actual_active_s": manifest.clocks.active_wall_s,
        "source_export": state.source_export, "campaign_id": state.campaign_id, "agent_id": state.agent_id,
        "system_digest": state.system_digest, "model_identity": state.model_identity, "arm": policy.arm,
        "initial_files": baseline, "experienced_files": files, "experienced_skills": skills,
        "session": None, "runtime_cache": None, "dispatch_authorized": False,
        "campaign_feedback_allowed": False})
