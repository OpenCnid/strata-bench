"""Remaining canonical records, partitioned by authority at schema export.

Structural validation does not confer admission, provenance, or CAS access.
Cross-record checks are performed by the operator/evaluator services.
"""

from typing import Annotated, Literal

from pydantic import Field, JsonValue, model_validator

from .contracts import (
    MAX_INT, PUBLIC_RECORDS, Digest, Id, Key, Positive, Ref, Stream, Strict, UInt, Utc,
)

Probability = Annotated[float, Field(ge=0, le=1)]
SignedCount = Annotated[int, Field(ge=-MAX_INT, le=MAX_INT)]


class Pin(Strict):
    version: Annotated[str, Field(min_length=1)]
    digest: Digest


class Evidence(Strict):
    test_id: Id
    status: Literal["not_run", "pass", "fail"]
    refs: list[Ref]

    @model_validator(mode="after")
    def evidence_required(self):
        if self.status != "not_run" and not self.refs:
            raise ValueError("executed check requires evidence")
        return self


class Limits(Strict):
    active_wall_s: UInt
    input_tokens: UInt
    output_tokens: UInt
    model_calls: UInt
    primitive_events: UInt
    avatar_ticks: UInt
    practice_world_s: UInt
    spend_microusd: UInt | None


class FileEntry(Strict):
    path: str
    digest: Digest
    bytes: UInt
    role: Literal["client", "server", "both"]
    origin: str
    project_id: Positive | None
    file_id: Positive | None
    license_ref: str | None
    layer: Literal["distribution", "resolved", "harness"]


class Header(Strict):
    is_example: bool


class Loader(Strict):
    name: Literal["forge", "none"]
    version: str | None

    @model_validator(mode="after")
    def version_matches(self):
        if (self.name == "none") != (self.version is None):
            raise ValueError("loader version inconsistent")
        return self


class PackLock(Header):
    wire_schema: Literal["mcbench/PackLock/1"] = Field(alias="schema")
    lock_id: Id
    status: Literal["candidate", "sealed"]
    provider: Literal["curseforge"]
    pack_slug: str
    release: str
    project_id: Positive | None
    client_file_id: Positive | None
    server_file_id: Positive | None
    minecraft: str
    loader: Loader
    source_revision: str | None
    distribution_refs: list[Ref]
    resolved_inventory: Ref | None
    installed_root_digest: Digest | None
    java: Pin | None
    launcher: Pin | None
    launch_profile: Ref | None
    expert_assertions: Ref | None
    harness_additions: list[Ref]
    acquisition_report: Ref | None
    sealed_at: Utc | None

    @model_validator(mode="after")
    def sealed_fields(self):
        if self.status == "sealed":
            required = [self.java, self.launcher, self.launch_profile, self.resolved_inventory,
                        self.installed_root_digest, self.acquisition_report, self.sealed_at]
            if not self.distribution_refs or any(value is None for value in required):
                raise ValueError("incomplete sealed pack")
            if self.pack_slug == "enigmatica9expert" and any(value is None for value in
                    (self.client_file_id, self.server_file_id, self.expert_assertions)):
                raise ValueError("expert distribution/assertions required")
        return self


class BackendProfile(Strict):
    kind: Literal["mineflayer", "forge_client", "os_input"]
    implementation: Pin
    capability_manifest: Ref


class CampaignConfig(Header):
    wire_schema: Literal["mcbench/CampaignConfig/1"] = Field(alias="schema")
    campaign_id: Id
    lineage_id: Id
    cohort_id: Id
    system_digest: Digest
    pack_lock: Ref
    protocol_ref: Ref
    world_baseline: Ref
    track: Literal["structured-actions/v1", "pixels-input-settings/v1", "pixels-os/v1",
                   "semantic-assisted/v1"]
    backend: BackendProfile
    n: Positive
    agent_ids: list[Id]
    topology: Literal["shared_cooperative"]
    information_policy: Ref
    communication_policy: Ref
    runtime_profile: Ref
    budget_policy: Literal["fixed_team", "fixed_per_agent"]
    training_team_limits: Limits
    per_agent_limits: Limits
    evaluation_limits: Limits
    checkpoints_active_s: list[UInt]
    episode_s: Positive
    checkpoint_period_s: Positive
    admission: Literal["queue", "reject"]
    drift_policy: Literal["split_quarantine"]
    recovery_policy: Literal["terminate_confirmatory", "resume_development"]

    @model_validator(mode="after")
    def roster_and_schedule(self):
        if len(self.agent_ids) != self.n or len(set(self.agent_ids)) != self.n:
            raise ValueError("roster must contain N unique avatars")
        times = self.checkpoints_active_s
        if not times or times[0] != 0 or any(a >= b for a, b in zip(times, times[1:])):
            raise ValueError("checkpoint schedule must begin at zero and increase")
        if times[-1] > self.training_team_limits.active_wall_s:
            raise ValueError("checkpoint exceeds training duration")
        return self


class AgentConfig(Header):
    wire_schema: Literal["mcbench/AgentConfig/1"] = Field(alias="schema")
    agent_id: Id
    system_digest: Digest
    runtime: Pin
    provider: str
    requested_model: str
    immutable_model_id: str | None
    identity_assurance: Literal["immutable", "provider_version_unverified"]
    inference_config: Ref
    dovetail_commit: str
    dovetail_version: str
    initial_skills: Ref
    learned_overlay: Ref | None
    memory_policy: Ref
    capability_profile: Ref
    account_ref: Id
    provider_auth_ref: Id
    helper_limit: UInt
    helper_depth: UInt
    self_play: bool
    resume_mode: Literal["session", "fresh_handoff"]

    @model_validator(mode="after")
    def identity(self):
        if self.identity_assurance == "immutable" and not self.immutable_model_id:
            raise ValueError("immutable assurance requires model identity")
        return self


class GameEvent(Stream):
    wire_schema: Literal["mcbench/GameEvent/1"] = Field(alias="schema")
    server_boot_id: Id
    server_event_seq: UInt
    server_tick: UInt
    kind: str
    payload_schema: str
    payload: dict[str, JsonValue]
    actor_ids: list[Id]
    evidence_refs: list[Ref]
    visibility: Literal["evaluator"]


class SkillRevision(Header):
    wire_schema: Literal["mcbench/SkillRevision/1"] = Field(alias="schema")
    revision_id: Id
    agent_id: Id
    parent_revision_id: Id | None
    kind: Literal["initial", "notes", "procedure", "executable", "handoff"]
    content: Ref
    provenance_refs: list[Ref]
    generating_call_ids: list[Id]
    origin: Literal["initial", "campaign", "practice", "probe"]
    status: Literal["candidate", "active", "rejected"]
    activated_at: Utc | None

    @model_validator(mode="after")
    def activation(self):
        if (self.status == "active") != (self.activated_at is not None):
            raise ValueError("activation time inconsistent")
        return self


class BindingChange(Strict):
    binding_id: Id
    owner_mod: str
    owner_evidence: Ref
    contexts: list[str]
    context_confidence: Literal["known", "unknown"]
    before: Key
    after: Key
    protected: bool
    competing_binding_ids: list[Id]
    candidate_evidence: Ref
    checks: list[Evidence]


class KeybindingPatch(Stream):
    wire_schema: Literal["mcbench/KeybindingPatch/1"] = Field(alias="schema")
    agent_id: Id
    transaction_id: Id
    expected_revision: UInt
    expected_keymap_digest: Digest
    backend_fingerprint: Digest
    changes: list[BindingChange]
    backup_ref: Ref | None
    phase: Literal["planned", "applying", "verifying", "committed", "rolled_back", "failed"]
    resulting_revision: UInt | None
    resulting_keymap_digest: Digest | None
    restart_check: Evidence
    failure_code: str | None

    @model_validator(mode="after")
    def transaction(self):
        ids = [change.binding_id for change in self.changes]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("patch requires unique changed bindings")
        if self.phase == "committed":
            if (self.backup_ref is None or self.resulting_revision is None
                    or self.resulting_revision <= self.expected_revision
                    or self.resulting_keymap_digest is None or self.failure_code is not None
                    or self.restart_check.status != "pass"):
                raise ValueError("incomplete committed transaction")
            if any(not c.checks or any(e.status != "pass" for e in c.checks)
                   for c in self.changes):
                raise ValueError("all effects must pass before commit")
        return self


class AgentSnapshot(Strict):
    agent_id: Id
    workspace: Ref
    skills: Ref
    keymap: Ref | None
    backend_state: Ref
    runtime_state: Ref
    last_action_seq: UInt
    model_identity: str | None


class Clocks(Strict):
    active_wall_s: UInt
    elapsed_wall_s: UInt
    avatar_ticks: UInt

    @model_validator(mode="after")
    def clock_order(self):
        if self.active_wall_s > self.elapsed_wall_s:
            raise ValueError("active exposure exceeds elapsed time")
        return self


class CheckpointManifest(Header):
    wire_schema: Literal["mcbench/CheckpointManifest/1"] = Field(alias="schema")
    checkpoint_id: Id
    campaign_id: Id
    parent_checkpoint_id: Id | None
    status: Literal["preparing", "committed"]
    created_at: Utc
    source_epoch: UInt
    scheduled_active_s: UInt | None
    pack_lock: Ref
    system_digest: Digest
    server_boot_id: Id
    server_tick: UInt
    world_and_external_state: Ref
    agents: list[AgentSnapshot]
    event_cursor: UInt
    ledger_cursor: UInt
    clean_stop_report: Ref
    clocks: Clocks
    manifest_digest: Digest | None

    @model_validator(mode="after")
    def complete_manifest(self):
        ids = [a.agent_id for a in self.agents]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("checkpoint agents must be unique and nonempty")
        if (self.status == "committed") != (self.manifest_digest is not None):
            raise ValueError("committed digest required; staging digest must be null")
        return self


class Usage(Strict):
    input_tokens: SignedCount
    cached_input_tokens: SignedCount
    output_tokens: SignedCount
    reasoning_tokens: SignedCount | None
    model_calls: SignedCount
    primitive_events: SignedCount
    avatar_ticks: SignedCount
    wall_ms: SignedCount
    spend_microusd: SignedCount | None


class BudgetLedger(Stream):
    wire_schema: Literal["mcbench/BudgetLedger/1"] = Field(alias="schema")
    ledger_id: Id
    campaign_account: Literal["training", "evaluation", "development"]
    agent_id: Id | None
    operation_id: Id
    parent_operation_id: Id | None
    source_event_id: Id
    posting: Literal["reserve", "settle", "adjust"]
    kind: Literal["model", "helper", "tool", "practice", "body", "infrastructure"]
    usage: Usage
    metering: Literal["reported", "estimated", "unknown"]
    pricing_ref: Ref | None
    model_identity: str | None
    raw_usage_ref: Ref | None
    reason: str

    @model_validator(mode="after")
    def usage_semantics(self):
        if self.posting != "adjust":
            if any(v is not None and v < 0 for v in self.usage.model_dump().values()):
                raise ValueError("only reconciliation adjustments can be negative")
            if self.usage.cached_input_tokens > self.usage.input_tokens:
                raise ValueError("cached input is a subset, not additional input")
            if (self.usage.reasoning_tokens is not None
                    and self.usage.reasoning_tokens > self.usage.output_tokens):
                raise ValueError("reasoning is a subset of output")
        return self


class EvaluationProtocol(Header):
    wire_schema: Literal["mcbench/EvaluationProtocol/1"] = Field(alias="schema")
    protocol_id: Id
    visibility: Literal["evaluator"]
    preregistered_at: Utc
    system_digests: list[Digest]
    suite_digest: Digest
    sealed_instances: Ref
    scorer: Ref
    family_weights: dict[str, Annotated[float, Field(gt=0)]]
    exposure_s: list[UInt]
    primary_checkpoint_s: UInt
    probe_limits: Limits
    artifact_projection: Ref
    control_keymap: Ref | None
    primary_estimand: Literal["paired_success_gain"]
    sample_plan: Ref
    randomization_plan: Ref
    censoring_plan: Ref
    alpha: Probability
    min_effect: Probability
    retention_margin: Probability
    analysis_plan: Ref
    access_log: Ref

    @model_validator(mode="after")
    def registered_schedule(self):
        if not self.family_weights or not self.system_digests:
            raise ValueError("protocol requires systems and families")
        if self.primary_checkpoint_s not in self.exposure_s:
            raise ValueError("primary exposure must be scheduled")
        if any(a >= b for a, b in zip(self.exposure_s, self.exposure_s[1:])):
            raise ValueError("exposure schedule must strictly increase")
        return self


class EvaluationResult(Header):
    wire_schema: Literal["mcbench/EvaluationResult/1"] = Field(alias="schema")
    result_id: Id
    protocol_id: Id
    visibility: Literal["evaluator"]
    lineage_id: Id
    checkpoint_id: Id
    pair_id: Id
    instance_id: Id
    arm: Literal["experienced", "initial"]
    outcome: Literal["success", "failure", "censored", "invalid"]
    success: bool | None
    progress: Probability | None
    active_time_s: UInt
    event_observed: bool
    censor_reason: str | None
    scores: Ref
    evidence_refs: list[Ref]
    budget_ledger_ref: Ref
    validity_flags: list[str]
    scored_at: Utc

    @model_validator(mode="after")
    def outcome_consistency(self):
        if self.outcome == "success" and (self.success is not True or not self.event_observed):
            raise ValueError("success requires observed event")
        if self.outcome == "failure" and self.success is not False:
            raise ValueError("within-budget failure must be false")
        if self.outcome in {"censored", "invalid"} and not self.censor_reason:
            raise ValueError("missing outcome requires classified reason")
        if self.outcome == "invalid" and self.success is not None:
            raise ValueError("invalid success is not observable")
        if self.outcome == "censored" and not self.event_observed and self.success is not None:
            raise ValueError("unobserved censored success must remain null")
        return self


AGENT_RECORDS = (*PUBLIC_RECORDS, SkillRevision, KeybindingPatch)
OPERATOR_RECORDS = (PackLock, CampaignConfig, AgentConfig, CheckpointManifest, BudgetLedger)
EVALUATOR_RECORDS = (GameEvent, EvaluationProtocol, EvaluationResult)
CANONICAL_RECORDS = (*PUBLIC_RECORDS[:3], *AGENT_RECORDS[4:], *OPERATOR_RECORDS,
                     *EVALUATOR_RECORDS)
RECORDS = {model.model_fields["wire_schema"].annotation.__args__[0]: model
           for model in (*CANONICAL_RECORDS, PUBLIC_RECORDS[3])}
