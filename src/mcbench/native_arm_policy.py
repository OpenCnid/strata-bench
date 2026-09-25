"""Live native capability enforcement for preregistered retention arms.

Read-only. Historical exports stay readable; registration is not retroactively
altered. A contradictory existing no-self-play job cannot dispatch or use tools.
"""

import json

from .native_broker_policy import NO_HELPER_POLICIES, validate_broker_settings
from .storage import canonical, require


def require_arm_policy(db, cas, plan):
    declared = []
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='campaigns'").fetchone():
        campaign = db.execute("SELECT agents FROM campaigns WHERE id=?", (plan.campaign_id,)).fetchone()
        if campaign is not None:
            declared = [a for a in json.loads(campaign[0]) if a.get("agent_id") == plan.agent_id]
    disabled = any(a.get("self_play") is False for a in declared)
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='native_retention_policies'").fetchone():
        require(not disabled, "NATIVE_RETENTION_NOT_REGISTERED")
        return None
    row = db.execute("SELECT * FROM native_retention_policies WHERE campaign=? AND agent=?",
                     (plan.campaign_id, plan.agent_id)).fetchone()
    if row is None:
        require(not disabled, "NATIVE_RETENTION_NOT_REGISTERED")
        return None
    from .native_checkpoint import NativeRetentionPolicy
    from .native_export import private_json
    from .records import AgentConfig, CampaignConfig
    policy = NativeRetentionPolicy.model_validate(private_json(db, cas, row["ref"]))
    config = CampaignConfig.model_validate_json(row["config"])
    agent = AgentConfig.model_validate_json(row["agent_config"])
    require(policy.campaign_id == config.campaign_id == plan.campaign_id and
            policy.agent_id == agent.agent_id == plan.agent_id and
            policy.system_digest == config.system_digest == agent.system_digest and
            row["ref"] == agent.memory_policy, "NATIVE_ARM_SCOPE")
    require(not disabled or policy.arm == "no-self-play", "NATIVE_ARM_SCOPE")
    if policy.arm == "no-self-play":
        require(canonical(declared) == canonical([agent.model_dump()]), "NATIVE_ARM_SCOPE")
        require(agent.self_play is False and agent.helper_limit == 0 and
                plan.helper_limit == 0 and plan.role == "executor" and plan.depth == 0 and
                plan.parent_job_id is None and plan.helper_skill_activation_ref is None and
                plan.broker_policy in NO_HELPER_POLICIES, "NATIVE_NO_SELF_PLAY")
        validate_broker_settings(plan.config_overrides, policy=plan.broker_policy)
    return policy.arm
