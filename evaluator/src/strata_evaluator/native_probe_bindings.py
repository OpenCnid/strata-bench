"""Compile complete prepared pair views into private native artifact bindings.

Registration consumes both arms' identities together, but grants no launch,
resource reservation, process access or budget authority.
"""

import json
from pathlib import Path

from mcbench.budgets import Budgets
from mcbench.native_export import MAX_METADATA, OPERATOR
from mcbench.native_probe_binding import POLICY, NativeProbeArtifactBinding, NativeProbeDestination
from mcbench.storage import canonical, digest, extended_path, require

from .probe_pairs import ARMS


class ProbeNativeBindings:
    def __init__(self, views):
        self.views, self.db, self.cas = views, views.db, views.cas
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_probe_binding_sets (namespace TEXT,pair TEXT,"
                       "digest TEXT,PRIMARY KEY(namespace,pair))")
            db.execute("CREATE TABLE IF NOT EXISTS native_probe_bindings (ref TEXT PRIMARY KEY,"
                       "namespace TEXT,pair TEXT,arm TEXT,source_agent TEXT,job TEXT UNIQUE,"
                       "campaign TEXT,agent TEXT,account TEXT UNIQUE,operation TEXT UNIQUE,"
                       "workspace TEXT UNIQUE,profile TEXT UNIQUE,body TEXT,"
                       "UNIQUE(namespace,pair,arm,source_agent),UNIQUE(campaign,agent))")

    def bind(self, principal, pair_id, destinations):
        self.views.pairs._authorize(principal)
        require(self.db.connection.execute("SELECT 1 FROM native_probe_binding_sets WHERE namespace=? AND pair=?",
                (self.views.namespace, pair_id)).fetchone() is None, "NATIVE_PROBE_BINDING_CONSUMED")
        require(isinstance(destinations, dict) and set(destinations) == set(ARMS), "NATIVE_PROBE_ROSTER")
        # Commit the existing view verifier's one-use verification intent before
        # examining the disk. Source/tree failure stays failed, not repairable.
        view_plan = self.views.verify(principal, pair_id)
        pair, _ = self.views._source(pair_id)
        members = pair["common"]["members"]
        require(all(isinstance(value, dict) and set(value) == set(members) for value in destinations.values()),
                "NATIVE_PROBE_ROSTER")
        selected = {arm: {agent: NativeProbeDestination.model_validate(value) for agent, value in group.items()}
                    for arm, group in destinations.items()}
        identities = [d for group in selected.values() for d in group.values()]
        for field in ("job_id", "account", "operation_id"):
            require(len({getattr(d, field) for d in identities}) == len(identities), "NATIVE_PROBE_IDENTITY_REUSED")
        require(all(len({d.campaign_id for d in group.values()}) == 1 for group in selected.values()) and
                len({d.campaign_id for d in identities}) == 2 and
                len({(d.campaign_id, d.agent_id) for d in identities}) == len(identities), "NATIVE_PROBE_ROSTER")
        root = self.db.connection.execute("SELECT target FROM probe_native_views WHERE namespace=? AND pair=?",
                                          (self.views.namespace, pair_id)).fetchone()[0]
        bindings = {}
        for arm in ARMS:
            bindings[arm] = {}
            for source_agent, d in selected[arm].items():
                member, view = members[source_agent], view_plan["views"][arm][source_agent]
                helpers = view["helper_set_requires_explicit_admission"]
                require(d.supply_helper_artifacts is helpers, "NATIVE_PROBE_HELPERS")
                require(member["helper_depth"] <= 2 and (helpers or member["helper_limit"] == 0), "NATIVE_PROBE_HELPERS")
                base = extended_path(Path(root) / view["directory"])
                value = {"schema": "strata/NativeProbeArtifactBinding/1", "policy": POLICY,
                    "is_example": pair["is_example"], "destination": d.model_dump(),
                    "pair_namespace": self.views.namespace, "pair_id": pair_id,
                    "pair_plan_digest": digest(pair), "views_plan_digest": digest(view_plan),
                    "workspace": str(base / "workspace"), "profile_directory": str(base / "profile"),
                    "model": member["requested_model"], "provider": member["provider"],
                    "helper_limit": member["helper_limit"], "helper_depth": member["helper_depth"],
                    "control_arm": pair["projections"][source_agent]["arm"],
                    "public_goal": pair["common"]["public_goal"], "instructions": view_plan["instructions"],
                    "broker_files": view["broker_files"], "catalog": view["catalog"]}
                bindings[arm][source_agent] = NativeProbeArtifactBinding.model_validate(value).model_dump()
        # CAS uses its own durable transactions. Publish inert private content
        # first; only the complete registry transaction below makes it a binding.
        # Interrupted/failed registration leaves no partially admitted roster.
        refs = {arm: {agent: self.cas.put(OPERATOR, "operator", "operator", canonical(body),
                      max_object_bytes=MAX_METADATA) for agent, body in group.items()}
                for arm, group in bindings.items()}
        with self.db.transaction() as db:
            require(db.execute("SELECT 1 FROM native_probe_binding_sets WHERE namespace=? AND pair=?",
                               (self.views.namespace, pair_id)).fetchone() is None, "NATIVE_PROBE_BINDING_CONSUMED")
            for d in identities:
                # Source campaigns, old accounts/operations and native sessions
                # cannot be renamed into disposable identities. Shared aggregate
                # accounts may retain prior costs; each new leaf must be unused.
                chain = Budgets.ancestors(db, d.account)
                leaf = chain[0]
                require(leaf["campaign"] == d.campaign_id and leaf["agent"] == d.agent_id and
                        leaf["category"] == "evaluation" and all(a["category"] in (None, "evaluation") and
                        a["campaign"] in ("*", d.campaign_id) for a in chain[1:]), "NATIVE_PROBE_ACCOUNT")
                require(db.execute("SELECT 1 FROM operations WHERE account=? OR id=?", (d.account, d.operation_id)).fetchone()
                        is None, "NATIVE_PROBE_IDENTITY_REUSED")
                require(db.execute("SELECT 1 FROM accounts WHERE parent=?", (d.account,)).fetchone() is None and
                        db.execute("SELECT 1 FROM ledger WHERE campaign=?", (d.campaign_id,)).fetchone() is None,
                        "NATIVE_PROBE_IDENTITY_REUSED")
                require(db.execute("SELECT 1 FROM campaigns WHERE id=?", (d.campaign_id,)).fetchone() is None and
                        db.execute("SELECT 1 FROM native_jobs WHERE id=? OR campaign=? OR json_extract(plan,'$.account')=? "
                        "OR json_extract(plan,'$.operation_id')=?", (d.job_id, d.campaign_id, d.account, d.operation_id)).fetchone()
                        is None, "NATIVE_PROBE_IDENTITY_REUSED")
                require(db.execute("SELECT 1 FROM native_probe_bindings WHERE job=? OR campaign=? OR account=? OR operation=?",
                        (d.job_id, d.campaign_id, d.account, d.operation_id)).fetchone() is None,
                        "NATIVE_PROBE_IDENTITY_REUSED")
            # Existing native workspaces/profiles must not own or contain either
            # destination. Windows comparison is case insensitive through Path.
            paths = [Path(v[k]) for group in bindings.values() for v in group.values()
                     for k in ("workspace", "profile_directory")]
            prior_paths = [extended_path(Path(p[k])) for row in db.execute("SELECT plan FROM native_jobs")
                           for p in (json.loads(row[0]),) for k in ("workspace", "profile_directory")]
            prior_paths += [Path(row[k]) for row in db.execute("SELECT workspace,profile FROM native_probe_bindings")
                            for k in ("workspace", "profile")]
            require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                        for i, a in enumerate(paths) for b in paths[i+1:] + prior_paths), "NATIVE_PROBE_PATH_REUSED")
            require(self.views._derive(pair_id) == view_plan, "NATIVE_PROBE_SOURCE_CHANGED")
            self.views._check(extended_path(Path(root)), view_plan)
            for arm, group in bindings.items():
                for agent, body in group.items():
                    ref = refs[arm][agent]
                    d = body["destination"]
                    db.execute("INSERT INTO native_probe_bindings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (ref, self.views.namespace, pair_id, arm, agent, d["job_id"], d["campaign_id"], d["agent_id"],
                         d["account"], d["operation_id"], body["workspace"], body["profile_directory"], canonical(body).decode()))
            db.execute("INSERT INTO native_probe_binding_sets VALUES(?,?,?)", (self.views.namespace, pair_id, digest(refs)))
            self.db.event(db, "probe.native_artifacts_bound", {"namespace": self.views.namespace,
                "pair": pair_id, "bindings_digest": digest(refs), "dispatch_authorized": False})
        return refs
