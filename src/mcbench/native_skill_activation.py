"""Complete-checkpoint learned skill activation and immutable native views.

Native loader conformance and game/backend restore authority are separate from
this private state transition. Helpers receive a named set only when the launch
explicitly supplies that same immutable set; no private provenance is projected.
"""

import hashlib
import json
import os
import re
import tempfile
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path

from .native_export import MAX_METADATA, OPERATOR, private_json
from .native_revisions import NativeSkillPublications
from .records import SkillRevision
from .storage import Principal, canonical, digest, extended_path, reject_links, require, safe_relative

POLICY = "native-checkpoint-learned-overlay/1"
INSTRUCTIONS = """\nLearned skills use the immutable active overlay. For a catalog path under
.agents/skills/<name>/, read its body and supporting text through the artifact
broker at active/<name>/<relative-path>. Initial skills remain unchanged.
Read active/revisions.json for the active names and parent revision identifiers.
Write proposed replacements under skills/<name>/ and publish the complete bundle
with its exact parent revision. Reading script source does not permit execution.
Helpers receive only the explicitly supplied immutable skill set and their own
results; they cannot read or change the executor's notes, drafts or handoff.
"""


def skill_metadata(name, files, cas):
    """Deliberately bounded native YAML surface; no tool/dependency configuration."""
    require("SKILL.md" in files, "NATIVE_SKILL_METADATA")
    text = cas.read(OPERATOR, "operator", files["SKILL.md"]).decode("utf-8")
    normalized = text.replace("\r\n", "\n")
    match = re.match(r"\A---\nname: ([a-z][a-z0-9-]{0,63})\ndescription: ([^\n]{1,512})\n---(?:\n|\Z)", normalized)
    require(match is not None and match[1] == name, "NATIVE_SKILL_METADATA")
    description = match[2]
    # Plain scalar only. Other YAML forms require a versioned parser policy;
    # quoted/multiline/tag/alias scalars are not silently interpreted differently.
    require(not any(c in description for c in ":#[]{}&*!|>'\"%@`\\") and
            description == description.strip(), "NATIVE_SKILL_METADATA")
    for path in files:
        relative = safe_relative(path)
        require(path == "SKILL.md" or (relative.parts[0] in {"references", "scripts", "assets"}
            and len(relative.parts) > 1 and relative.name != "SKILL.md"), "NATIVE_SKILL_METADATA")
    return {"name": name, "description": description}


def revision_index(skills):
    """Only public lineage handles; never private provenance or checkpoint IDs."""
    return {"schema": "strata/ActiveSkillIndex/1", "skills": {
        name: value["revision"]["revision_id"] for name, value in skills.items()}}


def active_files(body):
    index = "cas:sha256:" + digest(revision_index(body["skills"]))
    return {"active/" + name + "/" + path: ref for name, value in body["skills"].items()
            for path, ref in value["files"].items()} | {"active/revisions.json": index}


def read_set(db, cas, ref):
    body = private_json(db, cas, ref)
    require(body.get("schema") == "strata/NativeSkillSet/1" and body.get("policy") == POLICY,
            "NATIVE_SKILL_SET")
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='native_skill_sets'").fetchone(),
            "NATIVE_SKILL_SET_UNCOMMITTED")
    row = db.execute("SELECT ref FROM native_skill_sets WHERE checkpoint_ref=?", (body["checkpoint_ref"],)).fetchone()
    require(row is not None and row[0] == ref, "NATIVE_SKILL_SET_UNCOMMITTED")
    return body


def require_scope(body, plan):
    require(plan.role == "executor" and plan.campaign_id == body["campaign_id"] and
        plan.agent_id == body["agent_id"] and plan.model == body["model_identity"] and plan.epoch > body["source_epoch"] and
        (plan.helper_skill_activation_ref is None or plan.helper_skill_activation_ref == plan.skill_activation_ref),
        "NATIVE_SKILL_SCOPE")


def require_catalog(db, cas, plan, request, role):
    """Check native-generated developer catalogs before any child reservation.

    The pinned runtime shares the workspace catalog with clean-context helpers.
    Reject their first request unless that whole immutable set was explicitly
    supplied. Prompt instructions alone do not authorize inherited knowledge.
    """
    body = read_set(db, cas, plan.skill_activation_ref)
    require_scope(body, plan)
    require(role == "executor" or plan.helper_skill_activation_ref == plan.skill_activation_ref,
            "NATIVE_HELPER_SKILLS_NOT_SUPPLIED")
    blocks = []
    for item in request.get("input", []):
        if item.get("role") == "developer" and item.get("type") == "message":
            for part in item.get("content", []):
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    blocks.extend(re.findall(r"<skills_instructions>(.*?)</skills_instructions>",
                                             part["text"], re.S))
    require(len(blocks) == 1, "NATIVE_SKILL_CATALOG")
    text = blocks[0].replace("\\", "/")
    roots = dict(re.findall(r"^- `(r\d+)` = `([^`]+)`$", text, re.M))
    actual = {}
    for name, description, location in re.findall(r"^- ([^:\n]+): (.*?) \(file: ([^)\n]+)\)$", text, re.M):
        alias, _, tail = location.partition("/")
        path = roots[alias] + "/" + tail if alias in roots else location
        if "/.agents/skills/" in path:
            require(name not in actual, "NATIVE_SKILL_CATALOG")
            actual[name] = (description, path)
    root = Path(plan.workspace).as_posix().rstrip("/")
    expected = {name: (value["metadata"]["description"], root + "/.agents/skills/" + name + "/SKILL.md")
                for name, value in body["skills"].items()}
    require(actual == expected, "NATIVE_SKILL_CATALOG")


class NativeSkillSets:
    def __init__(self, runtime):
        self.runtime, self.db, self.cas = runtime, runtime.db, runtime.cas
        self.publications = NativeSkillPublications(runtime)
        from .checkpoints import Checkpoints
        from .native_checkpoint import NativeCheckpointStates
        self.components = NativeCheckpointStates(runtime)
        self.checkpoints = Checkpoints(self.db, self.cas)
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_skill_sets (checkpoint_ref TEXT PRIMARY KEY, ref TEXT UNIQUE)")
            db.execute("CREATE TABLE IF NOT EXISTS native_skill_views (path TEXT PRIMARY KEY, set_ref TEXT, files_digest TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS native_skill_projections "
                       "(runtime TEXT, thread TEXT, set_ref TEXT, PRIMARY KEY(runtime,thread))")

    def _source(self, checkpoint_ref):
        state, config = self.components.load(checkpoint_ref)
        # An isolated runtime component is not a complete game/agent checkpoint.
        manifest, _ = self.checkpoints.load(state.checkpoint_id, _native=self.components)
        require(any(a.agent_id == state.agent_id and a.runtime_state == checkpoint_ref for a in manifest.agents),
                "NATIVE_COMPLETE_CHECKPOINT_REQUIRED")
        retained = private_json(self.db.connection, self.cas, state.skills)
        workspace = private_json(self.db.connection, self.cas, state.workspace)["files"] | retained["files"]
        source = self.publications.exports.load(state.source_export)
        plan = json.loads(self.db.connection.execute("SELECT plan FROM native_jobs WHERE id=?", (source.job_id,)).fetchone()[0])
        prior = plan.get("skill_activation_ref")
        previous = read_set(self.db.connection, self.cas, prior) if prior else None
        require(not previous or (previous["campaign_id"] == state.campaign_id and
            previous["agent_id"] == state.agent_id and previous["system_digest"] == state.system_digest),
            "NATIVE_SKILL_SCOPE")
        carried = previous["skills"] if previous else {}
        # Retention already decided the surviving surface. Frozen episode arms
        # have no active files; recovery/full keep the exact admitted old set.
        if not any(p.startswith("active/") for p in workspace):
            carried = {}
        else:
            require(previous is not None and {p: r for p, r in workspace.items() if p.startswith("active/")}
                    == active_files(previous), "NATIVE_SKILL_SCOPE")
        publication = self.publications.load(retained["publication_ref"]) if retained.get("publication_ref") else None
        policy = private_json(self.db.connection, self.cas, state.retention_policy)
        if policy["arm"] == "frozen-skills":
            # Recovery preserves candidate evidence, not permission to activate
            # it. This arm forbids learned procedures within an episode too.
            require(not carried, "NATIVE_FROZEN_SKILLS_ACTIVE")
            publication = None
        return state, workspace, carried, publication, prior

    def create(self, checkpoint_ref):
        old = self.db.connection.execute("SELECT ref FROM native_skill_sets WHERE checkpoint_ref=?", (checkpoint_ref,)).fetchone()
        if old:
            self.load(old[0])
            return old[0]
        state, workspace, carried, publication, prior = self._source(checkpoint_ref)
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        skills = dict(carried)
        if publication:
            for value in publication["records"]:
                candidate = SkillRevision.model_validate(value)
                bundle = private_json(self.db.connection, self.cas, candidate.content)
                name = bundle["name"]
                parent = skills.get(name)
                require(candidate.parent_revision_id == (parent["revision"]["revision_id"] if parent else None),
                        "REVISION_CONFLICT")
                require(not parent or parent["revision"]["revision_id"] != candidate.revision_id, "REVISION_CONFLICT")
                metadata = skill_metadata(name, bundle["files"], self.cas)
                revision = SkillRevision.model_validate(candidate.model_dump() | {"status": "active", "activated_at": timestamp})
                skills[name] = {"metadata": metadata, "revision": revision.model_dump(), "files": bundle["files"]}
        self.cas.put(OPERATOR, "operator", "operator", canonical(revision_index(skills)))
        body = {"schema": "strata/NativeSkillSet/1", "policy": POLICY, "is_example": self.runtime.simulation,
            "checkpoint_ref": checkpoint_ref, "source_epoch": state.source_epoch, "campaign_id": state.campaign_id,
            "agent_id": state.agent_id, "system_digest": state.system_digest, "model_identity": state.model_identity,
            "parent_set": prior,
            "skills": skills, "activated_at": timestamp, "native_loader_qualified": False,
            "dispatch_authorized": False, "executes_scripts": False,
            "workspace": {p: r for p, r in workspace.items() if not p.startswith("active/")}}
        ref = self.cas.put(OPERATOR, "operator", "operator", canonical(body), max_object_bytes=MAX_METADATA)
        with self.db.transaction() as db:
            self._validate(ref)
            old = db.execute("SELECT ref FROM native_skill_sets WHERE checkpoint_ref=?", (checkpoint_ref,)).fetchone()
            if old:
                self.load(old[0])
                return old[0]
            db.execute("INSERT INTO native_skill_sets VALUES(?,?)", (checkpoint_ref, ref))
            self.db.event(db, "native.skills_activated", {"checkpoint_ref": checkpoint_ref, "ref": ref,
                "native_loader_qualified": False, "dispatch_authorized": False})
        return ref

    def _validate(self, ref):
        body = private_json(self.db.connection, self.cas, ref)
        require(set(body) == {"schema", "policy", "is_example", "checkpoint_ref", "source_epoch", "campaign_id",
            "agent_id", "system_digest", "parent_set", "skills", "activated_at", "native_loader_qualified",
            "dispatch_authorized", "executes_scripts", "workspace", "model_identity"} and body["schema"] == "strata/NativeSkillSet/1"
            and body["policy"] == POLICY and body["is_example"] is self.runtime.simulation and
            all(body[k] is False for k in ("native_loader_qualified", "dispatch_authorized", "executes_scripts")),
            "NATIVE_SKILL_SET")
        require(isinstance(body["activated_at"], str) and re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", body["activated_at"]), "NATIVE_SKILL_SET")
        try:
            datetime.fromisoformat(body["activated_at"])
        except ValueError:
            require(False, "NATIVE_SKILL_SET")
        state, workspace, carried, publication, prior = self._source(body["checkpoint_ref"])
        require(body["source_epoch"] == state.source_epoch and body["campaign_id"] == state.campaign_id and
            body["agent_id"] == state.agent_id and body["system_digest"] == state.system_digest and body["parent_set"] == prior
            and body["model_identity"] == state.model_identity
            and body["workspace"] == {p: r for p, r in workspace.items() if not p.startswith("active/")}, "NATIVE_SKILL_SCOPE")
        expected = dict(carried)
        for candidate in publication["records"] if publication else []:
            bundle = private_json(self.db.connection, self.cas, candidate["content"])
            name = bundle["name"]
            parent = expected.get(name)
            require(candidate["parent_revision_id"] == (parent["revision"]["revision_id"] if parent else None)
                and (not parent or parent["revision"]["revision_id"] != candidate["revision_id"]), "REVISION_CONFLICT")
            revision = SkillRevision.model_validate(candidate | {"status": "active", "activated_at": body["activated_at"]})
            expected[name] = {"metadata": skill_metadata(name, bundle["files"], self.cas),
                "revision": revision.model_dump(), "files": bundle["files"]}
        require(body["skills"] == expected, "NATIVE_SKILL_SET")
        from .native_checkpoint import check_files
        check_files(self.cas, body["workspace"] | active_files(body))
        return body

    def load(self, ref):
        with (nullcontext(self.db.connection) if self.db.connection.in_transaction else self.db.transaction()) as db:
            body = self._validate(ref)
            row = db.execute("SELECT ref FROM native_skill_sets WHERE checkpoint_ref=?", (body["checkpoint_ref"],)).fetchone()
            require(row is not None and row[0] == ref, "NATIVE_SKILL_SET_UNCOMMITTED")
            return body

    @staticmethod
    def view_files(body):
        return body["workspace"] | active_files(body) | {".agents/skills/" + name + "/" + path: ref
            for name, value in body["skills"].items() for path, ref in value["files"].items()}

    def materialize(self, ref, target):
        body = self.load(ref)
        files = self.view_files(body)
        target = extended_path(Path(target))
        reject_links(target)
        require(not target.exists(), "TARGET_EXISTS")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent, prefix=".skill-view-") as temporary:
            staged = Path(temporary) / "workspace"
            staged.mkdir()
            for path, value in files.items():
                dest = staged.joinpath(*safe_relative(path).parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                self.cas.copy_to(OPERATOR, "operator", value, dest)
            self._verify_files(staged, files)
            with self.db.transaction() as db:
                self.load(ref)
                require(db.execute("SELECT 1 FROM native_skill_views WHERE path=?", (str(target),)).fetchone() is None,
                        "TARGET_EXISTS")
                # A crash after rename retains an occupied target, never implicit
                # launch authority or automatic replacement on retry.
                os.rename(staged, target)
                db.execute("INSERT INTO native_skill_views VALUES(?,?,?)", (str(target), ref, digest(files)))
        return {"path": str(target), "files_digest": digest(files), "skill_set_ref": ref,
                "dispatch_authorized": False, "native_loader_qualified": False}

    @staticmethod
    def _verify_files(root, files):
        reject_links(root)
        actual = {}
        for path in root.rglob("*"):
            reject_links(path)
            if path.is_file():
                with path.open("rb") as stream:
                    actual[path.relative_to(root).as_posix()] = "cas:sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()
        require(actual == files, "NATIVE_SKILL_VIEW_CHANGED")

    def validate_launch(self, plan):
        body = self.load(plan.skill_activation_ref)
        require_scope(body, plan)
        campaign = self.db.connection.execute("SELECT epoch,config FROM campaigns WHERE id=?", (plan.campaign_id,)).fetchone()
        require(campaign is not None and plan.epoch >= campaign["epoch"] and
            json.loads(campaign["config"])["system_digest"] == body["system_digest"], "NATIVE_SKILL_SCOPE")
        target = extended_path(Path(plan.workspace))
        row = self.db.connection.execute("SELECT * FROM native_skill_views WHERE path=?", (str(target),)).fetchone()
        files = self.view_files(body)
        require(row is not None and row["set_ref"] == plan.skill_activation_ref and row["files_digest"] == digest(files),
                "NATIVE_SKILL_VIEW_UNCOMMITTED")
        self._verify_files(target, files)
        from .launch_integrity import read_manifest, safe
        require(plan.bootstrap_manifest is not None and plan.bootstrap_digest is not None, "SKILL_BOOTSTRAP_REQUIRED")
        manifest = read_manifest(plan.bootstrap_manifest, plan.bootstrap_digest)
        held = {str(safe(e["path"])): e["sha256"] for e in manifest["inventory"]["files"]}
        require(any(safe(t["path"]) == safe(target) for t in manifest["inventory"]["trees"]) and
            all(held.get(str(safe(target / p))) == r[11:] for p, r in files.items()), "SKILL_BODY_UNPINNED")
        return body

    def project(self, plan, grant, broker):
        body = self.validate_launch(plan)
        require(grant.role == "executor" or plan.helper_skill_activation_ref == plan.skill_activation_ref,
                "NATIVE_HELPER_SKILLS_NOT_SUPPLIED")
        require(grant.runtime_id == plan.job_id and grant.profile_digest == plan.profile_digest() and
            grant.campaign_id == plan.campaign_id and grant.agent_id == plan.agent_id and grant.epoch == plan.epoch,
            "NATIVE_SKILL_SCOPE")
        # Fresh helpers receive only the explicitly selected active set and their
        # initial/supplied artifacts, never root notes, drafts or provenance.
        files = active_files(body) | (body["workspace"] if grant.role == "executor" else {})
        for path, ref in files.items():
            broker._path(path)
            raw = self.cas.read(OPERATOR, "operator", ref)
            raw.decode("utf-8")
            require(self.cas.put(Principal(grant.namespace, "executor"), grant.namespace, "agent", raw,
                media_type="text/plain") == ref, "CORRUPT_EVIDENCE")
        with self.db.transaction() as db:
            require(broker._grant(db, grant.thread_id)[0] == grant, "NATIVE_SKILL_SCOPE")
            old = db.execute("SELECT set_ref FROM native_skill_projections WHERE runtime=? AND thread=?",
                             (plan.job_id, grant.thread_id)).fetchone()
            if old:
                require(old[0] == plan.skill_activation_ref, "NATIVE_SKILL_SCOPE")
                return  # Do not overwrite later mutable writes on another call.
            existing_paths = {r[0] for r in db.execute("SELECT path FROM broker_files WHERE namespace=?", (grant.namespace,))}
            require(len(existing_paths | set(files)) <= 1024, "ARTIFACT_QUOTA")
            for path, ref in files.items():
                immutable = path.split("/")[0] in {"initial", "docs", "supplied", "active"}
                prior = db.execute("SELECT ref,immutable FROM broker_files WHERE namespace=? AND path=?",
                                   (grant.namespace, path)).fetchone()
                require(prior is None or tuple(prior) == (ref, int(immutable)), "NATIVE_SKILL_SCOPE")
                db.execute("INSERT OR IGNORE INTO broker_files VALUES(?,?,?,?)",
                           (grant.namespace, path, ref, int(immutable)))
            db.execute("INSERT INTO native_skill_projections VALUES(?,?,?)",
                       (plan.job_id, grant.thread_id, plan.skill_activation_ref))
