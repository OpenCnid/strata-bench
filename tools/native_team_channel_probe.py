"""Owned synthetic controller plus actual native roster-message fixture.

No provider spending, game bodies, runtime qualification or production authority.
The private store is shared; native profiles/artifacts and designated identities
remain separate. Sequential jobs test durable delivery across native shutdown.
"""

import json
import threading
import time
from pathlib import Path

from mcbench.communication import Communication
from mcbench.controller import Controller, READINESS
from mcbench.records import AgentConfig, CampaignConfig
from mcbench.storage import CAS, Database, Principal, canonical, require
from mcbench.team_protocol import TeamPolicy, TeamResponse
from native_helper_pair_probe import HelperPairProbe, ROOT
from native_state_canaries import records

CHILD = ROOT + "/identity_child"
ACTORS = (ROOT, CHILD)
OWNER = "team-channel-fixture"
FOREIGN = "foreign-campaign"
FOREIGN_MARKER = "STRATA_FOREIGN_TEAM_MAIL_CANARY"
PAYLOADS = ("STRATA_TEAM_PUBLIC_FIRST", "STRATA_TEAM_PUBLIC_SECOND")
DONE = "STRATA_TEAM_HELPER_DONE"
POLICY = {"schema": "strata/CommunicationPolicy/1", "is_example": True, "mode": "campaign_roster",
          "max_body_bytes": 4096, "sends_per_minute": 10, "queue_limit": 100,
          "max_ttl_s": 600, "helper_access": False}


class TeamChannelStore:
    """An owned controller fixture; its heartbeat never reclaims an expired lease."""

    def __init__(self, root, campaign, agents):
        self.root = Path(root).absolute()
        require(not self.root.exists(), "TEAM_FIXTURE_EXISTS")
        campaign = CampaignConfig.model_validate(campaign.model_dump())
        agents = [AgentConfig.model_validate(a.model_dump()) for a in agents]
        require(campaign.n == 2 and campaign.agent_ids == ["a1", "a2"]
                and campaign.campaign_id != FOREIGN, "TEAM_FIXTURE_ROSTER")
        self.root.mkdir(parents=True)
        self.database = self.root / "synthetic.sqlite"
        self.objects = self.root / "objects"
        self.campaign_id = campaign.campaign_id
        self.epochs, self.heartbeats, self.errors = {}, [], []
        self.stop_event = threading.Event()
        self.thread = None
        db = Database(self.database)
        try:
            cas = CAS(db, self.objects)
            self.policy_ref = cas.put(Principal("operator", "operator"), "operator", "operator",
                                      canonical(TeamPolicy.model_validate(POLICY).model_dump()))
            evidence = cas.put(Principal("operator", "operator"), "operator", "operator",
                canonical({"schema": "strata/SyntheticTeamReadiness/1", "is_example": True,
                           "real_game_bodies": 0, "production_qualified": False}))
            controller = Controller(db, simulation=True)
            capacity = {"bodies": 4, "memory_mib": 16000, "disk_bytes": 100000000, "model_slots": 4}
            controller.certify("owned-synthetic-worker", "synthetic", capacity, evidence, simulation=True)
            for identity in (campaign.campaign_id, FOREIGN):
                config = campaign.model_copy(update={"campaign_id": identity, "communication_policy": self.policy_ref})
                roster = [a.model_copy(update={"account_ref": identity + ":" + a.agent_id}) for a in agents]
                controller.create(config, roster)
                epoch = controller.claim(identity, OWNER, 0)
                self.epochs[identity] = epoch
                for state in ("PROVISIONING", "VALIDATING"):
                    controller.transition(identity, OWNER, epoch, controller.status(identity)["revision"], state,
                                          "synthetic native team contract fixture; no game bodies")
                controller.admit(identity, OWNER, epoch, controller.status(identity)["revision"],
                    "owned-synthetic-worker", "synthetic", capacity | {"bodies": 2, "model_slots": 2,
                        "memory_mib": 1000, "disk_bytes": 1000})
                controller.ready(identity, OWNER, epoch, controller.status(identity)["revision"],
                    {a.agent_id: dict.fromkeys(READINESS, evidence) for a in roster})
            Communication(db).send(Principal(f"campaign:{FOREIGN}:agent:a2", "executor"),
                                  FOREIGN, "a2", "foreign-private-mail", FOREIGN_MARKER, ["a1"])
        finally:
            db.close()

    def __enter__(self):
        def heartbeat():
            db = Database(self.database)
            try:
                controller = Controller(db, simulation=True)
                while not self.stop_event.is_set():
                    for campaign, epoch in self.epochs.items():
                        controller.heartbeat(campaign, OWNER, epoch)
                        self.heartbeats.append({"campaign": campaign, "unix_ms": time.time_ns() // 1000000})
                    self.stop_event.wait(0.5)
            except Exception as exc:
                self.errors.append(type(exc).__name__ + ":" + str(exc))
                self.stop_event.set()
            finally:
                db.close()
        require(self.thread is None, "TEAM_FIXTURE_REARM")
        self.thread = threading.Thread(target=heartbeat, name="owned-team-controller", daemon=True)
        self.thread.start()
        return self

    def healthy(self):
        require(self.thread is not None and self.thread.is_alive() and not self.errors
                and not self.stop_event.is_set(), "TEAM_FIXTURE_HEARTBEAT")

    def __exit__(self, *_):
        self.stop_event.set()
        self.thread.join(5)
        require(not self.thread.is_alive(), "TEAM_FIXTURE_HEARTBEAT_DRAIN")
        (self.root / "heartbeat.json").write_bytes(canonical({"is_example": True,
            "heartbeats": self.heartbeats, "errors": self.errors, "thread_stopped": True}))


class TeamChannelProbe(HelperPairProbe):
    def __init__(self, store, mode):
        super().__init__()
        require(type(store) is TeamChannelStore and mode in {"sender", "receiver"}, "TEAM_FIXTURE_MODE")
        self.store, self.mode = store, mode
        self.agent_id = "a1" if mode == "sender" else "a2"
        self.job_id = "team-" + mode
        self.scope = {"campaign_id": store.campaign_id, "agent_id": self.agent_id,
                      "epoch": store.epochs[store.campaign_id], "account": store.campaign_id + ":" + self.agent_id}

    def request(self, request_id, operation, **updates):
        return {"schema": "strata/TeamRequest/1", "request_id": self.job_id + ":" + request_id,
            "campaign_id": self.scope["campaign_id"], "agent_id": self.agent_id,
            "epoch": self.scope["epoch"], "deadline_at": "replaced-immediately-before-dispatch",
            "operation": operation, **updates}

    @staticmethod
    def receive(**updates):
        return {"kind": "receive", "after": 0, "limit": 1, "acknowledge": [], **updates}

    def cases(self, actor):
        require(actor in ACTORS, "TEAM_FIXTURE_ACTOR")
        negative = [("wrong_campaign", self.request("foreign", self.receive(), campaign_id=FOREIGN)),
            ("wrong_sender", self.request("sender", self.receive(), agent_id="a2" if self.agent_id == "a1" else "a1")),
            ("stale_epoch", self.request("epoch", self.receive(), epoch=0)),
            ("foreign_recipient", self.request("outsider", {"kind": "send", "message_id": "outside",
                "recipients": ["outsider"], "body": "not delivered", "ttl_s": 600}))]
        # Epoch 2 is valid syntax but has no lease; test identity fencing rather
        # than only the integer parser. The actual campaign remains at epoch 1.
        negative[2][1]["epoch"] = 2
        if actor == CHILD:
            return [("helper", self.request("helper", self.receive())), *negative[:2]]
        if self.mode == "sender":
            first = self.request("send-first", {"kind": "send", "message_id": "first",
                "recipients": ["a2"], "body": PAYLOADS[0], "ttl_s": 600})
            return [("initial_empty", self.request("initial", self.receive())), ("send_first", first),
                ("send_retry", first), ("send_second", self.request("send-second", first["operation"] |
                {"message_id": "second", "body": PAYLOADS[1]})), *negative]
        return [("receive_first", self.request("receive-first", self.receive())),
            ("receive_second", self.request("receive-second", self.receive(after=1))),
            ("acknowledge", self.request("acknowledge", self.receive(acknowledge=["first", "second"]))),
            ("after_ack", self.request("after-ack", self.receive(limit=100))), *negative]

    def start(self, actor, operation, code):
        code += '\nconst teamTool=ALL_TOOLS.find(t=>t.name.endsWith("__team"));'
        code += 'if(!teamTool) throw new Error("TEAM_TOOL_MISSING");'
        code += 'text({probe:"team_catalog",names:ALL_TOOLS.filter(t=>t.name.includes("strata_broker")).map(t=>t.name)});'
        code += 'for(const [probe,request] of ' + json.dumps(self.cases(actor)) + ') {'
        code += 'request.deadline_at=new Date(Date.now()+3000).toISOString();'
        code += 'text({probe,result:await tools[teamTool.name]({request})});}'
        return self.call(actor, "initialize", operation, code=code)

    def next(self, actor, step, operation):
        require(actor in ACTORS and 1 <= step <= 8, "TEAM_FIXTURE_SEQUENCE")
        if actor == ROOT and self.phases[actor] == 0:
            self.phases[actor] = 1
            return [self.call(actor, "spawn", operation, name="spawn_agent", args={
                "task_name": "identity_child", "fork_turns": "none",
                "message": "Exercise the fixed synthetic broker helper-refusal fixture. No inherited parent history."})]
        if actor == ROOT and not self.received(CHILD, ROOT, DONE, "FINAL_ANSWER"):
            self.waits[actor] += 1
            require(self.waits[actor] <= 4, "TEAM_FIXTURE_DELIVERY_BOUND")
            return [self.call(actor, "wait", operation, name="wait_agent", args={"timeout_ms": 10000})]
        self.finished.add(actor)
        return [{"id": "message-" + operation, "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": DONE if actor == CHILD else "Synthetic team fixture complete.",
                         "annotations": []}]}]

    def report(self):
        by_actor = {}
        for actor in ACTORS:
            values = [self.outputs[key] for key, value in self.calls.items()
                      if value == {"actor": actor, "phase": "initialize"} and key in self.outputs]
            parsed = [r for v in values for r in records(v) if "probe" in r]
            by_actor[actor] = parsed
        checks = {"team_both_finished": self.finished == set(ACTORS),
                  "team_foreign_mail_absent": all(FOREIGN_MARKER not in json.dumps(r["body"]) for r in self.requests)}
        expected_errors = {"wrong_campaign": "BROKER_SCOPE", "wrong_sender": "BROKER_SCOPE",
                           "stale_epoch": "BROKER_SCOPE", "foreign_recipient": "FORBIDDEN"}
        responses = {}
        for actor in ACTORS:
            expected = {label for label, _ in self.cases(actor)}
            catalogs = [r for r in by_actor[actor] if r["probe"] == "team_catalog"]
            names = catalogs[0].get("names", []) if len(catalogs) == 1 else []
            checks[actor + "_team_catalog"] = len(names) == 5 and {
                n.rsplit("__", 1)[-1] for n in names if isinstance(n, str)} == {
                    "artifact_read", "artifact_write", "artifact_list", "game", "team"}
            seen = [r["probe"] for r in by_actor[actor] if r["probe"] != "team_catalog"]
            checks[actor + "_all_cases_returned_once"] = set(seen) == expected and len(seen) == len(expected)
            for row in by_actor[actor]:
                if row["probe"] == "team_catalog":
                    continue
                result = row.get("result", {})
                error = "BROKER_TEAM_FORBIDDEN" if actor == CHILD else expected_errors.get(row["probe"])
                if error:
                    checks[actor + ":" + row["probe"]] = result == {"isError": True,
                        "content": [{"type": "text", "text": error}]}
                else:
                    content = result.get("content")
                    valid = False
                    if isinstance(content, list) and len(content) == 1 and content[0].get("type") == "text" and not result.get("isError"):
                        try:
                            response = TeamResponse.model_validate_json(content[0]["text"]).model_dump()
                            wanted = dict(self.cases(actor))[row["probe"]]["request_id"]
                            valid = response["request_id"] == wanted
                            if valid:
                                responses[row["probe"]] = response
                        except (ValueError, TypeError, KeyError):
                            pass
                    checks[actor + ":" + row["probe"] + ":typed_response"] = valid
        if self.mode == "sender":
            checks["team_initial_empty"] = responses.get("initial_empty", {}).get("result", {}).get("messages") == []
            checks["team_send_retry_identical"] = responses.get("send_first") is not None and responses.get("send_first") == responses.get("send_retry")
            checks["team_send_order"] = [responses.get(k, {}).get("result", {}).get("sender_seq") for k in
                                         ("send_first", "send_second")] == [1, 2]
        else:
            for index, label in enumerate(("receive_first", "receive_second")):
                value = responses.get(label, {}).get("result", {})
                messages = value.get("messages", [])
                checks["team_" + label] = len(messages) == 1 and messages[0].get("body") == PAYLOADS[index] and (
                    messages[0].get("cursor") == index + 1 and value.get("has_more") is (index == 0))
            checks["team_explicit_ack_empty"] = all(responses.get(label, {}).get("result", {}).get("messages") == []
                                                    for label in ("acknowledge", "after_ack"))
        return {"is_example": True, "mode": self.mode, "job_id": self.job_id, "scope": self.scope,
                "checks": checks, "calls": self.calls, "outputs": self.outputs}
