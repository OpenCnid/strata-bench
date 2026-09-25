"""Owned separate native jobs: known foreign IDs versus scoped message controls."""

import json
import re
import threading
import time
import uuid

from mcbench.native_admission import context_metadata
from mcbench.storage import require
from native_helper_pair_probe import HelperPairProbe, ROOT

CHILD = "/root/identity_child"
ACTORS = (ROOT, CHILD)
TEAMS = ("alpha", "beta")
MISSING = "00000000-0000-4000-8000-000000000000"
METHODS = ("send_message", "followup_task", "interrupt_agent")


def review_denials(report, identities):
    """Exact observed native error, anchored to known foreign and absent IDs.

    Caller must first reconstruct calls/returns from authenticated captures and
    issued-response receipts. This never promotes a bare result.json to proof.
    """
    team = report.get("team")
    require(
        team in TEAMS
        and set(identities) == set(TEAMS)
        and all(set(v) == set(ACTORS) for v in identities.values()),
        "CROSS_TEAM_REVIEW_SCOPE",
    )
    ids = [value for row in identities.values() for value in row.values()]
    require(
        all(
            isinstance(v, str) and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", v)
            for v in ids
        )
        and len(set(ids)) == 4
        and MISSING not in ids,
        "CROSS_TEAM_REVIEW_SCOPE",
    )
    foreign = next(t for t in TEAMS if t != team)
    expected = {
        "foreign_root": identities[foreign][ROOT],
        "foreign_helper": identities[foreign][CHILD],
        "absent": MISSING,
    }
    require(report.get("targets") == dict.fromkeys(ACTORS, expected), "CROSS_TEAM_REVIEW_TARGETS")
    seen = set()
    for key, call in report["calls"].items():
        phase = call["phase"]
        matches = [
            (kind, method)
            for kind in expected
            for method in METHODS
            if phase == kind + "_" + method
        ]
        if not matches:
            continue
        kind, method = matches[0]
        identity = (call["actor"], kind, method)
        require(call["actor"] in ACTORS and identity not in seen, "CROSS_TEAM_REVIEW_DUPLICATE")
        seen.add(identity)
        require(
            report["outputs"].get(key) == "agent with id " + expected[kind] + " not found",
            "CROSS_TEAM_REVIEW_DENIAL",
        )
    require(
        seen
        == {(actor, kind, method) for actor in ACTORS for kind in expected for method in METHODS},
        "CROSS_TEAM_REVIEW_INCOMPLETE",
    )
    return {
        "policy": "native-separate-job-known-id-denial/1",
        "checked": len(seen),
        "foreign_denials": 12,
        "absent_controls": 6,
        "is_example": True,
        "campaign_team_api_qualified": False,
    }


class CrossTeamCoordinator:
    """Private test control, never a runtime tool or real inference gateway."""

    def __init__(self):
        self.lock = threading.Lock()
        self.barrier = threading.Barrier(2)
        self.identities = {team: {} for team in TEAMS}
        self.ready, self.attacked = set(), set()
        self.timeline = []
        self.canaries = {team: "STRATA_CROSS_TEAM_PRIVATE_" + uuid.uuid4().hex for team in TEAMS}

    def record(self, team, actor, body):
        meta = context_metadata(body)
        require(
            team in TEAMS and actor in ACTORS and meta["agent_name"] == actor, "CROSS_TEAM_IDENTITY"
        )
        with self.lock:
            known = self.identities[team].get(actor)
            require(known is None or known == meta["thread_id"], "CROSS_TEAM_IDENTITY_CHANGED")
            others = {
                value
                for t in TEAMS
                for a, value in self.identities[t].items()
                if (t, a) != (team, actor)
            }
            require(
                meta["thread_id"] not in others and meta["thread_id"] != MISSING,
                "CROSS_TEAM_IDENTITY_COLLISION",
            )
            self.identities[team][actor] = meta["thread_id"]

    def mark(self, phase, team, actor):
        with self.lock:
            target = self.ready if phase == "ready" else self.attacked
            key = team if phase == "ready" else (team, actor)
            if key not in target:
                target.add(key)
                self.timeline.append(
                    {
                        "phase": phase,
                        "team": team,
                        "actor": actor,
                        "at_unix_ms": time.time_ns() // 1_000_000,
                    }
                )

    def ready_for_attempts(self):
        with self.lock:
            return self.ready == set(TEAMS) and all(
                set(ids) == set(ACTORS) for ids in self.identities.values()
            )

    def targets(self, team):
        require(team in TEAMS and self.ready_for_attempts(), "CROSS_TEAM_NOT_READY")
        with self.lock:
            foreign = next(t for t in TEAMS if t != team)
            return {
                "foreign_root": self.identities[foreign][ROOT],
                "foreign_helper": self.identities[foreign][CHILD],
                "absent": MISSING,
            }

    def all_attempts_observed(self):
        with self.lock:
            return self.attacked == {(t, a) for t in TEAMS for a in ACTORS}


class CrossTeamProbe(HelperPairProbe):
    def __init__(self, coordinator, team):
        require(type(coordinator) is CrossTeamCoordinator and team in TEAMS, "CROSS_TEAM_SCOPE")
        super().__init__()
        self.coordinator, self.team = coordinator, team
        self.phases = dict.fromkeys(ACTORS, 0)
        self.waits = dict.fromkeys(ACTORS, 0)
        self.syncs = 0
        self.attempt_targets = {}

    def before_launch(self):
        self.coordinator.barrier.wait(timeout=60)

    def marker(self, phase):
        return "STRATA_CROSS_" + self.team + "_" + phase

    def observe(self, actor, body):
        self.coordinator.record(self.team, actor, body)
        super().observe(actor, body)

    def start(self, actor, operation, code):
        code += (
            '\ntext({probe:"own_private",value:'
            + json.dumps(self.coordinator.canaries[self.team])
            + "});"
        )
        return self.call(actor, "initialize", operation, code=code)

    def wait(self, actor, operation):
        self.waits[actor] += 1
        require(self.waits[actor] <= 5, "CROSS_TEAM_DELIVERY_BOUND")
        return self.call(actor, "wait", operation, name="wait_agent", args={"timeout_ms": 10000})

    def attacks(self, actor, operation):
        targets = self.coordinator.targets(self.team)
        self.attempt_targets[actor] = targets
        items = []
        for target_kind, target in targets.items():
            for method in METHODS:
                args = {"target": target}
                if method != "interrupt_agent":
                    args["message"] = self.coordinator.canaries[self.team]
                items.append(
                    self.call(actor, target_kind + "_" + method, operation, name=method, args=args)
                )
        return items

    def next(self, actor, step, operation):
        require(actor in ACTORS and 1 <= step <= 18, "CROSS_TEAM_SEQUENCE")
        phase = self.phases[actor]
        if actor == ROOT:
            if phase == 0:
                self.phases[actor] += 1
                return [
                    self.call(
                        actor,
                        "spawn",
                        operation,
                        name="spawn_agent",
                        args={
                            "task_name": "identity_child",
                            "fork_turns": "none",
                            "message": "Exercise only the owned cross-team fixture and permitted local messages.",
                        },
                    )
                ]
            if phase == 1:
                if not self.received(CHILD, ROOT, self.marker("ready")):
                    return [self.wait(actor, operation)]
                self.coordinator.mark("ready", self.team, actor)
                if not self.coordinator.ready_for_attempts():
                    self.syncs += 1
                    require(self.syncs <= 3, "CROSS_TEAM_SYNC_BOUND")
                    return [
                        self.call(
                            actor,
                            "sync",
                            operation,
                            code='await new Promise(r=>setTimeout(r,2000)); text({probe:"bounded_peer_start_wait"});',
                        )
                    ]
                self.phases[actor] += 1
                return [
                    self.call(
                        actor,
                        "start",
                        operation,
                        name="send_message",
                        args={"target": CHILD, "message": self.marker("start")},
                    )
                ]
            if phase == 2:
                self.phases[actor] += 1
                return self.attacks(actor, operation)
            if phase == 3:
                self.require_attempt_outputs(actor)
                self.coordinator.mark("attempts_observed", self.team, actor)
                if not self.received(CHILD, ROOT, self.marker("attempts_done")):
                    return [self.wait(actor, operation)]
                if not self.coordinator.all_attempts_observed():
                    self.syncs += 1
                    require(self.syncs <= 3, "CROSS_TEAM_SYNC_BOUND")
                    return [
                        self.call(
                            actor,
                            "sync",
                            operation,
                            code='await new Promise(r=>setTimeout(r,2000)); text({probe:"bounded_peer_attempt_wait"});',
                        )
                    ]
                self.phases[actor] += 1
                return [
                    self.call(
                        actor,
                        "release",
                        operation,
                        name="send_message",
                        args={"target": CHILD, "message": self.marker("release")},
                    )
                ]
            if phase == 4:
                if not self.received(CHILD, ROOT, self.marker("done"), "FINAL_ANSWER"):
                    return [self.wait(actor, operation)]
                message = self.marker("root_done")
            else:
                require(False, "CROSS_TEAM_SEQUENCE")
        else:
            if phase == 0:
                self.phases[actor] += 1
                return [
                    self.call(
                        actor,
                        "ready",
                        operation,
                        name="send_message",
                        args={"target": ROOT, "message": self.marker("ready")},
                    )
                ]
            if phase == 1:
                if not self.received(ROOT, CHILD, self.marker("start")):
                    return [self.wait(actor, operation)]
                self.phases[actor] += 1
                return self.attacks(actor, operation)
            if phase == 2:
                self.require_attempt_outputs(actor)
                self.coordinator.mark("attempts_observed", self.team, actor)
                self.phases[actor] += 1
                return [
                    self.call(
                        actor,
                        "attempts_done",
                        operation,
                        name="send_message",
                        args={"target": ROOT, "message": self.marker("attempts_done")},
                    )
                ]
            require(phase == 3, "CROSS_TEAM_SEQUENCE")
            if not self.received(ROOT, CHILD, self.marker("release")):
                return [self.wait(actor, operation)]
            message = self.marker("done")
        require(self.coordinator.all_attempts_observed(), "CROSS_TEAM_EARLY_FINISH")
        self.finished.add(actor)
        self.phases[actor] += 1
        return [
            {
                "id": "message-" + operation,
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": message, "annotations": []}],
            }
        ]

    def require_attempt_outputs(self, actor):
        rows = {
            key: call
            for key, call in self.calls.items()
            if call["actor"] == actor
            and any(
                call["phase"] == kind + "_" + method
                for kind in ("foreign_root", "foreign_helper", "absent")
                for method in METHODS
            )
        }
        require(
            len(rows) == 9 and all(key in self.outputs for key in rows), "CROSS_TEAM_OUTPUT_MISSING"
        )

    def report(self):
        # Exact denial classification is intentionally audited from native
        # capture; unknown errors or bare absence never become an automatic pass.
        checks = {
            "cross_both_finished": self.finished == set(ACTORS),
            "cross_exact_denials_reviewed": False,
            "cross_all_targets_known_while_jobs_live": self.coordinator.all_attempts_observed(),
            "cross_permitted_local_messages": self.received(CHILD, ROOT, self.marker("ready"))
            and self.received(ROOT, CHILD, self.marker("start"))
            and self.received(CHILD, ROOT, self.marker("attempts_done"))
            and self.received(ROOT, CHILD, self.marker("release"))
            and self.received(CHILD, ROOT, self.marker("done"), "FINAL_ANSWER"),
        }
        foreign = next(t for t in TEAMS if t != self.team)
        checks["cross_private_peer_marker_absent"] = all(
            self.coordinator.canaries[foreign] not in json.dumps(r["body"]) for r in self.requests
        )
        return {
            "schema": "strata/NativeCrossTeamProbe/1",
            "is_example": True,
            "production_qualified": False,
            "team": self.team,
            "checks": checks,
            "calls": self.calls,
            "outputs": self.outputs,
            "messages": sorted(self.messages),
            "targets": self.attempt_targets,
            "waits": self.waits,
            "denial_classification": "requires_independent_exact_native_error_review",
        }
