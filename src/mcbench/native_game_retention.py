"""Private preregistration for the scripted-provider native/game capture.

This creates a DRAFT controller and a native retention component. It does not
seal a pack, admit a campaign, change an allowance or authorize a restoration.
The input must be externally hash-pinned before any game process starts.
"""

import hashlib
import json
from pathlib import Path

from mcbench.controller import Controller
from mcbench.native_checkpoint import InitialArtifacts, NativeCheckpointStates, NativeRetentionPolicy
from mcbench.native_export import OPERATOR
from mcbench.records import AgentConfig, CampaignConfig, PackLock
from mcbench.storage import digest, reject_links, require

INITIAL = {"supplied/plan.md": "STRATA_SCOPED_PLAN",
           "initial/skill.md": "STRATA_IMMUTABLE_SKILL",
           "docs/root-only.md": "STRATA_ROOT_ONLY_CANARY"}
MAX_INPUT = 1024 * 1024


def paired_components(output, result, input_sha256, server_plan):
    """Join normal/extended Windows paths without weakening stop requirements."""
    from mcbench.launch_integrity import safe
    from mcbench.vanilla_persistence import verify_snapshot
    snapshot = result["server_result"]["stopped_snapshot"]
    target = safe(output / "server/stopped-instance")
    require(result["status"] == "pass" and safe(Path(snapshot["path"])) == target,
            "M0_CAPTURE_INCOMPLETE")
    captured = verify_snapshot(target, snapshot["manifest_sha256"])
    require(captured["server_plan_digest"] == digest(server_plan) and "native_retention" in result,
            "M0_CAPTURE_INCOMPLETE")
    return {"schema": "strata/NativeGameStoppedComponents/1",
        "native_component": result["native_retention"]["component_ref"],
        "snapshot_sha256": snapshot["manifest_sha256"], "retention_input_sha256": input_sha256,
        "complete_checkpoint": False, "dispatch_authorized": False, "G0": "fail"}


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "RETENTION_INPUT_INVALID")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: require(False, "RETENTION_INPUT_INVALID"))


class GameRetention:
    def __init__(self, source):
        require(isinstance(source, dict) and set(source) == {"path", "sha256"}, "RETENTION_INPUT_INVALID")
        path = Path(source["path"])
        require(path.is_absolute(), "RETENTION_INPUT_INVALID")
        reject_links(path)
        require(path.is_file() and path.stat().st_nlink == 1 and path.stat().st_size <= MAX_INPUT,
                "RETENTION_INPUT_INVALID")
        with path.open("rb") as stream:
            raw = stream.read(MAX_INPUT + 1)
        require(len(raw) <= MAX_INPUT and hashlib.sha256(raw).hexdigest() == source["sha256"],
                "RETENTION_INPUT_CHANGED")
        body = strict_json(raw)
        require(isinstance(body, dict) and set(body) == {"schema", "qualification", "campaign", "agent", "objects"}
                and body["schema"] == "strata/NativeGameRetentionInput/1"
                and body["qualification"] == "component_only", "RETENTION_INPUT_INVALID")
        self.config = CampaignConfig.model_validate(body["campaign"])
        self.agent = AgentConfig.model_validate(body["agent"])
        c, a = self.config, self.agent
        require(not c.is_example and not a.is_example and c.n == 1 and c.agent_ids == [a.agent_id]
                and c.track == "structured-actions/v1" and c.backend.kind == "mineflayer"
                and c.recovery_policy == "resume_development" and c.system_digest == a.system_digest
                and a.resume_mode == "fresh_handoff" and a.learned_overlay is None,
                "RETENTION_INPUT_SCOPE")
        objects = body["objects"]
        require(isinstance(objects, dict) and 1 <= len(objects) <= 64, "RETENTION_INPUT_INVALID")
        for ref, text in objects.items():
            require(isinstance(text, str) and ref == "cas:sha256:" + hashlib.sha256(text.encode()).hexdigest(),
                    "RETENTION_INPUT_CHANGED")
        require(a.memory_policy in objects and a.initial_skills in objects, "RETENTION_INPUT_INCOMPLETE")
        policy = NativeRetentionPolicy.model_validate(strict_json(objects[a.memory_policy]))
        initial = InitialArtifacts.model_validate(strict_json(objects[a.initial_skills]))
        require(policy.is_example is True and policy.campaign_id == c.campaign_id and
                policy.agent_id == a.agent_id and policy.system_digest == c.system_digest and
                policy.initial_artifacts == a.initial_skills and policy.arm == "full",
                "RETENTION_INPUT_SCOPE")
        expected = {name: "cas:sha256:" + hashlib.sha256(text.encode()).hexdigest()
                    for name, text in INITIAL.items()}
        require(initial.files == expected and all(objects.get(ref) == INITIAL[name]
                for name, ref in expected.items()), "RETENTION_INPUT_BASELINE")
        context = {c.pack_lock, c.protocol_ref, c.world_baseline, c.information_policy,
                   c.communication_policy, c.runtime_profile, c.backend.capability_manifest,
                   a.inference_config, a.capability_profile}
        require(context <= set(objects), "RETENTION_INPUT_INCOMPLETE")
        for ref in context:
            require(isinstance(strict_json(objects[ref]), dict), "RETENTION_INPUT_INVALID")
        lock = PackLock.model_validate(strict_json(objects[c.pack_lock]))
        require(not lock.is_example and lock.pack_slug == "vanilla" and lock.minecraft == "1.19.2",
                "RETENTION_INPUT_PROFILE")
        require(set(objects) == {a.memory_policy, a.initial_skills, *expected.values(), *context},
                "RETENTION_INPUT_EXTRA_OBJECTS")
        self.body, self.raw, self.source = body, raw, dict(source)

    def check_scope(self, scope):
        require(scope["campaign_id"] == self.config.campaign_id and scope["agent_id"] == self.agent.agent_id,
                "RETENTION_INPUT_SCOPE")

    def check_identity(self, *, model, dovetail_commit, binary_digest, binary_version, helper_limit):
        require(model == self.agent.requested_model and dovetail_commit == self.agent.dovetail_commit
                and binary_digest == self.agent.runtime.digest and binary_version == self.agent.runtime.version
                and helper_limit == self.agent.helper_limit and self.agent.helper_depth == 2,
                "RETENTION_INPUT_PROFILE")

    def register(self, runtime, plan):
        require(runtime.simulation is True and plan.role == "executor" and plan.purpose == "conformance",
                "RETENTION_INPUT_PROFILE")
        self.check_scope(plan.model_dump())
        self.check_identity(**{key: getattr(plan, key) for key in
            ("model", "dovetail_commit", "binary_digest", "binary_version", "helper_limit")})
        # Check lateness before importing or constructing a new controller.
        require(runtime.db.connection.execute("SELECT 1 FROM native_jobs WHERE campaign=? AND agent=?",
                (plan.campaign_id, plan.agent_id)).fetchone() is None, "NATIVE_RETENTION_TOO_LATE")
        for ref, text in self.body["objects"].items():
            require(runtime.cas.put(OPERATOR, "operator", "operator", text.encode()) == ref,
                    "RETENTION_INPUT_CHANGED")
        self.input_ref = runtime.cas.put(OPERATOR, "operator", "operator", self.raw)
        Controller(runtime.db, simulation=True).create(self.config, [self.agent])
        self.service = NativeCheckpointStates(runtime)
        self.service.register(self.config, self.agent)
        self.runtime, self.plan = runtime, plan

    def finish(self):
        runtime, plan = self.runtime, self.plan
        before = runtime.budgets.status(plan.account)
        export_ref = runtime.export_broker_state(plan.job_id)
        state, ref = self.service.seal(export_ref, plan.job_id + "-stopped", boundary="recovery")
        require(self.service.load(ref)[0] == state and runtime.budgets.status(plan.account) == before,
                "RETENTION_COMPONENT_CHANGED")
        return {"schema": "strata/NativeGameRetentionResult/1", "input_ref": self.input_ref,
                "input_sha256": self.source["sha256"], "campaign_digest": digest(self.config.model_dump()),
                "component_ref": ref, "source_export": export_ref, "component": state.model_dump(),
                "model_evidence": "synthetic_provider", "controller_state": "DRAFT",
                "cost_rollback": False, "complete_checkpoint": False, "dispatch_authorized": False,
                "pack_qualified": False, "G0": "fail"}
