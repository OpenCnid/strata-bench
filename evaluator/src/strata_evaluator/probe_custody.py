"""Held prepared-pair files and atomic pair-wide resources/budget envelopes.

This is preparation custody, not a native/game launch permit. File leases deny
modification of the prepared inputs; they are not gameplay OS isolation.
"""

import json
import time
import uuid
from pathlib import Path

from mcbench.budgets import DIMENSIONS, vector
from mcbench.controller import RESOURCES, reserved_resources
from mcbench.launch_integrity import FileLease, snapshot
from mcbench.native_probe_binding import read_binding, require_binding_account
from mcbench.records import BudgetLedger
from mcbench.storage import canonical, digest, extended_path, require

POLICY = "held-prepared-pair-resources-and-envelopes/1"


class ProbeCustody:
    def __init__(self, bindings, *, clock=time.time, monotonic=time.monotonic):
        self.bindings, self.views = bindings, bindings.views
        self.db, self.cas = bindings.db, bindings.cas
        self.runtime = self.views.pairs.sets.runtime
        self.clock, self.owner = clock, uuid.uuid4().hex
        self.monotonic, self.deadline = monotonic, None
        self.lease = self.pair_id = self.plan = None
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS probe_pair_custody (namespace TEXT,pair TEXT,owner TEXT,"
                       "state TEXT,plan TEXT,expires REAL,PRIMARY KEY(namespace,pair))")
            db.execute("CREATE TABLE IF NOT EXISTS probe_pair_resources (namespace TEXT,pair TEXT,"
                       "worker TEXT,resources TEXT,released INTEGER,PRIMARY KEY(namespace,pair))")

    def _source(self, pair_id):
        pair, target = self.views._source(pair_id)
        view = self.db.connection.execute("SELECT * FROM probe_native_views WHERE namespace=? AND pair=?",
                                          (self.views.namespace, pair_id)).fetchone()
        require(view is not None and view["state"] == "PREPARED", "PROBE_VIEWS_NOT_PREPARED")
        views = self.views._derive(pair_id)
        require(canonical(views).decode() == view["plan"], "PROBE_SOURCE_CHANGED")
        self.views._check(extended_path(Path(view["target"])), views)
        rows = self.db.connection.execute("SELECT * FROM native_probe_bindings WHERE namespace=? AND pair=?",
                                         (self.views.namespace, pair_id)).fetchall()
        expected = {(arm, a) for arm in pair["arm_order"] for a in pair["common"]["members"]}
        require({(r["arm"], r["source_agent"]) for r in rows} == expected, "NATIVE_PROBE_ROSTER")
        bodies = {row["job"]: read_binding(self.db.connection, self.cas, row["ref"]) for row in rows}
        require(all(b.is_example is self.runtime.simulation for b in bodies.values()), "PROFILE_MISMATCH")
        return pair, views, target, extended_path(Path(view["target"])), rows, bodies

    def acquire(self, principal, pair_id, reservations, *, worker, fingerprint, per_arm_resources, lifetime_s=120):
        self.views.pairs._authorize(principal)
        require(self.lease is None and self.pair_id is None, "PROBE_CUSTODY_CONSUMED")
        require(type(lifetime_s) is int and 1 <= lifetime_s <= 300, "PROBE_CUSTODY_DEADLINE")
        require(isinstance(worker, str) and 0 < len(worker) <= 128 and
                isinstance(fingerprint, str) and 0 < len(fingerprint) <= 256, "CAPACITY_UNCERTIFIED")
        require(set(per_arm_resources) == RESOURCES and all(type(v) is int and 0 < v <= 2**52-1
                for v in per_arm_resources.values()), "CAPACITY_RANGE")
        require(self.db.connection.execute("SELECT 1 FROM probe_pair_custody WHERE namespace=? AND pair=?",
                (self.views.namespace, pair_id)).fetchone() is None, "PROBE_CUSTODY_CONSUMED")
        self.views.verify(principal, pair_id)
        pair, views, target, view_target, rows, bodies = self._source(pair_id)
        require(isinstance(reservations, dict) and set(reservations) == set(bodies), "NATIVE_PROBE_ROSTER")
        records = {job: BudgetLedger.model_validate(value) for job, value in reservations.items()}
        limits = pair["common"]["probe_limits"]
        require(limits["spend_microusd"] is not None, "SPENDING_CEILING_REQUIRED")
        for job, b in bodies.items():
            r, d = records[job], b.destination
            require(not r.is_example and r.posting == "reserve" and r.kind == "model" and
                    r.campaign_account == "evaluation" and r.campaign_id == d.campaign_id and
                    r.agent_id == d.agent_id and r.operation_id == d.operation_id and r.epoch == 1 and
                    r.parent_operation_id is None and r.model_identity == b.model and
                    r.usage.spend_microusd is not None and r.usage.spend_microusd > 0 and
                    r.usage.model_calls > 0, "PROBE_RESERVATION_SCOPE")
        # Limits are explicit per-probe (team) ceilings in the registered protocol.
        # Shared thinking latency is a campaign clock, not summed helper wall time.
        for arm in pair["arm_order"]:
            selected = [records[row["job"]] for row in rows if row["arm"] == arm]
            for key in DIMENSIONS:
                limit = limits["practice_world_s"] * 1000 if key == "practice_world_ms" else limits[key]
                require(sum(vector(r)[key] for r in selected) <= limit, "PROBE_ENVELOPE_LIMIT")
            require(all(r.usage.wall_ms <= limits["active_wall_s"]*1000 for r in selected), "PROBE_ENVELOPE_LIMIT")
        for agent in pair["common"]["members"]:
            selected = [records[r["job"]] for r in rows if r["source_agent"] == agent]
            require(len(selected) == 2 and selected[0].usage == selected[1].usage and
                    selected[0].pricing_ref == selected[1].pricing_ref and
                    selected[0].metering == selected[1].metering, "PROBE_UNMATCHED_ENVELOPES")
        n = pair["common"]["n"]
        require(per_arm_resources["bodies"] == n and per_arm_resources["model_slots"] >=
                sum(1 + m["helper_limit"] for m in pair["common"]["members"].values()), "PARTIAL_TEAM_FORBIDDEN")
        # This version reserves both arms concurrently. A sequential peak-capacity
        # scheduler needs its own explicit handover; it cannot halve this hold.
        resources = {key: value*2 for key, value in per_arm_resources.items()}
        inventory = snapshot([], [target, view_target])
        require(resources["disk_bytes"] >= sum(f["bytes"] for f in inventory["files"]), "PROBE_STORAGE_LIMIT")
        plan = {"policy": POLICY, "is_example": pair["is_example"], "pair_digest": digest(pair),
            "views_digest": digest(views), "bindings": {r["job"]: r["ref"] for r in rows},
            "inventory": inventory, "worker": worker, "fingerprint": fingerprint, "resources": resources,
            "reservations": {j: r.model_dump() for j, r in records.items()}, "native_launch_authorized": False}
        self.deadline = self.monotonic()+lifetime_s
        with self.db.transaction() as db:
            require(db.execute("SELECT 1 FROM probe_pair_custody WHERE namespace=? AND pair=?",
                               (self.views.namespace, pair_id)).fetchone() is None, "PROBE_CUSTODY_CONSUMED")
            db.execute("INSERT INTO probe_pair_custody VALUES(?,?,?,'PREPARING',?,?)", (self.views.namespace,
                pair_id, self.owner, canonical(plan).decode(), self.clock()+lifetime_s))
            self.db.event(db, "probe.custody_preparing", {"namespace": self.views.namespace, "pair": pair_id,
                                                        "owner": self.owner, "plan_digest": digest(plan)})
        self.pair_id, self.plan = pair_id, plan
        try:
            self.lease = FileLease(inventory)
            current, current_views, *_ = self._source(pair_id)
            require(current == pair and current_views == views, "PROBE_SOURCE_CHANGED")
            with self.db.transaction() as db:
                self._owned(db, "PREPARING")
                checked, checked_views, *_ = self._source(pair_id)
                require(checked == pair and checked_views == views, "PROBE_SOURCE_CHANGED")
                certificate = self._certificate(db)
                used = reserved_resources(db, worker)
                require(all(used[k]+resources[k] <= json.loads(certificate["capacity"])[k] for k in RESOURCES),
                        "CAPACITY_EXCEEDED")
                for job, r in records.items():
                    require(db.execute("SELECT 1 FROM native_jobs WHERE id=?", (job,)).fetchone() is None,
                            "NATIVE_PROBE_IDENTITY_REUSED")
                    require(db.execute("SELECT 1 FROM operations WHERE id=?", (r.operation_id,)).fetchone() is None,
                            "NATIVE_PROBE_IDENTITY_REUSED")
                    self.runtime.budgets.post_in_transaction(db, bodies[job].destination.account, r, envelope=True)
                db.execute("INSERT INTO probe_pair_resources VALUES(?,?,?,?,0)",
                           (self.views.namespace, pair_id, worker, canonical(resources).decode()))
                db.execute("UPDATE probe_pair_custody SET state='HELD' WHERE namespace=? AND pair=?",
                           (self.views.namespace, pair_id))
                self.db.event(db, "probe.custody_held", {"namespace": self.views.namespace, "pair": pair_id,
                    "owner": self.owner, "plan_digest": digest(plan), "native_launch_authorized": False})
            return self
        except BaseException as error:
            self._fence(reason=getattr(error, "code", type(error).__name__))
            if self.lease:
                self.lease.close()
            raise

    def _owned(self, db, state):
        row = db.execute("SELECT * FROM probe_pair_custody WHERE namespace=? AND pair=?",
                          (self.views.namespace, self.pair_id)).fetchone()
        require(row is not None and row["owner"] == self.owner and row["state"] == state and
                row["plan"] == canonical(self.plan).decode(), "PROBE_CUSTODY_LOST")
        require(row["expires"] > self.clock() and self.deadline is not None and self.monotonic() < self.deadline,
                "PROBE_CUSTODY_EXPIRED")
        return row

    def _certificate(self, db):
        row = db.execute("SELECT * FROM workers WHERE id=?", (self.plan["worker"],)).fetchone()
        require(row is not None and row["fingerprint"] == self.plan["fingerprint"] and
                row["certified_until"] > self.clock() and row["simulation"] == int(self.runtime.simulation),
                "CAPACITY_UNCERTIFIED")
        return row

    def _fence(self, *, reason="owner_closed"):
        # A committed resource/cost hold survives failure, expiry and restart.
        # Only an undispatched live owner can explicitly release preparation resources.
        with self.db.transaction() as db:
            row = db.execute("SELECT state FROM probe_pair_custody WHERE namespace=? AND pair=? AND owner=?",
                             (self.views.namespace, self.pair_id, self.owner)).fetchone()
            if row is not None and row[0] in {"PREPARING", "HELD"}:
                state = "FAILED" if row[0] == "PREPARING" else "FENCED"
                db.execute("UPDATE probe_pair_custody SET state=? WHERE namespace=? AND pair=?",
                           (state, self.views.namespace, self.pair_id))
                self.db.event(db, "probe.custody_fenced", {"namespace": self.views.namespace,
                    "pair": self.pair_id, "state": state, "reason": reason, "holds_retained": True})

    def check(self):
        try:
            require(self.lease is not None and not self.lease.closed, "PROBE_CUSTODY_NOT_HELD")
            self._owned(self.db.connection, "HELD")
            certificate = self._certificate(self.db.connection)
            row = self.db.connection.execute("SELECT * FROM probe_pair_resources WHERE namespace=? AND pair=?",
                                            (self.views.namespace, self.pair_id)).fetchone()
            require(row is not None and not row["released"] and row["worker"] == self.plan["worker"] and
                    row["resources"] == canonical(self.plan["resources"]).decode(), "PROBE_RESOURCE_HOLD_CHANGED")
            used = reserved_resources(self.db.connection, self.plan["worker"])
            require(all(used[k] <= json.loads(certificate["capacity"])[k] for k in RESOURCES), "CAPACITY_EXCEEDED")
            self.lease.recheck()
            pair, views, *_ = self._source(self.pair_id)
            require(digest(pair) == self.plan["pair_digest"] and digest(views) == self.plan["views_digest"],
                    "PROBE_SOURCE_CHANGED")
            for job, value in self.plan["reservations"].items():
                r = BudgetLedger.model_validate(value)
                row = self.db.connection.execute("SELECT * FROM operations WHERE id=?", (r.operation_id,)).fetchone()
                body = read_binding(self.db.connection, self.cas, self.plan["bindings"][job])
                require_binding_account(self.db.connection, body)
                require(row is not None and row["account"] == body.destination.account and row["actual"] is None
                        and row["parent"] is None and row["kind"] == "model" and not row["uncertain"] and
                        row["reserved"] == canonical(vector(r)).decode() and
                        self.db.connection.execute("SELECT 1 FROM budget_envelopes WHERE operation=?", (r.operation_id,)).fetchone()
                        is not None, "PROBE_ENVELOPE_CHANGED")
                original = self.db.connection.execute("SELECT digest,body FROM ledger WHERE campaign=? AND source=?",
                                                     (r.campaign_id, r.source_event_id)).fetchone()
                require(original is not None and original["body"] == canonical(r.model_dump()).decode() and
                        original["digest"] == digest({"account":body.destination.account,"body":r.model_dump()}),
                        "PROBE_ENVELOPE_CHANGED")
                require(not self.runtime.budgets.status(body.destination.account)["uncertain"], "METERING_UNKNOWN")
            return {"policy": POLICY, "state": "HELD", "plan_digest": digest(self.plan), "native_launch_authorized": False}
        except BaseException as error:
            self._fence(reason=getattr(error, "code", type(error).__name__))
            raise

    def close(self):
        """Fence before releasing file handles. Never settle/refund an envelope."""
        try:
            self._fence()
        finally:
            if self.lease:
                self.lease.close()

    def release_undispatched_resources(self):
        """Current preparation-only path; any native intent forbids this release.

        It does not release costs or authorize reuse of this pair/identity.
        Future world/runtime launch custody must use a separate stopped proof.
        """
        self.check()
        with self.db.transaction() as db:
            self._owned(db, "HELD")
            require(all(db.execute("SELECT 1 FROM native_jobs WHERE id=?", (job,)).fetchone() is None
                        for job in self.plan["bindings"]), "PROBE_ALREADY_DISPATCHED")
            db.execute("UPDATE probe_pair_custody SET state='CLOSED' WHERE namespace=? AND pair=?",
                       (self.views.namespace, self.pair_id))
            db.execute("UPDATE probe_pair_resources SET released=1 WHERE namespace=? AND pair=?",
                       (self.views.namespace, self.pair_id))
            self.db.event(db, "probe.preparation_resources_released", {"namespace": self.views.namespace,
                "pair": self.pair_id, "native_intents": 0, "cost_holds_retained": True})
        self.lease.close()
