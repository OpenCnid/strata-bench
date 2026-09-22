"""Source-bound root restoration for the explicit scripted M0 recovery profile.

Production admission still requires a complete committed checkpoint. This
conformance path cannot authorize a real provider or certify game restoration.
"""

from .native_checkpoint import NativeCheckpointStates, check_files
from .native_export import OPERATOR, private_json
from .storage import Principal, require
from urllib.parse import urlsplit


class NativeRecovery:
    def __init__(self, runtime):
        self.runtime, self.db, self.cas = runtime, runtime.db, runtime.cas
        self.components = NativeCheckpointStates(runtime)
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_recovery_projections ("
                "runtime TEXT, thread TEXT, component TEXT, PRIMARY KEY(runtime,thread))")

    def validate_launch(self, plan):
        require(self.runtime.simulation and plan.purpose == "conformance" and plan.role == "executor"
                and plan.parent_job_id is None and plan.broker_policy is not None
                and plan.provider == "strata_local_fixture"
                and plan.budget_mode == "per_dispatch" and plan.skill_activation_ref is None
                and plan.helper_skill_activation_ref is None and plan.resume_component_ref is not None,
                "NATIVE_RECOVERY_PROFILE")
        endpoint = urlsplit(plan.config_overrides.get("model_providers.strata_local_fixture.base_url", ""))
        require(endpoint.scheme == "http" and endpoint.hostname == "127.0.0.1" and endpoint.port
                and endpoint.path == "/v1" and not endpoint.query and not endpoint.fragment
                and endpoint.username is None and endpoint.password is None, "NATIVE_RECOVERY_PROFILE")
        state, config = self.components.load(plan.resume_component_ref)
        export = self.components.exports.load(state.source_export)
        from .native import NativeLaunch
        source = NativeLaunch.model_validate_json(self.db.connection.execute(
            "SELECT plan FROM native_jobs WHERE id=?", (export.job_id,)).fetchone()[0])
        require(plan.campaign_id == state.campaign_id and plan.agent_id == state.agent_id
                and plan.epoch > state.source_epoch and plan.job_id != export.job_id
                and plan.account == source.account and config.recovery_policy == "resume_development"
                and state.boundary == "recovery" and all(getattr(plan, key) == getattr(source, key)
                    for key in ("model", "binary_digest", "binary_version", "dovetail_commit", "helper_limit")),
                "NATIVE_RECOVERY_SCOPE")
        prior = self.db.connection.execute("SELECT id FROM native_jobs WHERE campaign=? AND agent=? "
            "AND role='executor' AND id!=? ORDER BY rowid DESC LIMIT 1",
            (plan.campaign_id, plan.agent_id, plan.job_id)).fetchone()
        require(prior is not None and prior[0] == export.job_id, "NATIVE_LATER_STATE")
        skills = private_json(self.db.connection, self.cas, state.skills)
        require(skills == {"schema": "strata/NativeRetainedArtifacts/1", "kind": "skill_drafts",
                           "files": {}, "activates_skills": False}, "NATIVE_RECOVERY_PROFILE")
        files = private_json(self.db.connection, self.cas, state.workspace)["files"]
        check_files(self.cas, files)
        require(not any(p.startswith(("skills/", "active/")) for p in files), "NATIVE_RECOVERY_PROFILE")
        return state, files

    def project(self, plan, grant, broker):
        _, files = self.validate_launch(plan)
        require(grant.runtime_id == plan.job_id and grant.profile_digest == plan.profile_digest()
                and grant.campaign_id == plan.campaign_id and grant.agent_id == plan.agent_id
                and grant.epoch == plan.epoch, "NATIVE_RECOVERY_SCOPE")
        if grant.role != "executor":
            return  # Clean-context helpers never inherit root notes or private exports.
        old = self.db.connection.execute("SELECT component FROM native_recovery_projections "
            "WHERE runtime=? AND thread=?", (plan.job_id, grant.thread_id)).fetchone()
        if old:
            require(old[0] == plan.resume_component_ref, "NATIVE_RECOVERY_SCOPE")
            return
        for path, ref in files.items():
            broker._path(path)
            raw = self.cas.read(OPERATOR, "operator", ref)
            require(self.cas.put(Principal(grant.namespace, "executor"), grant.namespace, "agent", raw,
                                media_type="text/plain") == ref, "CORRUPT_EVIDENCE")
        with self.db.transaction() as db:
            require(broker._grant(db, grant.thread_id)[0] == grant, "NATIVE_RECOVERY_SCOPE")
            require(not db.execute("SELECT 1 FROM native_recovery_projections WHERE runtime=? AND thread=?",
                (plan.job_id, grant.thread_id)).fetchone(), "NATIVE_RECOVERY_SCOPE")
            require(not db.execute("SELECT 1 FROM broker_files WHERE namespace=?", (grant.namespace,)).fetchone(),
                    "NATIVE_RECOVERY_NOT_FRESH")
            for path, ref in files.items():
                immutable = path.split("/")[0] in {"initial", "docs", "supplied"}
                db.execute("INSERT INTO broker_files VALUES(?,?,?,?)", (grant.namespace, path, ref, int(immutable)))
            db.execute("INSERT INTO native_recovery_projections VALUES(?,?,?)",
                       (plan.job_id, grant.thread_id, plan.resume_component_ref))
            self.db.event(db, "native.recovery_projected", {"job": plan.job_id, "thread": grant.thread_id,
                "component": plan.resume_component_ref, "source_epoch": self.validate_launch(plan)[0].source_epoch,
                "epoch": plan.epoch, "full_checkpoint": False})
