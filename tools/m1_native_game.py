"""Owned M1 campaign-boundary integration; scripted provider, no paid permit.

Uses the held pack/worker and normal-stop lifecycle shared with M0. This plan
has its own schema and typed scope; it never imports M0 agent retention.
"""

import argparse
from contextlib import ExitStack
from dataclasses import dataclass
import json
from pathlib import Path

from mcbench.inventory import file_hash
from mcbench.native import NativeExec
from mcbench.native_export import NativeExports
from mcbench.pack_launch import RestoredPackLaunchBinding, parse_pack_binding
from mcbench.pack_restore import baseline_record
from mcbench.pack_worker import WorkerInvocation
from mcbench.records import AgentConfig, CampaignConfig
from mcbench.runtime import CODEX_VERSION, DOVETAIL_COMMIT, native_companion_paths
from mcbench.storage import CAS, Database, digest, require
from native_dispatch_probe import BINARY_SHA256
from native_campaign_boundary_probe import CampaignBoundaryProbe
from native_team_channel_probe import TeamChannelStore

SCHEMA = "strata/M1NativeBoundary/1"
FIELDS = {"schema", "output", "pack", "worker_invocation", "worker_runtime", "codex",
          "tool_projections", "model_catalog", "campaign", "agents"}


@dataclass(frozen=True)
class Candidate:
    plan_digest: str
    campaign: CampaignConfig
    agents: tuple[AgentConfig, ...]

    def require_plan(self, plan):
        require(digest(plan) == self.plan_digest and plan["schema"] == SCHEMA, "M1_PLAN_CHANGED")

    def native(self, plan, descriptor, config, output):
        from m0_native_game import write
        from native_mcp_identity_probe import run
        self.require_plan(plan)
        with TeamChannelStore(output.parent / "controller", self.campaign, self.agents) as store:
            with CampaignBoundaryProbe(store, "sender", descriptor, config["lease_id"], output) as probe:
                result = run(Path(plan["codex"]), output, broker_mode=True, admission_mode=True,
                    bootstrap_mode=True, ingress_mode=True, oauth_mode=True, model="gpt-6-luna",
                    tool_projections=json.loads(Path(plan["tool_projections"]).read_bytes()),
                    no_patch_catalog=Path(plan["model_catalog"]), job_id=probe.job_id,
                    campaign_boundary_probe=probe)
            # A stopped export is independent evidence even when a scenario
            # check failed. A missing/uncertain export never becomes a pass.
            db = Database(store.database)
            try:
                cas = CAS(db, store.objects)
                exports = NativeExports(NativeExec(db, cas, simulation=True))
                ref = exports.export(probe.job_id)
                state = exports.load(ref)
                write(output / "export.json", {"ref": ref, "state": state.model_dump()})
                result["candidate_export"] = {"ref": ref, "state": state.model_dump()}
            finally:
                db.close()
            return result


def validate(plan):
    from m0_native_game import private
    require(isinstance(plan, dict) and set(plan) == FIELDS and plan["schema"] == SCHEMA,
            "M1_PLAN_INVALID")
    campaign = CampaignConfig.model_validate(plan["campaign"])
    require(isinstance(plan["agents"], list), "M1_PLAN_ROSTER")
    agents = tuple(AgentConfig.model_validate(a) for a in plan["agents"])
    # These are actual controller execution records, even though its readiness
    # evidence and provider are synthetic. Example documents cannot execute.
    require(not campaign.is_example and campaign.n == 2 and campaign.agent_ids == ["a1", "a2"]
            and [a.agent_id for a in agents] == campaign.agent_ids and all(not a.is_example for a in agents),
            "M1_PLAN_ROSTER")
    require(campaign.track == "structured-actions/v1" and all(a.provider == "local_scripted"
                and a.requested_model == "gpt-6-luna" and a.runtime.version == CODEX_VERSION
                and a.runtime.digest == BINARY_SHA256 and a.dovetail_commit == DOVETAIL_COMMIT
                and a.helper_limit == 1 and a.helper_depth == 1 for a in agents), "M1_PLAN_RUNTIME")
    binding = parse_pack_binding(plan["pack"])
    require(isinstance(binding, RestoredPackLaunchBinding) and campaign.pack_lock == binding.lock
            and campaign.world_baseline == "cas:sha256:" + digest(baseline_record(binding)),
            "M1_PLAN_BASELINE")
    invocation = WorkerInvocation.model_validate(plan["worker_invocation"])
    output = private(plan["output"])
    require(not output.exists() and invocation.campaign_id == campaign.campaign_id
            and invocation.agent_id == "a1" and invocation.epoch == 1
            and private(invocation.state_directory) == output / "worker"
            and private(invocation.configuration_path) == output / "worker-config.json", "M1_PLAN_SCOPE")
    for path in (binding.store, binding.instance, binding.restoration.snapshot, plan["codex"],
                 plan["tool_projections"], plan["model_catalog"]):
        private(path)
    require(file_hash(Path(plan["codex"])) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    native_companion_paths(plan["codex"])
    return Candidate(digest(plan), campaign, agents)


def run(path):
    from m0_native_game import private, run_plan
    path = private(path)
    require(path.stat().st_size <= 8 * 1024**2, "M1_PLAN_SIZE")
    plan = json.loads(path.read_bytes())
    candidate = validate(plan)
    with ExitStack() as resources:
        return run_plan(plan, resources, candidate=candidate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    # Keep the Candidate type identity stable when invoked as a script.
    from m1_native_game import run as entry
    result = entry(parser.parse_args().plan)
    print(json.dumps({k: result[k] for k in ("status", "schema", "game_evidence", "model_evidence", "elapsed_s")}))
    raise SystemExit(0 if result["status"] == "pass" else 1)
