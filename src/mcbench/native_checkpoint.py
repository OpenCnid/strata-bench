"""Preregistered native retention and source-bound checkpoint components.

These private records stage fresh-handoff artifacts. They do not grant runtime
dispatch, qualify game persistence, or activate draft skills.
"""

import json
from contextlib import nullcontext
from typing import Literal

from pydantic import Field

from .broker import MAX_TEXT
from .contracts import Digest, Id, Positive, Ref, Strict
from .native_export import MAX_METADATA, OPERATOR, NativeExports, private_json
from .records import AgentConfig, CampaignConfig
from .storage import Principal, canonical, require, safe_relative

POLICY = "native-preregistered-retention-checkpoint/1"
ARMS = Literal["full", "frozen-persistence", "frozen-skills", "no-self-play"]


class InitialArtifacts(Strict):
    schema_: Literal["strata/NativeInitialArtifacts/1"] = Field(alias="schema")
    files: dict[str, Ref]


class NativeRetentionPolicy(Strict):
    schema_: Literal["strata/NativeRetentionPolicy/1"] = Field(alias="schema")
    is_example: bool
    policy: Literal["native-preregistered-retention-checkpoint/1"]
    campaign_id: Id
    agent_id: Id
    system_digest: Digest
    arm: ARMS
    initial_artifacts: Ref
    resume_mode: Literal["fresh_handoff"]


class NativeCheckpointState(Strict):
    schema_: Literal["strata/NativeCheckpointState/1"] = Field(alias="schema")
    is_example: bool
    policy: Literal["native-preregistered-retention-checkpoint/1"]
    checkpoint_id: Id
    campaign_id: Id
    agent_id: Id
    source_epoch: Positive
    system_digest: Digest
    profile_digest: Digest
    model_identity: str
    source_export: Ref
    retention_policy: Ref
    boundary: Literal["episode", "recovery"]
    workspace: Ref
    skills: Ref
    resume_mode: Literal["fresh_handoff"]
    session: None
    runtime_cache: None
    cost_rollback: Literal[False]
    dispatch_authorized: Literal[False]


def check_files(cas, files, namespace="operator", role="operator"):
    """Validate a whole projected root inventory, including aggregate handoff size."""
    require(isinstance(files, dict) and len(files) <= 1024, "ARTIFACT_QUOTA")
    folded = {p.casefold() for p in files}
    require(len(folded) == len(files), "AMBIGUOUS_PATHS")
    total = handoff = 0
    for path, ref in files.items():
        relative = safe_relative(path)
        require(path.isascii() and len(path) <= 256 and len(relative.parts) > 1 and
            relative.parts[0] in {"initial", "docs", "supplied", "notes", "skills", "handoff"} and
            not any(str(p).casefold() in folded for p in relative.parents if str(p) != "."), "AMBIGUOUS_PATHS")
        require(not {p.casefold() for p in relative.parts} & {
            ".git", ".codex", ".ssh", ".aws", "auth.json", "credentials.json", "keys.json",
            "launcher_accounts.json", "launcher_msa_credentials.bin", "auth-cache", "auth_cache"},
            "SECRET_IN_SNAPSHOT")
        raw = cas.read(Principal(namespace, role), namespace, ref, max_bytes=MAX_TEXT)
        raw.decode("utf-8", errors="strict")
        if namespace == "operator":
            row = cas.database.connection.execute("SELECT visibility FROM objects WHERE namespace=? AND ref=?",
                                                   (namespace, ref)).fetchone()
            require(row[0] == "operator", "NATIVE_EXPORT_PRIVATE")
        total += len(raw)
        if relative.parts[0] == "handoff":
            handoff += len(raw)
    require(total <= 20 * 1024 * 1024 and handoff <= 8000, "ARTIFACT_QUOTA")


class NativeCheckpointStates:
    def __init__(self, runtime):
        self.runtime, self.db, self.cas = runtime, runtime.db, runtime.cas
        self.exports = NativeExports(runtime)
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_retention_policies (campaign TEXT, agent TEXT, "
                "ref TEXT, config TEXT, agent_config TEXT, PRIMARY KEY(campaign,agent))")
            db.execute("CREATE TABLE IF NOT EXISTS native_checkpoint_states (checkpoint TEXT, agent TEXT, "
                "ref TEXT, PRIMARY KEY(checkpoint,agent))")

    def _controller_mode(self):
        db = self.db.connection
        require(db.execute("SELECT 1 FROM sqlite_master WHERE name='controller_profile'").fetchone(), "PROFILE_MISMATCH")
        mode = db.execute("SELECT simulation FROM controller_profile").fetchone()
        require(mode is not None and mode[0] == int(self.runtime.simulation), "PROFILE_MISMATCH")

    def register(self, config: CampaignConfig, agent: AgentConfig):
        """Freeze the declared baseline before any native job in this lineage."""
        self._controller_mode()
        policy = NativeRetentionPolicy.model_validate(private_json(self.db.connection, self.cas, agent.memory_policy))
        require(not config.is_example and not agent.is_example and policy.is_example is self.runtime.simulation and
            policy.campaign_id == config.campaign_id and policy.agent_id == agent.agent_id and
            agent.agent_id in config.agent_ids and policy.system_digest == config.system_digest == agent.system_digest
            and agent.initial_skills == policy.initial_artifacts and agent.resume_mode == "fresh_handoff" and
            (policy.arm != "no-self-play" or agent.self_play is False), "NATIVE_RETENTION_SCOPE")
        initial = InitialArtifacts.model_validate(private_json(self.db.connection, self.cas, policy.initial_artifacts))
        check_files(self.cas, initial.files)
        values = (config.campaign_id, agent.agent_id, agent.memory_policy,
                  canonical(config.model_dump()).decode(), canonical(agent.model_dump()).decode())
        with self.db.transaction() as db:
            old = db.execute("SELECT * FROM native_retention_policies WHERE campaign=? AND agent=?", values[:2]).fetchone()
            if old:
                require(tuple(old) == values, "IDEMPOTENCY_CONFLICT")
                return agent.memory_policy
            require(db.execute("SELECT 1 FROM sqlite_master WHERE name='campaigns'").fetchone(), "NATIVE_RETENTION_SCOPE")
            campaign = db.execute("SELECT config,agents FROM campaigns WHERE id=?", (config.campaign_id,)).fetchone()
            require(campaign is not None and json.loads(campaign["config"]) == config.model_dump() and
                agent.model_dump() in json.loads(campaign["agents"]), "NATIVE_RETENTION_SCOPE")
            require(db.execute("SELECT 1 FROM native_jobs WHERE campaign=? AND agent=?", values[:2]).fetchone() is None,
                    "NATIVE_RETENTION_TOO_LATE")
            db.execute("INSERT INTO native_retention_policies VALUES(?,?,?,?,?)", values)
            self.db.event(db, "native.retention_registered", {"campaign": config.campaign_id,
                "agent": agent.agent_id, "policy_ref": agent.memory_policy})
        return agent.memory_policy

    def _derive(self, state, boundary):
        db = self.db.connection
        registered = db.execute("SELECT * FROM native_retention_policies WHERE campaign=? AND agent=?",
                                (state.campaign_id, state.agent_id)).fetchone()
        require(registered is not None, "NATIVE_RETENTION_NOT_REGISTERED")
        self._controller_mode()
        config = CampaignConfig.model_validate_json(registered["config"])
        agent = AgentConfig.model_validate_json(registered["agent_config"])
        policy = NativeRetentionPolicy.model_validate(private_json(db, self.cas, registered["ref"]))
        require(policy.is_example is self.runtime.simulation and policy.campaign_id == state.campaign_id and
            policy.agent_id == state.agent_id and policy.system_digest == config.system_digest == agent.system_digest and
            policy.initial_artifacts == agent.initial_skills and registered["ref"] == agent.memory_policy,
            "NATIVE_RETENTION_SCOPE")
        initial = InitialArtifacts.model_validate(private_json(db, self.cas, policy.initial_artifacts)).files
        inventory = private_json(db, self.cas, state.root_artifacts)
        current = {x["path"]: x["ref"] for x in inventory["files"]}
        check_files(self.cas, initial)
        check_files(self.cas, current, inventory["namespace"], "executor")
        def immutable(path):
            return path.split("/")[0] in {"initial", "docs", "supplied"}
        require({k: v for k, v in initial.items() if immutable(k)} ==
                {k: v for k, v in current.items() if immutable(k)}, "NATIVE_INITIAL_CHANGED")
        # An active revision is a separate capability with provenance, activation
        # and supporting files. Never silently turn it into a broker draft.
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='revisions'").fetchone():
            require(db.execute("SELECT 1 FROM revisions WHERE agent=? AND active=1 AND namespace IN (?,?)",
                (state.agent_id, inventory["namespace"], f"campaign:{state.campaign_id}:agent:{state.agent_id}")).fetchone()
                is None, "NATIVE_REVISION_EXPORT_REQUIRED")
        if boundary == "episode" and policy.arm == "frozen-persistence":
            files = initial
        elif boundary == "episode" and policy.arm == "frozen-skills":
            files = {k: v for k, v in initial.items() if immutable(k) or k.startswith("skills/")}
            files |= {k: v for k, v in current.items() if k.startswith(("notes/", "handoff/"))}
        else:
            files = current
        return registered, policy, config, agent, inventory, files

    def _put(self, body):
        return self.cas.put(OPERATOR, "operator", "operator", canonical(body), max_object_bytes=MAX_METADATA)

    def _latest_source(self, state):
        latest = self.db.connection.execute("SELECT id FROM native_jobs WHERE campaign=? AND agent=? "
            "AND role='executor' ORDER BY rowid DESC LIMIT 1", (state.campaign_id, state.agent_id)).fetchone()
        require(latest is not None and latest[0] == state.job_id, "NATIVE_LATER_STATE")

    def seal(self, export_ref, checkpoint_id, *, boundary):
        require(boundary in {"episode", "recovery"}, "NATIVE_RETENTION_BOUNDARY")
        state = self.exports.load(export_ref)
        self._latest_source(state)
        registered, policy, config, agent, inventory, files = self._derive(state, boundary)
        for path, ref in files.items():
            row = self.db.connection.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?", (ref,)).fetchone()
            if row:
                require(row[0] == "operator", "NATIVE_EXPORT_PRIVATE")
                self.cas.verify(OPERATOR, "operator", ref)
            else:
                raw = self.cas.read(Principal(inventory["namespace"], "executor"), inventory["namespace"], ref, max_bytes=MAX_TEXT)
                require(self.cas.put(OPERATOR, "operator", "operator", raw, media_type="text/plain") == ref,
                        "CORRUPT_EVIDENCE")
        def part(skill):
            return self._put({"schema": "strata/NativeRetainedArtifacts/1", "kind": "skill_drafts" if skill else "workspace",
                "files": {k: v for k, v in files.items() if k.startswith("skills/") == skill},
                "activates_skills": False})
        launch = json.loads(self.db.connection.execute("SELECT plan FROM native_jobs WHERE id=?", (state.job_id,)).fetchone()[0])
        require(launch["model"] == agent.requested_model, "NATIVE_RETENTION_SCOPE")
        checkpoint = NativeCheckpointState.model_validate({"schema": "strata/NativeCheckpointState/1",
            "is_example": self.runtime.simulation, "policy": POLICY, "checkpoint_id": checkpoint_id,
            "campaign_id": state.campaign_id, "agent_id": state.agent_id, "source_epoch": state.source_epoch,
            "system_digest": config.system_digest, "profile_digest": state.profile_digest, "model_identity": launch["model"],
            "source_export": export_ref, "retention_policy": registered["ref"], "boundary": boundary,
            "workspace": part(False), "skills": part(True), "resume_mode": "fresh_handoff", "session": None,
            "runtime_cache": None, "cost_rollback": False, "dispatch_authorized": False})
        ref = self._put(checkpoint.model_dump())
        with self.db.transaction() as db:
            self._latest_source(state)
            self._validate(ref)
            old = db.execute("SELECT ref FROM native_checkpoint_states WHERE checkpoint=? AND agent=?",
                             (checkpoint_id, state.agent_id)).fetchone()
            if old:
                require(old[0] == ref, "IDEMPOTENCY_CONFLICT")
                return checkpoint, ref
            db.execute("INSERT INTO native_checkpoint_states VALUES(?,?,?)", (checkpoint_id, state.agent_id, ref))
            self.db.event(db, "native.checkpoint_component", {"checkpoint": checkpoint_id, "agent": state.agent_id,
                "ref": ref, "policy_ref": registered["ref"], "dispatch_authorized": False})
        return checkpoint, ref

    def _validate(self, ref):
        body = private_json(self.db.connection, self.cas, ref)
        require(body.get("schema") == "strata/NativeCheckpointState/1", "NATIVE_CHECKPOINT_REQUIRED")
        state = NativeCheckpointState.model_validate(body)
        export = self.exports.load(state.source_export)
        registered, _, config, agent, _, files = self._derive(export, state.boundary)
        require(state.is_example is self.runtime.simulation and state.campaign_id == export.campaign_id and
            state.agent_id == export.agent_id and state.source_epoch == export.source_epoch and
            state.profile_digest == export.profile_digest and state.system_digest == config.system_digest and
            state.model_identity == agent.requested_model and state.retention_policy == registered["ref"],
            "NATIVE_RETENTION_SCOPE")
        merged = {}
        for skill, part_ref in ((False, state.workspace), (True, state.skills)):
            part = private_json(self.db.connection, self.cas, part_ref)
            expected = {"schema": "strata/NativeRetainedArtifacts/1", "kind": "skill_drafts" if skill else "workspace",
                "files": {k: v for k, v in files.items() if k.startswith("skills/") == skill}, "activates_skills": False}
            require(part == expected, "NATIVE_RETENTION_CHANGED")
            merged |= part["files"]
        check_files(self.cas, merged)
        return state, config

    def load(self, ref):
        with (nullcontext(self.db.connection) if self.db.connection.in_transaction else self.db.transaction()) as db:
            state, config = self._validate(ref)
            row = db.execute("SELECT ref FROM native_checkpoint_states WHERE checkpoint=? AND agent=?",
                             (state.checkpoint_id, state.agent_id)).fetchone()
            require(row is not None and row[0] == ref, "NATIVE_CHECKPOINT_UNCOMMITTED")
            return state, config

    def validate_snapshot(self, manifest, snapshot, namespace):
        require(namespace == "operator", "NATIVE_EXPORT_PRIVATE")
        state, config = self.load(snapshot.runtime_state)
        require(state.checkpoint_id == manifest.checkpoint_id and state.campaign_id == manifest.campaign_id and
            state.agent_id == snapshot.agent_id and state.source_epoch == manifest.source_epoch and
            state.system_digest == manifest.system_digest and config.pack_lock == manifest.pack_lock and
            snapshot.workspace == state.workspace and snapshot.skills == state.skills and
            snapshot.model_identity == state.model_identity, "MIXED_SNAPSHOT")
        export = self.exports.load(state.source_export)
        accounting = private_json(self.db.connection, self.cas, export.accounting_ref)
        require(manifest.ledger_cursor >= accounting["ledger_cursor"], "MIXED_SNAPSHOT")
        if manifest.scheduled_active_s is not None and manifest.scheduled_active_s % config.episode_s == 0:
            require(state.boundary == "episode", "NATIVE_RETENTION_BOUNDARY")
        return state
