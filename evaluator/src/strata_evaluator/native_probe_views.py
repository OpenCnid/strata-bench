"""One-use native artifact/catalog views derived from a complete prepared pair.

Operator/evaluator only. These are bootstrap inputs, not launch permits. Actual
native catalog loading, scoped broker projection and live isolation remain due.
"""

import json
import os
import shutil
from pathlib import Path

from mcbench.checkpoints import Checkpoints
from mcbench.native_export import MAX_METADATA, OPERATOR
from mcbench.native_skill_activation import skill_metadata
from mcbench.storage import canonical, digest, extended_path, reject_links, require, safe_relative

from .probe_pairs import ARMS, ProbePairRequest

POLICY = "pair-derived-native-artifact-views/1"
INSTRUCTIONS = """Read catalog skills under .agents/skills/<name>/ through the artifact
broker at active/<name>/<relative-path>. Read active/revisions.json for the
available revision identifiers. Initial skills remain unchanged. Record local
observations in notes/ and revised procedures or scripts in skills/. Reading
script text does not grant additional tools or filesystem access. Helpers receive
only the explicitly supplied immutable artifacts and their own results, never
the executor's notes, drafts or handoff.
"""


class ProbeNativeViews:
    def __init__(self, pairs):
        self.pairs, self.db, self.cas = pairs, pairs.db, pairs.cas
        self.namespace = pairs.namespace
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS probe_native_views (namespace TEXT, pair TEXT, "
                "target TEXT UNIQUE, plan TEXT, state TEXT, PRIMARY KEY(namespace,pair))")

    def _source(self, pair_id):
        row = self.db.connection.execute("SELECT * FROM probe_pair_staging WHERE namespace=? AND id=?",
                                         (self.namespace, pair_id)).fetchone()
        require(row is not None and row["state"] == "PREPARED", "PROBE_PAIR_NOT_PREPARED")
        request = ProbePairRequest.model_validate_json(row["request"])
        pair = self.pairs._derive(OPERATOR, request)
        require(canonical(pair).decode() == row["plan"], "PROBE_SOURCE_CHANGED")
        self.pairs._check(extended_path(Path(row["target"])), pair)
        return pair, extended_path(Path(row["target"]))

    def _derive(self, pair_id):
        pair, pair_target = self._source(pair_id)
        views = {}
        for arm in ARMS:
            views[arm] = {}
            for agent, member in pair["common"]["members"].items():
                p = pair["projections"][agent]
                root = dict(p["initial_files"] if arm == "initial" else p["experienced_files"])
                skills = {} if arm == "initial" else p["experienced_skills"]
                catalog = {}
                active = {}
                for name, value in skills.items():
                    metadata = skill_metadata(name, value["files"], self.cas)
                    require(metadata == {"name": name, "description": value["description"]}, "PROBE_SKILL_METADATA")
                    catalog[name] = metadata | {"revision_id": value["revision_id"], "files": value["files"]}
                    active.update({"active/" + name + "/" + path: ref for path, ref in value["files"].items()})
                index = {"schema": "strata/ActiveSkillIndex/1",
                         "skills": {name: value["revision_id"] for name, value in skills.items()}}
                # Only this generated public index is added; private source,
                # revision provenance, pair identity and account refs stay out.
                active["active/revisions.json"] = "cas:sha256:" + digest(index)
                helpers = member["self_play"] and member["helper_limit"] > 0
                helper = {path: ref for path, ref in p["initial_files"].items()
                          if path.startswith(("initial/", "docs/", "supplied/"))} | active
                views[arm][agent] = {"directory": pair["arm_directories"][arm] + "/" + member["directory"],
                    "broker_files": {"executor": root | active} | ({"helper": helper} if helpers else {}),
                    "catalog": catalog, "index": index,
                    "helper_set_requires_explicit_admission": helpers}
        return {"schema": "strata/ProbeNativeViews/1", "policy": POLICY, "is_example": pair["is_example"],
            "pair_id": pair_id, "pair_namespace": self.namespace, "pair_plan_digest": digest(pair),
            "pair_target": str(pair_target), "views": views, "instructions": INSTRUCTIONS,
            "dispatch_authorized": False, "campaign_feedback_allowed": False,
            "native_loader_verified": False, "broker_projection_verified": False}

    def _inventory(self, plan):
        files, generated, directories = {}, {"views.json": canonical(plan)}, set()
        for arm in ARMS:
            for view in plan["views"][arm].values():
                root = view["directory"]
                directories.update({root + "/workspace", root + "/profile"})
                for path, ref in view["broker_files"]["executor"].items():
                    if path == "active/revisions.json":
                        generated[root + "/workspace/" + path] = canonical(view["index"])
                    else:
                        files[root + "/workspace/" + path] = ("operator", ref)
                for name, value in view["catalog"].items():
                    files.update({root + "/workspace/.agents/skills/" + name + "/" + path: ("operator", ref)
                                  for path, ref in value["files"].items()})
        for path in files.keys() | generated.keys() | directories:
            directories.update(str(p) for p in safe_relative(path).parents if str(p) != ".")
        return files, generated, directories

    def _check(self, target, plan):
        refs = {ref for arm in plan["views"].values() for view in arm.values()
                for files in view["broker_files"].values() for ref in files.values()}
        for ref in refs:
            row = self.db.connection.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?",
                                             (ref,)).fetchone()
            require(row is not None and row[0] == "operator", "PROBE_ARTIFACT_SOURCE")
            self.cas.verify(OPERATOR, "operator", ref)
        files, generated, directories = self._inventory(plan)
        mapped = files | {p: (self.namespace, "cas:sha256:" + digest(json.loads(raw))) for p, raw in generated.items()}
        checker = object.__new__(Checkpoints)
        checker.database, checker.cas = self.db, self.cas
        checker._verify_staged_tree(target, mapped, directories)

    def _fail(self, pair_id):
        with self.db.transaction() as db:
            changed = db.execute("UPDATE probe_native_views SET state='FAILED' WHERE namespace=? AND pair=? "
                "AND state IN ('PREPARING','VERIFYING')", (self.namespace, pair_id))
            if changed.rowcount:
                self.db.event(db, "probe.native_views_failed", {"namespace": self.namespace, "pair": pair_id})

    def prepare(self, principal, pair_id, target, *, max_bytes):
        self.pairs._authorize(principal)
        require(type(max_bytes) is int and 0 < max_bytes <= 2**53-1, "PROBE_STORAGE_LIMIT")
        plan = self._derive(pair_id)
        target = extended_path(Path(target))
        reject_links(target)
        require(not target.exists() and not target.is_relative_to(extended_path(self.cas.root)) and
                not target.is_relative_to(Path(plan["pair_target"])), "TARGET_EXISTS")
        files, generated, directories = self._inventory(plan)
        total = sum(self.db.connection.execute("SELECT bytes FROM objects WHERE namespace=? AND ref=?", value).fetchone()[0]
                    for value in files.values()) + sum(len(raw) for raw in generated.values())
        require(total <= max_bytes, "PROBE_STORAGE_LIMIT")
        target.parent.mkdir(parents=True, exist_ok=True)
        require(shutil.disk_usage(target.parent).free >= total, "PROBE_STORAGE_LIMIT")
        with self.db.transaction() as db:
            require(db.execute("SELECT 1 FROM probe_native_views WHERE namespace=? AND pair=? OR target=?",
                               (self.namespace, pair_id, str(target))).fetchone() is None, "PROBE_VIEWS_CONSUMED")
            db.execute("INSERT INTO probe_native_views VALUES(?,?,?,?,'PREPARING')",
                       (self.namespace, pair_id, str(target), canonical(plan).decode()))
            self.db.event(db, "probe.native_views_preparing", {"namespace": self.namespace, "pair": pair_id,
                "plan_digest": digest(plan), "materialized_bytes": total})
        try:
            target.mkdir()
            for path in sorted(directories):
                target.joinpath(*safe_relative(path).parts).mkdir(parents=True, exist_ok=True)
            for path, (namespace, ref) in files.items():
                self.cas.copy_to(OPERATOR, namespace, ref, target.joinpath(*safe_relative(path).parts))
            for path, raw in generated.items():
                self.cas.put(OPERATOR, self.namespace, "evaluator", raw, max_object_bytes=MAX_METADATA)
                if path.endswith("/workspace/active/revisions.json"):
                    # Every broker_files ref resolves in the operator artifact
                    # store. Copy only this public index, never views.json.
                    self.cas.put(OPERATOR, "operator", "operator", raw, max_object_bytes=MAX_METADATA)
                with target.joinpath(*safe_relative(path).parts).open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
            with self.db.transaction() as db:
                require(self._derive(pair_id) == plan, "PROBE_SOURCE_CHANGED")
                self._check(target, plan)
                db.execute("UPDATE probe_native_views SET state='PREPARED' WHERE namespace=? AND pair=?",
                           (self.namespace, pair_id))
                self.db.event(db, "probe.native_views_prepared", {"namespace": self.namespace, "pair": pair_id,
                    "plan_digest": digest(plan), "dispatch_authorized": False})
        except BaseException:
            self._fail(pair_id)
            raise
        return plan

    def verify(self, principal, pair_id):
        self.pairs._authorize(principal)
        with self.db.transaction() as db:
            row = db.execute("SELECT * FROM probe_native_views WHERE namespace=? AND pair=?",
                             (self.namespace, pair_id)).fetchone()
            require(row is not None and row["state"] == "PREPARED", "PROBE_VIEWS_NOT_PREPARED")
            db.execute("UPDATE probe_native_views SET state='VERIFYING' WHERE namespace=? AND pair=?",
                       (self.namespace, pair_id))
            self.db.event(db, "probe.native_views_verifying", {"namespace": self.namespace, "pair": pair_id})
        try:
            with self.db.transaction() as db:
                plan = self._derive(pair_id)
                require(canonical(plan).decode() == row["plan"], "PROBE_SOURCE_CHANGED")
                self._check(extended_path(Path(row["target"])), plan)
                db.execute("UPDATE probe_native_views SET state='PREPARED' WHERE namespace=? AND pair=?",
                           (self.namespace, pair_id))
                self.db.event(db, "probe.native_views_verified", {"namespace": self.namespace, "pair": pair_id,
                    "plan_digest": digest(plan), "dispatch_authorized": False})
        except BaseException:
            self._fail(pair_id)
            raise
        return plan
