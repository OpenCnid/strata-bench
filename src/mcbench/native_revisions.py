"""Source-bound learned skill bundles captured at a stopped native boundary.

Publication is atomic and private. It creates candidate SkillRevision records,
not a native skill-loader activation or permission to execute bundled scripts.
"""

import json
import re
from contextlib import nullcontext
from typing import Literal

from pydantic import Field, model_validator

from .broker import MAX_TEXT
from .contracts import Id, Ref, Strict
from .native_export import MAX_METADATA, OPERATOR, NativeExports, private_json
from .plugins import CORE_SKILLS
from .records import SkillRevision
from .storage import Principal, canonical, digest, require, safe_relative

POLICY = "native-root-written-skill-bundles/1"
LINEAGE_POLICY = "native-root-written-skill-bundles/2"
MANIFEST = "skills/publish.json"


class Candidate(Strict):
    revision_id: Id
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{0,63}$")
    kind: Literal["procedure", "executable"]
    parent_revision_id: Id | None
    files: dict[str, Ref]
    inputs: dict[str, Ref]
    development_evidence: dict[str, Ref]


class PublicationRequest(Strict):
    schema_: Literal["strata/NativeSkillPublicationRequest/1", "strata/NativeSkillPublicationRequest/2"] = Field(alias="schema")
    policy: Literal["native-root-written-skill-bundles/1", "native-root-written-skill-bundles/2"]
    candidates: list[Candidate] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def versioned_parents(self):
        if self.schema_.endswith("/1"):
            if self.policy != POLICY or any(c.parent_revision_id is not None for c in self.candidates):
                raise ValueError("initial publication requires null parents")
        elif self.policy != LINEAGE_POLICY:
            raise ValueError("publication policy/schema mismatch")
        return self


def parent_for(previous, candidate):
    """A replacement names its own exact active predecessor and a fresh ID."""
    parent = previous.get(candidate.name)
    require(candidate.parent_revision_id == (parent["revision"]["revision_id"] if parent else None),
            "REVISION_CONFLICT")
    require(all(candidate.revision_id != s["revision"]["revision_id"] for s in previous.values()),
            "REVISION_CONFLICT")
    return parent


def _private_put(cas, body):
    return cas.put(OPERATOR, "operator", "operator", canonical(body), max_object_bytes=MAX_METADATA)


class NativeSkillPublications:
    def __init__(self, runtime):
        self.runtime, self.db, self.cas = runtime, runtime.db, runtime.cas
        self.exports = NativeExports(runtime)
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_skill_publications (job TEXT PRIMARY KEY, "
                "export_ref TEXT, ref TEXT)")

    def _source(self, export_ref):
        state = self.exports.load(export_ref)
        db = self.db.connection
        source = private_json(db, self.cas, state.source_ref)
        inventory = private_json(db, self.cas, state.root_artifacts)
        files = {f["path"]: f["ref"] for f in inventory["files"]}
        principal = Principal(inventory["namespace"], "executor")
        require(MANIFEST in files, "NATIVE_REVISION_REQUEST_REQUIRED")
        request = PublicationRequest.model_validate_json(self.cas.read(principal, principal.namespace,
            files[MANIFEST], max_bytes=MAX_TEXT))
        require(len({c.name for c in request.candidates}) == len(request.candidates) and
            len({c.revision_id for c in request.candidates}) == len(request.candidates), "REVISION_CONFLICT")
        # Evaluation and unclassified accounts cannot import revisions into a
        # campaign. Caller-supplied origin labels are never accepted.
        require(source["account_identities"][0]["category"] in {"training", "development"}, "PROBE_IMPORT_FORBIDDEN")
        calls = {c["cursor"]: c for c in source["broker_calls"]}
        writes = {}
        for write in source.get("artifact_writes", []):
            if write["thread"] != inventory["thread_id"]:
                continue
            call = calls.get(write["event"])
            require(call is not None and write["namespace"] == principal.namespace and
                    write["runtime"] == state.job_id, "NATIVE_REVISION_PROVENANCE")
            event = json.loads(call["body"])
            raw = self.cas.read(principal, principal.namespace, write["ref"], max_bytes=MAX_TEXT)
            require(event["runtime"] == state.job_id and event["thread"] == inventory["thread_id"] and
                event["tool"] == "artifact_write" and event["arguments_digest"] == digest({
                    "path": write["path"], "text": raw.decode("utf-8"), "expected_ref": write["expected_ref"]}),
                "NATIVE_REVISION_PROVENANCE")
            if call["state"] == "RETURNED" and call["result_digest"] == digest({"path": write["path"], "ref": write["ref"]}):
                writes[(write["path"], write["ref"])] = write["event"]
        require((MANIFEST, files[MANIFEST]) in writes, "NATIVE_REVISION_PROVENANCE")
        from .native_checkpoint import check_files
        check_files(self.cas, files, principal.namespace, "executor")
        bundles = []
        initial_names = {p.split("/")[1] for p in CORE_SKILLS} | {"minecraft-keybindings"} | {
            p.split("/")[-2] for p in files if p.startswith("initial/") and p.endswith("/SKILL.md")}
        plan = json.loads(db.execute("SELECT plan FROM native_jobs WHERE id=?", (state.job_id,)).fetchone()[0])
        previous = {}
        if prior := plan.get("skill_activation_ref"):
            from .native import NativeLaunch
            from .native_skill_activation import read_set, require_scope
            active = read_set(db, self.cas, prior)
            require_scope(active, NativeLaunch.model_validate(plan))
            previous = active["skills"]
        for candidate in request.candidates:
            require(candidate.name not in initial_names, "INITIAL_IMMUTABLE")
            require(0 < len(candidate.files) <= 128 and 0 < len(candidate.inputs) <= 128 and
                    0 < len(candidate.development_evidence) <= 128 and "SKILL.md" in candidate.files,
                    "NATIVE_REVISION_FILES")
            prefix = "skills/" + candidate.name + "/"
            parent = parent_for(previous, candidate)
            expected = {p.removeprefix(prefix): r for p, r in files.items() if p.startswith(prefix)}
            require(candidate.files == expected, "NATIVE_REVISION_FILES")
            selected = {prefix + p: r for p, r in candidate.files.items()}
            require(sum(len(self.cas.read(principal, principal.namespace, r, max_bytes=MAX_TEXT))
                        for r in selected.values()) <= MAX_TEXT, "ARTIFACT_QUOTA")
            for path in candidate.files:
                safe_relative(path)
                require(path != "publish.json" and not re.search(r"(^|/)(tests|fixtures)(/|$)", path, re.I),
                        "NATIVE_REVISION_FILES")
            provenance = candidate.inputs | candidate.development_evidence
            require(all(p.startswith(("notes/", "docs/", "supplied/")) and files.get(p) == r
                for group in (candidate.inputs, candidate.development_evidence) for p, r in group.items()),
                "NATIVE_REVISION_PROVENANCE")
            inherited = {prefix + p: r for p, r in parent["files"].items()} if parent else {}
            require(all((p, r) in writes or inherited.get(p) == r for p, r in selected.items()),
                    "NATIVE_REVISION_PROVENANCE")
            generating = {"broker:" + str(writes[(MANIFEST, files[MANIFEST])])}
            generating.update("broker:" + str(writes[(p, r)]) for p, r in selected.items() if (p, r) in writes)
            if any((p, r) not in writes for p, r in selected.items()):
                generating.update(parent["revision"]["generating_call_ids"])
            # Preserve provenance bytes, not operator/source/helper directory names.
            selected |= provenance
            bundles.append({"candidate": candidate.model_dump(), "files": selected,
                "generating_call_ids": sorted(generating)})
        return state, request, principal, bundles

    def publish(self, export_ref):
        state, request, principal, bundles = self._source(export_ref)
        old = self.db.connection.execute("SELECT * FROM native_skill_publications WHERE job=?", (state.job_id,)).fetchone()
        if old:
            require(old["export_ref"] == export_ref, "IDEMPOTENCY_CONFLICT")
            self.load(old["ref"])
            return old["ref"]
        # CAS writes precede one durable publication transaction. A crash may
        # leave unreferenced blobs, never a partially active revision set.
        records = []
        for entry in bundles:
            candidate = entry["candidate"]
            for ref in entry["files"].values():
                old = self.db.connection.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?",
                                                (ref,)).fetchone()
                if old:
                    require(old[0] == "operator", "NATIVE_EXPORT_PRIVATE")
                    self.cas.verify(OPERATOR, "operator", ref)
                    continue
                raw = self.cas.read(principal, principal.namespace, ref, max_bytes=MAX_TEXT)
                require(self.cas.put(OPERATOR, "operator", "operator", raw, media_type="text/plain") == ref,
                        "CORRUPT_EVIDENCE")
            version = request.schema_.rsplit("/", 1)[1]
            bundle = {"schema": "strata/NativeSkillBundle/" + version, "policy": request.policy, "name": candidate["name"],
                "files": candidate["files"], "inputs": candidate["inputs"],
                "development_evidence": candidate["development_evidence"], "executes_scripts": False}
            record = SkillRevision.model_validate({"schema": "mcbench/SkillRevision/1",
                "is_example": self.runtime.simulation, "revision_id": candidate["revision_id"],
                "agent_id": state.agent_id, "parent_revision_id": candidate["parent_revision_id"], "kind": candidate["kind"],
                "content": _private_put(self.cas, bundle), "provenance_refs": sorted(set(
                    (candidate["inputs"] | candidate["development_evidence"]).values())),
                "generating_call_ids": entry["generating_call_ids"], "origin": "campaign", "status": "candidate",
                "activated_at": None})
            records.append(record.model_dump())
        publication = {"schema": "strata/NativeSkillPublication/" + version, "policy": request.policy,
            "is_example": self.runtime.simulation, "source_export": export_ref, "source_digest": state.source_digest,
            "campaign_id": state.campaign_id, "agent_id": state.agent_id, "job_id": state.job_id,
            "request": request.model_dump(), "records": records, "native_activation_verified": False,
            "activates_skills": False, "executes_scripts": False}
        ref = _private_put(self.cas, publication)
        with self.db.transaction() as db:
            self._validate(ref)
            latest = db.execute("SELECT id FROM native_jobs WHERE campaign=? AND agent=? AND role='executor' "
                "ORDER BY rowid DESC LIMIT 1", (state.campaign_id, state.agent_id)).fetchone()
            require(latest[0] == state.job_id, "NATIVE_LATER_STATE")
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='native_checkpoint_states'").fetchone():
                for checkpoint in db.execute("SELECT ref FROM native_checkpoint_states WHERE agent=?", (state.agent_id,)):
                    require(private_json(db, self.cas, checkpoint[0])["source_export"] != export_ref,
                            "NATIVE_REVISION_TOO_LATE")
            old = db.execute("SELECT ref FROM native_skill_publications WHERE job=?", (state.job_id,)).fetchone()
            require(old is None or old[0] == ref, "IDEMPOTENCY_CONFLICT")
            if old is None:
                db.execute("INSERT INTO native_skill_publications VALUES(?,?,?)", (state.job_id, export_ref, ref))
                self.db.event(db, "native.skills_published", {"job": state.job_id, "ref": ref, "activates_skills": False})
        return ref

    def _validate(self, ref):
        body = private_json(self.db.connection, self.cas, ref)
        require(set(body) == {"schema", "policy", "is_example", "source_export", "source_digest", "campaign_id",
            "agent_id", "job_id", "request", "records", "native_activation_verified", "activates_skills", "executes_scripts"}
            and (body["schema"], body["policy"]) in {("strata/NativeSkillPublication/1", POLICY),
                ("strata/NativeSkillPublication/2", LINEAGE_POLICY)} and
            body["is_example"] is self.runtime.simulation and all(body[k] is False for k in
                ("native_activation_verified", "activates_skills", "executes_scripts")), "NATIVE_REVISION_INVALID")
        state, request, _, bundles = self._source(body["source_export"])
        version = request.schema_.rsplit("/", 1)[1]
        require(body["schema"] == "strata/NativeSkillPublication/" + version and body["policy"] == request.policy and
            body["request"] == request.model_dump() and body["source_digest"] == state.source_digest and
            body["campaign_id"] == state.campaign_id and body["agent_id"] == state.agent_id and body["job_id"] == state.job_id
            and len(body["records"]) == len(bundles), "NATIVE_REVISION_INVALID")
        for value, entry in zip(body["records"], bundles, strict=True):
            record = SkillRevision.model_validate(value)
            candidate = entry["candidate"]
            expected_bundle = {"schema": "strata/NativeSkillBundle/" + version, "policy": request.policy, "name": candidate["name"],
                "files": candidate["files"], "inputs": candidate["inputs"],
                "development_evidence": candidate["development_evidence"], "executes_scripts": False}
            require(private_json(self.db.connection, self.cas, record.content) == expected_bundle and
                record.model_dump() == {"schema": "mcbench/SkillRevision/1", "is_example": self.runtime.simulation,
                    "revision_id": candidate["revision_id"], "agent_id": state.agent_id, "parent_revision_id": candidate["parent_revision_id"],
                    "kind": candidate["kind"], "content": record.content,
                    "provenance_refs": sorted(set((candidate["inputs"] | candidate["development_evidence"]).values())),
                    "generating_call_ids": entry["generating_call_ids"], "origin": "campaign", "status": "candidate",
                    "activated_at": None}, "NATIVE_REVISION_INVALID")
            for file_ref in entry["files"].values():
                row = self.db.connection.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?",
                    (file_ref,)).fetchone()
                require(row is not None and row[0] == "operator", "NATIVE_EXPORT_PRIVATE")
                self.cas.verify(OPERATOR, "operator", file_ref)
        return body

    def load(self, ref):
        with (nullcontext(self.db.connection) if self.db.connection.in_transaction else self.db.transaction()) as db:
            body = self._validate(ref)
            row = db.execute("SELECT export_ref,ref FROM native_skill_publications WHERE job=?", (body["job_id"],)).fetchone()
            require(row is not None and tuple(row) == (body["source_export"], ref), "NATIVE_REVISION_UNCOMMITTED")
            return body
