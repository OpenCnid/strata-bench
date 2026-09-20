"""Durable operator lifecycle, whole-team reservations, epochs and scoped grants.

This service manages state; an authenticated supervisor supplies actual readiness,
cleanup and capacity evidence. It does not launch games or assert OS isolation.
"""

import hashlib
import json
import secrets
import time

from .records import AgentConfig, CampaignConfig, PackLock
from .storage import CAS, Database, Fault, Principal, canonical, digest, require

TRANSITIONS = {
    "DRAFT": {"PROVISIONING"},
    "PROVISIONING": {"AWAITING_ARTIFACT", "AWAITING_AUTH", "VALIDATING"},
    "AWAITING_ARTIFACT": {"PROVISIONING"}, "AWAITING_AUTH": {"PROVISIONING"},
    "VALIDATING": {"QUEUED", "STARTING"}, "QUEUED": {"STARTING"},
    "STARTING": {"RUNNING"}, "RUNNING": {"CHECKPOINTING", "RECOVERING", "STOPPING"},
    "CHECKPOINTING": {"RUNNING", "RECOVERING"}, "RECOVERING": {"RUNNING"},
    "STOPPING": {"COMPLETE"}, "COMPLETE": set(), "ABORTED": set(),
}
RESOURCES = {"bodies", "memory_mib", "disk_bytes", "model_slots"}
READINESS = {"backend", "fresh_observation", "runtime_grant", "metering", "telemetry"}


class Controller:
    def __init__(self, database: Database, *, simulation=False, clock=time.time,
                 cas: CAS | None = None, evidence_namespace="operator"):
        self.database, self.simulation, self.clock = database, simulation, clock
        self.cas, self.evidence_namespace = cas, evidence_namespace
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS controller_profile (simulation INTEGER)")
            profile = db.execute("SELECT simulation FROM controller_profile").fetchone()
            if profile is None:
                db.execute("INSERT INTO controller_profile VALUES (?)", (int(simulation),))
            else:
                require(bool(profile[0]) == simulation, "PROFILE_MISMATCH")
            db.execute("CREATE TABLE IF NOT EXISTS campaigns (id TEXT PRIMARY KEY, config TEXT, "
                       "agents TEXT, state TEXT, revision INTEGER, epoch INTEGER, owner TEXT, "
                       "lease_until REAL, request_digest TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS workers (id TEXT PRIMARY KEY, fingerprint TEXT, "
                       "capacity TEXT, certified_until REAL, evidence TEXT, simulation INTEGER)")
            db.execute("CREATE TABLE IF NOT EXISTS reservations (campaign TEXT PRIMARY KEY "
                       "REFERENCES campaigns(id), worker TEXT REFERENCES workers(id), resources TEXT, "
                       "expires REAL, active INTEGER)")
            db.execute("CREATE TABLE IF NOT EXISTS account_leases (account TEXT PRIMARY KEY, "
                       "campaign TEXT REFERENCES reservations(campaign) ON DELETE CASCADE)")
            db.execute("CREATE TABLE IF NOT EXISTS grants (hash TEXT PRIMARY KEY, campaign TEXT, "
                       "agent TEXT, role TEXT, namespace TEXT, epoch INTEGER, methods TEXT, "
                       "expires REAL, remaining INTEGER, revoked INTEGER DEFAULT 0)")
            db.execute("CREATE TABLE IF NOT EXISTS avatar_lanes (campaign TEXT REFERENCES campaigns(id), "
                       "agent TEXT, epoch INTEGER, generation INTEGER, state TEXT, repair TEXT, "
                       "lease_id TEXT, PRIMARY KEY(campaign,agent))")
            if "generation" not in {r[1] for r in db.execute("PRAGMA table_info(grants)")}:
                db.execute("ALTER TABLE grants ADD COLUMN generation INTEGER")

    def evidence(self, ref):
        require(self.cas is not None, "EVIDENCE_STORE_REQUIRED")
        return self.cas.json(Principal("operator", "operator"), self.evidence_namespace, ref)

    def validate_admission(self, config, agents):
        # Simulations exercise the same scheduler without authorizing a game process.
        # A simulation database cannot be reopened as a production controller.
        if self.simulation:
            return
        lock = PackLock.model_validate(self.evidence(config["pack_lock"]))
        require(not lock.is_example and lock.status == "sealed", "PACK_NOT_SEALED")
        for key in ("protocol_ref", "world_baseline", "information_policy", "communication_policy"):
            self.evidence(config[key])
        profile = self.evidence(config["runtime_profile"])
        require(profile.get("schema") == "strata/AdmissionEvidence/1" and
                profile.get("system_digest") == config["system_digest"] and
                profile.get("pack_lock") == config["pack_lock"] and
                profile.get("expires_at_unix", 0) > self.clock() and
                profile.get("is_example") is False, "ADMISSION_EVIDENCE_REQUIRED")
        checks = {"official_acquisition", "body_conformance", "native_host", "isolation",
                  "all_call_metering", "telemetry", "hard_budget_reservation"}
        require(set(profile.get("checks", {})) == checks, "ADMISSION_EVIDENCE_REQUIRED")
        for ref in profile["checks"].values():
            proof = self.evidence(ref)
            require(proof.get("result") == "pass" and proof.get("is_example") is False and
                    proof.get("system_digest") == config["system_digest"], "CONFORMANCE_REQUIRED")
        require(config["training_team_limits"]["spend_microusd"] is not None and
                config["evaluation_limits"]["spend_microusd"] is not None, "SPENDING_CEILING_REQUIRED")
        for agent in agents:
            for key in ("initial_skills", "inference_config", "memory_policy", "capability_profile"):
                self.evidence(agent[key])

    def create(self, config: CampaignConfig, agents: list[AgentConfig]):
        require(not config.is_example and all(not a.is_example for a in agents),
                "EXAMPLE_NOT_EXECUTABLE")
        require(len(agents) == config.n and set(config.agent_ids) == {a.agent_id for a in agents},
                "ROSTER_MISMATCH")
        require(all(a.system_digest == config.system_digest for a in agents), "SYSTEM_MISMATCH")
        require(len({a.account_ref for a in agents}) == config.n, "ACCOUNT_CONFLICT")
        data, agent_data = config.model_dump(), [a.model_dump() for a in agents]
        identity = digest({"config": data, "agents": agent_data})
        with self.database.transaction() as db:
            old = db.execute("SELECT request_digest FROM campaigns WHERE id=?",
                             (config.campaign_id,)).fetchone()
            if old:
                require(old[0] == identity, "IDEMPOTENCY_CONFLICT")
                return
            db.execute("INSERT INTO campaigns VALUES (?,?,?,'DRAFT',0,0,NULL,0,?)",
                       (config.campaign_id, canonical(data).decode(), canonical(agent_data).decode(),
                        identity))
            db.executemany("INSERT INTO avatar_lanes VALUES (?,?,0,0,'CREATED',NULL,NULL)",
                           [(config.campaign_id, agent.agent_id) for agent in agents])
            self.database.event(db, "campaign.created", {"id": config.campaign_id,
                                                        "simulation": self.simulation})

    @staticmethod
    def row(db, campaign):
        row = db.execute("SELECT * FROM campaigns WHERE id=?", (campaign,)).fetchone()
        require(row is not None, "CAMPAIGN_MISSING")
        return row

    def claim(self, campaign, owner, expected_revision):
        with self.database.transaction() as db:
            row = self.row(db, campaign)
            require(row["revision"] == expected_revision, "REVISION_CONFLICT")
            require(row["state"] not in {"COMPLETE", "ABORTED"}, "TERMINAL_STATE")
            require(row["owner"] is None or row["lease_until"] <= self.clock(), "LEASE_BUSY")
            epoch = row["epoch"] + 1
            db.execute("UPDATE campaigns SET owner=?,lease_until=?,epoch=?,revision=revision+1 "
                       "WHERE id=?", (owner, self.clock() + 6, epoch, campaign))
            db.execute("UPDATE grants SET revoked=1 WHERE campaign=?", (campaign,))
            db.execute("UPDATE avatar_lanes SET epoch=?,generation=generation+1,lease_id=NULL, "
                       "state=CASE WHEN state='CREATED' THEN state ELSE 'INTERRUPTED' END "
                       "WHERE campaign=?", (epoch, campaign))
            self.database.event(db, "campaign.claimed", {"id": campaign, "epoch": epoch})
            return epoch

    def owned(self, db, campaign, owner, epoch):
        row = self.row(db, campaign)
        require(row["owner"] == owner and row["epoch"] == epoch
                and row["lease_until"] > self.clock(), "LEASE_EXPIRED")
        return row

    def heartbeat(self, campaign, owner, epoch):
        with self.database.transaction() as db:
            self.owned(db, campaign, owner, epoch)
            db.execute("UPDATE campaigns SET lease_until=? WHERE id=?", (self.clock() + 6, campaign))

    def _transition(self, db, row, state, reason):
        require(state in TRANSITIONS[row["state"]] or state == "ABORTED"
                and row["state"] not in {"COMPLETE", "ABORTED"}, "INVALID_TRANSITION")
        db.execute("UPDATE campaigns SET state=?,revision=revision+1 WHERE id=?", (state, row["id"]))
        self.database.event(db, "campaign.transition", {"campaign": row["id"], "from": row["state"],
                            "to": state, "reason": reason, "epoch": row["epoch"]})

    def transition(self, campaign, owner, epoch, revision, state, reason, *, cleanup_ref=None):
        # Admission/readiness are the only entry points to starting/running.
        require(state not in {"STARTING", "RUNNING"}, "READINESS_REQUIRED")
        with self.database.transaction() as db:
            row = self.owned(db, campaign, owner, epoch)
            require(row["revision"] == revision, "REVISION_CONFLICT")
            if state in {"COMPLETE", "ABORTED"}:
                require(cleanup_ref is not None, "CLEANUP_REQUIRED")
                if not self.simulation:
                    proof = self.evidence(cleanup_ref)
                    require(proof.get("campaign_id") == campaign and proof.get("epoch") == epoch
                            and proof.get("stopped") is True, "CLEANUP_REQUIRED")
                db.execute("UPDATE grants SET revoked=1 WHERE campaign=?", (campaign,))
                db.execute("DELETE FROM reservations WHERE campaign=?", (campaign,))
            self._transition(db, row, state, reason)

    def certify(self, worker, fingerprint, capacity, evidence_ref, *, simulation, lifetime_s=86400):
        require(simulation == self.simulation, "PROFILE_MISMATCH")
        require(set(capacity) == RESOURCES and all(type(v) is int and v >= 0
                                                  for v in capacity.values()), "CAPACITY_RANGE")
        require(0 < lifetime_s <= 86400 and evidence_ref.startswith("cas:sha256:"),
                "CERTIFICATE_REQUIRED")
        if not self.simulation:
            proof = self.evidence(evidence_ref)
            require(proof.get("schema") == "strata/CapacityCertificate/1" and
                    proof.get("fingerprint") == fingerprint and proof.get("capacity") == capacity
                    and proof.get("is_example") is False and proof.get("result") == "pass"
                    and proof.get("stress_minutes", 0) >= 30 and proof.get("soak_hours", 0) >= 24,
                    "CAPACITY_UNCERTIFIED")
        with self.database.transaction() as db:
            old = db.execute("SELECT fingerprint FROM workers WHERE id=?", (worker,)).fetchone()
            if old and old[0] != fingerprint:
                require(db.execute("SELECT 1 FROM reservations WHERE worker=?", (worker,)).fetchone()
                        is None, "WORKER_IN_USE")
            db.execute("INSERT OR REPLACE INTO workers VALUES (?,?,?,?,?,?)",
                       (worker, fingerprint, canonical(capacity).decode(),
                        self.clock() + lifetime_s, evidence_ref, int(simulation)))

    def admit(self, campaign, owner, epoch, revision, worker, fingerprint, resources):
        require(set(resources) == RESOURCES and all(type(v) is int and v >= 0
                                                   for v in resources.values()), "CAPACITY_RANGE")
        with self.database.transaction() as db:
            row = self.owned(db, campaign, owner, epoch)
            require(row["revision"] == revision, "REVISION_CONFLICT")
            require(row["state"] in {"VALIDATING", "QUEUED"}, "INVALID_TRANSITION")
            config = json.loads(row["config"])
            self.validate_admission(config, json.loads(row["agents"]))
            require(resources["bodies"] == config["n"], "PARTIAL_TEAM_FORBIDDEN")
            cert = db.execute("SELECT * FROM workers WHERE id=?", (worker,)).fetchone()
            require(cert is not None and cert["certified_until"] > self.clock()
                    and cert["fingerprint"] == fingerprint, "CAPACITY_UNCERTIFIED")
            available = json.loads(cert["capacity"])
            # Expired reservations remain held until supervisor stop/cleanup is recorded.
            # Releasing on TTL alone could overbook a live but unresponsive worker.
            for reservation in db.execute("SELECT resources FROM reservations WHERE worker=?",
                                          (worker,)):
                for key, used in json.loads(reservation[0]).items():
                    available[key] -= used
            accounts = [a["account_ref"] for a in json.loads(row["agents"])]
            shortage = any(resources[k] > available[k] for k in resources)
            shortage |= any(db.execute("SELECT 1 FROM account_leases WHERE account=?", (a,))
                            .fetchone() is not None for a in accounts)
            if shortage:
                if config["admission"] == "reject":
                    raise Fault("CAPACITY_EXCEEDED")
                if row["state"] != "QUEUED":
                    self._transition(db, row, "QUEUED", "capacity")
                return "QUEUED"
            db.execute("INSERT INTO reservations VALUES (?,?,?,?,0)",
                       (campaign, worker, canonical(resources).decode(), self.clock() + 120))
            db.executemany("INSERT INTO account_leases VALUES (?,?)", [(a, campaign) for a in accounts])
            self._transition(db, row, "STARTING", "whole-team-reserved")
            return "STARTING"

    def ready(self, campaign, owner, epoch, revision, readiness, *, resume_evidence=None):
        with self.database.transaction() as db:
            row = self.owned(db, campaign, owner, epoch)
            require(row["revision"] == revision, "REVISION_CONFLICT")
            require(row["state"] in {"STARTING", "CHECKPOINTING", "RECOVERING"}, "INVALID_TRANSITION")
            config = json.loads(row["config"])
            require(set(readiness) == set(config["agent_ids"]) and all(
                set(proof) == READINESS and all(isinstance(ref, str) and
                    ref.startswith("cas:sha256:") for ref in proof.values())
                for proof in readiness.values()), "TEAM_NOT_READY")
            if not self.simulation:
                for agent, proofs in readiness.items():
                    for kind, ref in proofs.items():
                        proof = self.evidence(ref)
                        require(proof.get("campaign_id") == campaign and proof.get("agent_id") == agent
                                and proof.get("epoch") == epoch and proof.get("kind") == kind
                                and proof.get("ready") is True and
                                self.clock() - 2 <= proof.get("observed_unix", 0) <= self.clock(),
                                "TEAM_NOT_READY")
            reservation = db.execute("SELECT * FROM reservations WHERE campaign=?", (campaign,))
            reservation = reservation.fetchone()
            require(reservation is not None and (reservation["active"] or
                    reservation["expires"] > self.clock()), "RESERVATION_EXPIRED")
            if row["state"] != "STARTING":
                require(resume_evidence is not None, "RESUME_EVIDENCE_REQUIRED")
            db.execute("UPDATE reservations SET active=1 WHERE campaign=?", (campaign,))
            lanes = db.execute("SELECT * FROM avatar_lanes WHERE campaign=?", (campaign,)).fetchall()
            # Missing legacy lane authority is not reconstructed from old grants.
            require({lane["agent"] for lane in lanes} == set(config["agent_ids"]),
                    "INPUT_AUTHORITY_REQUIRED")
            require(all(lane["repair"] is None for lane in lanes), "RECONFIGURATION_PENDING")
            for lane in lanes:
                db.execute("UPDATE avatar_lanes SET state='READY',epoch=?,generation=generation+1, "
                           "lease_id=? WHERE campaign=? AND agent=?",
                           (epoch, secrets.token_hex(16), campaign, lane["agent"]))
            self._transition(db, row, "RUNNING", "all-bodies-ready")

    def grant(self, campaign, owner, epoch, agent, namespace, methods, *, role="executor", ttl=6,
              quota=100):
        require(role in {"executor", "helper"} and 0 < ttl <= 6 and quota > 0, "GRANT_RANGE")
        allowed = {"observe", "capabilities", "wait_events", "recipes.list", "artifact.read"}
        if role == "executor":
            allowed |= {"act", "action_status", "cancel", "stop_all", "artifact.write",
                        "team.send", "team.receive"}
        require(set(methods) <= allowed, "FORBIDDEN")
        token = secrets.token_urlsafe(32)
        with self.database.transaction() as db:
            row = self.owned(db, campaign, owner, epoch)
            require(agent in json.loads(row["config"])["agent_ids"], "FORBIDDEN")
            require(namespace == f"campaign:{campaign}:agent:{agent}", "FORBIDDEN")
            require(row["state"] in {"STARTING", "RUNNING"}, "INVALID_TRANSITION")
            lane = self.lane(db, campaign, agent)
            if "act" in methods:
                require(lane["epoch"] == epoch and lane["state"] in {"READY", "OBSERVING"}
                        and lane["repair"] is None and lane["lease_id"] is not None,
                        "INPUT_SUSPENDED")
                # Grant replacement cannot leave two input-bearing authorities.
                for old in db.execute("SELECT hash,methods FROM grants WHERE campaign=? AND agent=? "
                                      "AND revoked=0", (campaign, agent)).fetchall():
                    if "act" in json.loads(old["methods"]):
                        db.execute("UPDATE grants SET revoked=1 WHERE hash=?", (old["hash"],))
            db.execute("INSERT INTO grants (hash,campaign,agent,role,namespace,epoch,methods,expires,"
                       "remaining,revoked,generation) VALUES (?,?,?,?,?,?,?,?,?,0,?)",
                       (hashlib.sha256(token.encode()).hexdigest(), campaign, agent, role, namespace,
                        epoch, canonical(sorted(methods)).decode(), self.clock() + ttl, quota,
                        lane["generation"]))
        return token  # deliver through a protected file/IPC, never model text or command args

    def authorize(self, token, campaign, agent, epoch, method, deadline):
        with self.database.transaction() as db:
            grant = db.execute("SELECT * FROM grants WHERE hash=?",
                               (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
            require(grant is not None, "FORBIDDEN")
            row = self.row(db, campaign)
            require(not grant["revoked"] and grant["campaign"] == campaign and
                    grant["agent"] == agent and grant["epoch"] == epoch == row["epoch"] and
                    grant["expires"] > self.clock() and row["lease_until"] > self.clock() and
                    row["state"] in {"STARTING", "RUNNING"} and
                    method in json.loads(grant["methods"]), "FORBIDDEN")
            require(self.clock() < deadline <= self.clock() + 5.25, "DEADLINE_INVALID")
            if method == "act":
                lane = self.lane(db, campaign, agent)
                require(lane["epoch"] == epoch and lane["state"] in {"READY", "OBSERVING"}
                        and lane["repair"] is None and lane["lease_id"] is not None
                        and grant["generation"] == lane["generation"], "INPUT_SUSPENDED")
            require(grant["remaining"] > 0, "QUOTA_EXHAUSTED")
            db.execute("UPDATE grants SET remaining=remaining-1 WHERE hash=?", (grant["hash"],))
            return Principal(grant["namespace"], grant["role"])

    @staticmethod
    def lane(db, campaign, agent):
        row = db.execute("SELECT * FROM avatar_lanes WHERE campaign=? AND agent=?",
                         (campaign, agent)).fetchone()
        require(row is not None, "INPUT_AUTHORITY_REQUIRED")
        return row

    def input_authority(self, campaign, owner, epoch, agent):
        with self.database.transaction() as db:
            self.owned(db, campaign, owner, epoch)
            return dict(self.lane(db, campaign, agent))

    def status(self, campaign):
        row = self.row(self.database.connection, campaign)
        return {k: row[k] for k in ("id", "state", "revision", "epoch", "lease_until")}
