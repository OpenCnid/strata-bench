"""Owned synthetic checkpoint continuation for the selected campaign catalog.

Readiness is synthetic. This never creates production qualification or changes
the copied campaign/configuration, allowance, checkpoint or historical epoch.
"""

import json
import threading
import time

from mcbench.controller import Controller, READINESS
from mcbench.native_team import require_team_plan
from mcbench.native_process_drain import require_process_drain
from mcbench.storage import Database, Principal, canonical, require
from mcbench.team_protocol import TeamPolicy

OWNER = "selected-activation-fixture"


class ActivationController:
    def __init__(self, runtime, body, plan):
        self.runtime, self.body, self.plan = runtime, body, plan
        self.thread = None
        self.stop_event = threading.Event()
        self.started = threading.Event()
        self.errors, self.heartbeats = [], []
        self.entered = False
        self.policy_ref = None
        self.checkpoint_transition = None

    def __enter__(self):
        require(not self.entered, "ACTIVATION_CONTROLLER_REARM")
        self.entered = True
        runtime, body, plan = self.runtime, self.body, self.plan
        db = runtime.db.connection
        require(runtime.simulation is True and body["is_example"] is True
                and body["model_identity"] == plan.model == "gpt-6-luna"
                and plan.campaign_id == body["campaign_id"] and plan.agent_id == body["agent_id"]
                and plan.epoch == body["source_epoch"] + 1, "ACTIVATION_CONTROLLER_SCOPE")
        profile = db.execute("SELECT simulation FROM controller_profile").fetchall()
        require(len(profile) == 1 and profile[0][0] == 1, "ACTIVATION_CONTROLLER_SCOPE")
        row = db.execute("SELECT * FROM campaigns WHERE id=?", (plan.campaign_id,)).fetchone()
        require(row is not None and row["state"] == "CHECKPOINTING" and row["epoch"] == body["source_epoch"],
                "ACTIVATION_CONTROLLER_CHECKPOINT")
        config, agents = json.loads(row["config"]), json.loads(row["agents"])
        require(config["system_digest"] == body["system_digest"] and config["agent_ids"] == [plan.agent_id]
                and config["n"] == len(agents) == 1 and agents[0]["requested_model"] == plan.model,
                "ACTIVATION_CONTROLLER_SCOPE")
        policy_ref = config["communication_policy"]
        private = db.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?", (policy_ref,)).fetchone()
        require(private is not None and private[0] == "operator", "TEAM_POLICY_PRIVATE")
        policy = TeamPolicy.model_validate(runtime.cas.json(Principal("operator", "operator"), "operator", policy_ref))
        require(policy.is_example and policy.mode == "campaign_roster", "TEAM_POLICY_SCOPE")
        require(row["owner"] is None or row["lease_until"] <= time.time(), "LEASE_BUSY")
        proof = runtime.cas.put(Principal("operator", "operator"), "operator", "operator", canonical({
            "schema": "strata/SyntheticActivationReadiness/1", "is_example": True,
            "campaign_id": plan.campaign_id, "agent_id": plan.agent_id, "epoch": plan.epoch,
            "checkpoint_ref": body["checkpoint_ref"], "source_epoch": body["source_epoch"],
            "real_game_bodies": 0, "production_qualified": False}))
        controller = Controller(runtime.db, simulation=True)
        epoch = controller.claim(plan.campaign_id, OWNER, row["revision"])
        require(epoch == plan.epoch, "ACTIVATION_CONTROLLER_SCOPE")
        controller.ready(plan.campaign_id, OWNER, epoch, controller.status(plan.campaign_id)["revision"],
                         {plan.agent_id: dict.fromkeys(READINESS, proof)}, resume_evidence=proof)
        self.policy_ref = policy_ref
        def heartbeat():
            connection = Database(runtime.db.path)
            try:
                owned = Controller(connection, simulation=True)
                while not self.stop_event.is_set():
                    owned.heartbeat(plan.campaign_id, OWNER, plan.epoch)
                    self.heartbeats.append(time.time_ns() // 1000000)
                    self.started.set()
                    self.stop_event.wait(0.5)
            except Exception as error:
                self.errors.append(type(error).__name__ + ":" + str(error))
                self.stop_event.set()
                self.started.set()
            finally:
                connection.close()
        self.thread = threading.Thread(target=heartbeat, name="activation-controller", daemon=True)
        self.thread.start()
        if not self.started.wait(2) or self.errors or not self.heartbeats:
            self.__exit__()
            require(False, "ACTIVATION_CONTROLLER_HEARTBEAT")
        return self

    def healthy(self, plan):
        require(self.thread is not None and self.thread.is_alive() and self.heartbeats and not self.errors
                and not self.stop_event.is_set(), "ACTIVATION_CONTROLLER_HEARTBEAT")
        require_team_plan(self.runtime.db.connection, self.runtime.cas, plan)

    def __exit__(self, *_):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(5)
            require(not self.thread.is_alive(), "ACTIVATION_CONTROLLER_DRAIN")

    def begin_checkpoint(self, plan):
        """Normal stopped boundary while this exact controller owner is held."""
        require(self.checkpoint_transition is None, "ACTIVATION_CHECKPOINT_REARM")
        self.healthy(plan)
        require((plan.campaign_id, plan.agent_id, plan.epoch) ==
                (self.plan.campaign_id, self.plan.agent_id, self.plan.epoch), "ACTIVATION_CONTROLLER_SCOPE")
        status = self.runtime.status(plan.job_id)
        require(status["state"] == "FINALIZED" and status["returncode"] == 0
                and status["reason"] == "native_exit" and plan.job_id not in self.runtime.live,
                "ACTIVATION_CHECKPOINT_NOT_NORMAL")
        proof = require_process_drain(self.runtime.db.connection, self.runtime.cas, plan)
        observed = self.runtime.cas.json(Principal("operator", "operator"), "operator", proof["proof_ref"])
        require(observed["observation"]["accounting"]["terminated_processes"] == 0,
                "ACTIVATION_CHECKPOINT_NOT_NORMAL")
        controller = Controller(self.runtime.db, simulation=True)
        before = controller.status(plan.campaign_id)
        controller.transition(plan.campaign_id, OWNER, plan.epoch, before["revision"],
                              "CHECKPOINTING", "normal native fixture episode boundary")
        self.checkpoint_transition = {"job_id": plan.job_id, "epoch": plan.epoch,
            "from_revision": before["revision"], "state": controller.status(plan.campaign_id)["state"],
            "process_drain": proof, "complete_checkpoint": False}
        return self.checkpoint_transition

    def report(self):
        return {"is_example": True, "controller_readiness": "synthetic", "real_game_bodies": 0,
                "campaign_id": self.plan.campaign_id, "epoch": self.plan.epoch,
                "source_epoch": self.body["source_epoch"], "policy_ref": self.policy_ref,
                "checkpoint_transition": self.checkpoint_transition,
                "thread_stopped": self.thread is not None and not self.thread.is_alive(),
                "heartbeats": self.heartbeats, "errors": self.errors, "production_qualified": False}
