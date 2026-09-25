"""One-use private probe-pair staging, with no process or dispatch authority.

The actual launch adapter must recheck staging and qualify live initial state,
resource admission and isolation. Empty directories are not proof of isolation.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Literal

from pydantic import Field

from mcbench.checkpoints import Checkpoints
from mcbench.contracts import Id, Positive, Ref, Strict
from mcbench.native_export import MAX_METADATA, OPERATOR
from mcbench.records import AgentConfig, EvaluationProtocol, PackLock
from mcbench.storage import canonical, digest, extended_path, reject_links, require, safe_relative

from .native_probe_projection import NativeProbeArtifactSelection, project_native_checkpoint

POLICY = "private-matched-probe-pair-staging/1"
ARMS = ("experienced", "initial")


class ProbeFixture(Strict):
    schema_: Literal["strata/ProbeFixture/1"] = Field(alias="schema")
    is_example: bool
    instance_id: Id
    pack_lock: Ref
    world_files: dict[str, Ref] = Field(min_length=1, max_length=200000)
    body_states: dict[Id, Ref]
    keymaps: dict[Id, Ref | None]
    control_cards: dict[Id, Ref]
    public_goal: str = Field(min_length=1, max_length=8000)
    backend_initialization: Ref
    runtime_policy: Ref
    tools: Ref
    observation_action_limits: Ref
    information_policy: Ref


class ProbePairRequest(Strict):
    schema_: Literal["strata/ProbePairRequest/1"] = Field(alias="schema")
    policy: Literal["private-matched-probe-pair-staging/1"]
    is_example: bool
    pair_id: Id
    protocol_ref: Ref
    fixture_ref: Ref
    selections: dict[Id, NativeProbeArtifactSelection] = Field(min_length=1)
    arm_order: list[Literal["experienced", "initial"]] = Field(min_length=2, max_length=2)
    max_materialized_bytes: Positive


class ProbePairs:
    def __init__(self, sets, evaluator_namespace):
        self.sets, self.db, self.cas = sets, sets.db, sets.cas
        require(evaluator_namespace.startswith("evaluation:") and len(evaluator_namespace) <= 256,
                "PROBE_NAMESPACE")
        self.namespace = evaluator_namespace
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS probe_pair_staging (namespace TEXT, id TEXT, "
                "instance TEXT UNIQUE, fixture_ref TEXT UNIQUE, world_digest TEXT UNIQUE, target TEXT UNIQUE, "
                "request TEXT, plan TEXT, state TEXT, PRIMARY KEY(namespace,id))")

    def _private(self, ref):
        row = self.db.connection.execute("SELECT visibility FROM objects WHERE namespace=? AND ref=?",
                                         (self.namespace, ref)).fetchone()
        require(row is not None and row[0] == "evaluator", "PROBE_PRIVATE_SOURCE")
        return json.loads(self.cas.read(OPERATOR, self.namespace, ref, max_bytes=MAX_METADATA))

    def _authorize(self, principal):
        require(principal.role == "operator" or principal.role == "evaluator" and
                principal.namespace == self.namespace, "FORBIDDEN")

    def _index(self, ref, schema, field):
        value = self._private(ref)
        require(isinstance(value, dict) and set(value) == {"schema", field} and value["schema"] == schema
                and isinstance(value[field], dict), "PROBE_INDEX_SCHEMA")
        return value[field]

    def _derive(self, principal, request):
        self._authorize(principal)
        require(request.is_example is self.sets.runtime.simulation and set(request.arm_order) == set(ARMS),
                "PROBE_PAIR_SCOPE")
        protocol = EvaluationProtocol.model_validate(self._private(request.protocol_ref))
        fixture = ProbeFixture.model_validate(self._private(request.fixture_ref))
        require(protocol.is_example is request.is_example and fixture.is_example is request.is_example,
                "PROBE_PAIR_SCOPE")
        # These fixed manifests are private protocol inputs, not caller-assigned
        # labels supplied during a launch. Preserve their exact bytes in the plan.
        instances = self._index(protocol.sealed_instances, "strata/ProbeInstanceIndex/1", "instances")
        require(instances.get(fixture.instance_id) == request.fixture_ref, "PROBE_INSTANCE_SCOPE")
        projections = self._index(protocol.artifact_projection, "strata/ProbeSelectionIndex/1", "selections")
        require(projections.get(request.pair_id) ==
                {a: s.model_dump() for a, s in request.selections.items()}, "PROBE_SELECTION_SCOPE")
        allocation = self._index(protocol.randomization_plan, "strata/ProbeOrderIndex/1", "orders")
        require(allocation.get(request.pair_id) == request.arm_order, "PROBE_ORDER_SCOPE")
        for ref in (protocol.scorer, protocol.sample_plan, protocol.censoring_plan,
                    protocol.analysis_plan, protocol.access_log):
            self._private(ref)
        if protocol.control_keymap:
            self._private(protocol.control_keymap)
        lock = PackLock.model_validate(self._private(fixture.pack_lock))
        require(lock.status == "sealed" and not lock.is_example, "PACK_NOT_SEALED")
        projected = {a: project_native_checkpoint(principal, self.sets, s)
                     for a, s in request.selections.items()}
        first = next(iter(projected.values()))
        state, config = self.sets.components.load(first.checkpoint_ref)
        roster = set(config.agent_ids)
        require(set(projected) == roster and len(roster) == config.n and
                all(set(group) == roster for group in (fixture.body_states, fixture.keymaps, fixture.control_cards)),
                "PROBE_COMPLETE_ROSTER")
        require(config.system_digest in protocol.system_digests and config.pack_lock == fixture.pack_lock and
                first.scheduled_active_s in protocol.exposure_s, "PROBE_PROTOCOL_SCOPE")
        require(config.information_policy == fixture.information_policy and config.runtime_profile == fixture.runtime_policy,
                "PROBE_SYSTEM_POLICY")
        for ref in (config.communication_policy, config.backend.capability_manifest):
            self.cas.verify(OPERATOR, "operator", ref)
        require(all(p.agent_id == a and p.campaign_id == first.campaign_id and
                p.checkpoint_manifest_digest == first.checkpoint_manifest_digest and
                p.checkpoint_id == first.checkpoint_id and p.system_digest == config.system_digest and
                p.scheduled_active_s == first.scheduled_active_s and p.actual_active_s == first.actual_active_s
                for a, p in projected.items()), "PROBE_MIXED_SOURCE")
        for files in (fixture.world_files,):
            require(len({p.casefold() for p in files}) == len(files), "AMBIGUOUS_PATHS")
            folded = {p.casefold() for p in files}
            for path, ref in files.items():
                parts = safe_relative(path)
                require(parts.parts[0] in {"world", "external"} and len(parts.parts) > 1 and
                        not any(str(p).casefold() in folded for p in parts.parents if str(p) != "."),
                        "PROBE_WORLD_PATH")
                require(not {p.casefold() for p in parts.parts} & {
                    ".git", ".codex", ".ssh", "auth.json", "credentials.json", "launcher_accounts.json",
                    "launcher_msa_credentials.bin", "auth-cache", "auth_cache"}, "SECRET_IN_SNAPSHOT")
                row = self.db.connection.execute("SELECT visibility FROM objects WHERE namespace=? AND ref=?",
                                                 (self.namespace, ref)).fetchone()
                require(row is not None and row[0] == "evaluator", "PROBE_PRIVATE_SOURCE")
                self.cas.verify(OPERATOR, self.namespace, ref)
        require("world/level.dat" in fixture.world_files, "PROBE_WORLD_INCOMPLETE")
        for ref in (*fixture.body_states.values(), *fixture.control_cards.values(),
                    *(r for r in fixture.keymaps.values() if r), fixture.backend_initialization,
                    fixture.runtime_policy, fixture.tools, fixture.observation_action_limits, fixture.information_policy):
            self._private(ref)
        require(all(r == protocol.control_keymap for r in fixture.keymaps.values()), "PROBE_KEYMAP_SCOPE")
        members = {}
        for index, agent in enumerate(sorted(roster)):
            registered = self.db.connection.execute("SELECT agent_config FROM native_retention_policies "
                "WHERE campaign=? AND agent=?", (first.campaign_id, agent)).fetchone()
            a = AgentConfig.model_validate_json(registered[0])
            require(a.requested_model == projected[agent].model_identity, "PROBE_MODEL_SCOPE")
            self.cas.verify(OPERATOR, "operator", a.inference_config)
            self.cas.verify(OPERATOR, "operator", a.capability_profile)
            members[agent] = {"directory": "body-" + str(index), "requested_model": a.requested_model,
                "immutable_model_id": a.immutable_model_id, "identity_assurance": a.identity_assurance,
                "provider": a.provider, "inference_config": a.inference_config,
                "runtime": a.runtime.model_dump(), "dovetail_commit": a.dovetail_commit,
                "dovetail_version": a.dovetail_version, "initial_skills": a.initial_skills,
                "capability_profile": a.capability_profile, "helper_limit": a.helper_limit,
                "helper_depth": a.helper_depth, "self_play": a.self_play,
                "helper_practice_namespace": "development", "body_state": fixture.body_states[agent],
                "keymap": fixture.keymaps[agent], "control_card": fixture.control_cards[agent]}
        common = {"system_digest": config.system_digest, "pack_lock": fixture.pack_lock,
            "n": config.n, "members": members, "public_goal": fixture.public_goal,
            "track": config.track, "backend": config.backend.model_dump(), "topology": config.topology,
            "communication_policy": config.communication_policy, "budget_policy": config.budget_policy,
            "probe_limits": protocol.probe_limits.model_dump(), "handoff_bytes_limit": 8000,
            "backend_initialization": fixture.backend_initialization,
            "runtime_policy": fixture.runtime_policy, "tools": fixture.tools,
            "observation_action_limits": fixture.observation_action_limits,
            "information_policy": fixture.information_policy, "session": None, "runtime_cache": None}
        same = all(p.initial_files == p.experienced_files and not p.experienced_skills for p in projected.values())
        require(first.scheduled_active_s != 0 or first.actual_active_s == 0 and same, "T0_NOT_MATCHED")
        plan = {"schema": "strata/ProbePairStaging/1", "policy": POLICY, "is_example": request.is_example,
            "pair_id": request.pair_id, "instance_id": fixture.instance_id, "fixture_ref": request.fixture_ref,
            "world_digest": digest({"pack_lock": fixture.pack_lock, "files": fixture.world_files}),
            "protocol_ref": request.protocol_ref, "request_digest": digest(request.model_dump()),
            "arm_order": request.arm_order,
            "arm_directories": {arm: "copy-" + str(i) for i, arm in enumerate(request.arm_order)},
            "common": common, "world_files": fixture.world_files,
            "projections": {a: p.model_dump() for a, p in projected.items()},
            "at_t0": first.scheduled_active_s == first.actual_active_s == 0,
            "dispatch_authorized": False, "campaign_feedback_allowed": False,
            "live_initial_state_verified": False, "resource_admission_verified": False}
        return plan

    def _inventory(self, plan):
        """Only admitted cognitive files go beneath a gameplay workspace."""
        files, generated, directories = {}, {}, set()
        for arm in ARMS:
            directory = plan["arm_directories"][arm]
            generated[directory + "/private/common.json"] = canonical(plan["common"])
            files.update({directory + "/server/" + p: (self.namespace, r) for p, r in plan["world_files"].items()})
            for agent, member in plan["common"]["members"].items():
                root = directory + "/agents/" + member["directory"]
                directories.update({root + "/profile", root + "/backend-cache", root + "/workspace"})
                p = plan["projections"][agent]
                admitted = p["initial_files"] if arm == "initial" else p["experienced_files"]
                files.update({root + "/workspace/" + path: ("operator", ref) for path, ref in admitted.items()})
                skills = {} if arm == "initial" else p["experienced_skills"]
                for name, skill in skills.items():
                    files.update({root + "/workspace/active/" + name + "/" + path: ("operator", ref)
                                  for path, ref in skill["files"].items()})
                generated[root + "/workspace/active/revisions.json"] = canonical({
                    "schema": "strata/ActiveSkillIndex/1",
                    "skills": {name: value["revision_id"] for name, value in skills.items()}})
                for field in ("body_state", "keymap", "control_card"):
                    if ref := member[field]:
                        files[directory + "/private/" + member["directory"] + "/" + field + ".json"] = (self.namespace, ref)
        generated["pair.json"] = canonical(plan)
        for path in files.keys() | generated.keys() | directories:
            directories.update(str(p) for p in safe_relative(path).parents if str(p) != ".")
        return files, generated, directories

    def _check(self, target, plan):
        files, generated, directories = self._inventory(plan)
        # Reuse the complete-set checker for regular-file/link/size/hash/inventory
        # verification. Generated private metadata has its own evaluator CAS refs.
        mapped = files | {p: (self.namespace, "cas:sha256:" + digest(json.loads(raw))) for p, raw in generated.items()}
        checker = object.__new__(Checkpoints)
        checker.database, checker.cas = self.db, self.cas
        checker._verify_staged_tree(target, mapped, directories)

    def prepare(self, principal, request, target):
        self._authorize(principal)
        request = ProbePairRequest.model_validate(request)
        plan = self._derive(principal, request)
        target = extended_path(Path(target))
        reject_links(target)
        require(not target.exists() and not target.is_relative_to(extended_path(self.cas.root)), "TARGET_EXISTS")
        files, generated, directories = self._inventory(plan)
        total = sum(self.db.connection.execute("SELECT bytes FROM objects WHERE namespace=? AND ref=?", value).fetchone()[0]
                    for value in files.values()) + sum(len(raw) for raw in generated.values())
        require(total <= request.max_materialized_bytes, "PROBE_STORAGE_LIMIT")
        target.parent.mkdir(parents=True, exist_ok=True)
        require(shutil.disk_usage(target.parent).free >= total, "PROBE_STORAGE_LIMIT")
        with self.db.transaction() as db:
            require(db.execute("SELECT 1 FROM probe_pair_staging WHERE (namespace=? AND id=?) OR instance=? "
                "OR fixture_ref=? OR target=? OR world_digest=?", (self.namespace, request.pair_id, plan["instance_id"],
                                                request.fixture_ref, str(target), plan["world_digest"])).fetchone() is None,
                "PROBE_INSTANCE_CONSUMED")
            db.execute("INSERT INTO probe_pair_staging VALUES(?,?,?,?,?,?,?,?,'PREPARING')",
                (self.namespace, request.pair_id, plan["instance_id"], request.fixture_ref, plan["world_digest"], str(target),
                 request.model_dump_json(), canonical(plan).decode()))
            self.db.event(db, "probe.pair_preparing", {"namespace": self.namespace, "pair": request.pair_id,
                "instance": plan["instance_id"], "request_digest": plan["request_digest"]})
        try:
            target.mkdir()
            for path in sorted(directories):
                target.joinpath(*safe_relative(path).parts).mkdir(parents=True, exist_ok=True)
            for path, (namespace, ref) in files.items():
                self.cas.copy_to(OPERATOR, namespace, ref, target.joinpath(*safe_relative(path).parts))
            for path, raw in generated.items():
                self.cas.put(OPERATOR, self.namespace, "evaluator", raw, max_object_bytes=MAX_METADATA)
                with target.joinpath(*safe_relative(path).parts).open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
            with self.db.transaction() as db:
                require(self._derive(principal, request) == plan, "PROBE_SOURCE_CHANGED")
                self._check(target, plan)
                db.execute("UPDATE probe_pair_staging SET state='PREPARED' WHERE namespace=? AND id=?",
                           (self.namespace, request.pair_id))
                self.db.event(db, "probe.pair_prepared", {"namespace": self.namespace, "pair": request.pair_id,
                    "plan_digest": digest(plan), "materialized_bytes": total, "dispatch_authorized": False})
        except BaseException:
            with self.db.transaction() as db:
                db.execute("UPDATE probe_pair_staging SET state='FAILED' WHERE namespace=? AND id=?",
                           (self.namespace, request.pair_id))
                self.db.event(db, "probe.pair_failed", {"namespace": self.namespace, "pair": request.pair_id})
            raise
        return plan

    def verify(self, principal, pair_id):
        """Reconstruct and inspect both complete trees, without launching either."""
        self._authorize(principal)
        with self.db.transaction() as db:
            row = db.execute("SELECT * FROM probe_pair_staging WHERE namespace=? AND id=?",
                             (self.namespace, pair_id)).fetchone()
            require(row is not None and row["state"] == "PREPARED", "PROBE_PAIR_NOT_PREPARED")
            request = ProbePairRequest.model_validate_json(row["request"])
            plan = self._derive(principal, request)
            require(canonical(plan).decode() == row["plan"], "PROBE_SOURCE_CHANGED")
            target = extended_path(Path(row["target"]))
            self._check(target, plan)
            self.db.event(db, "probe.pair_verified", {"namespace": self.namespace, "pair": pair_id,
                "plan_digest": digest(plan), "dispatch_authorized": False})
        return plan
