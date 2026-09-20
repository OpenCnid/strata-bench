"""Exact pinned Dovetail skill bodies exposed through immutable broker files.

This enables native skill reads without granting shell or filesystem access.
Script execution, learned-skill activation and supporting-file projection are
separate capabilities; this projection does not claim to implement them.
"""

import hashlib
import json
from pathlib import Path

from .broker import MAX_TEXT, NativeBroker
from .plugins import CORE_SKILLS, EXPLICIT_SKILLS, inspect_plugin_tree, _extended_path
from .runtime import DOVETAIL_COMMIT
from .storage import Principal, canonical, require

POLICY = "dovetail-eight-immutable-bodies/1"
OPERATOR = Principal("operator", "operator")
INSTRUCTIONS = (
    "Use the installed native Dovetail skill catalog and its invocation rules. "
    "Read an activated Dovetail skill body through strata_broker.artifact_read at "
    "initial/dovetail/skills/<skill-name>/SKILL.md. These are immutable initial skills. "
    "Use strata_broker.artifact_list to inspect your permitted artifacts. "
    "The current capability profile exposes skill bodies, scoped notes/helper results, "
    "and executor game actions. Skill supporting files, arbitrary file reads, shell/script "
    "execution and learned-skill activation are unavailable in this profile. "
    "If a skill requires an unavailable capability, report it explicitly."
)


def prepare_skill_corpus(cas, installed_root):
    """Operator-only source inspection; no gameplay-controlled filesystem path."""
    root = Path(installed_root)
    inventory = inspect_plugin_tree(root)
    pinned = {e["path"]: e for e in inventory["files"]}
    bodies = []
    for path in CORE_SKILLS:
        raw = _extended_path(root / path).read_bytes()
        require(len(raw) <= MAX_TEXT and hashlib.sha256(raw).hexdigest() == pinned[path]["sha256"],
                "SKILL_BODY_CHANGED")
        text = raw.decode("utf-8", errors="strict")
        bodies.append({"path": "initial/dovetail/" + path, "sha256": pinned[path]["sha256"],
                       "text": text, "explicit_only": path in EXPLICIT_SKILLS})
    body = {"schema": "strata/NativeSkillCorpus/1", "policy": POLICY,
            "source_commit": DOVETAIL_COMMIT, "installed_tree_digest": inventory["installed_tree_digest"],
            "installed_root": str(root.absolute()),
            "bodies": bodies}
    raw = canonical(body)
    require(len(raw) <= 1024 * 1024, "SKILL_CORPUS_SIZE")
    return cas.put(OPERATOR, "operator", "operator", raw)


def read_skill_corpus(cas, ref):
    row = cas.database.connection.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?",
                                    (ref,)).fetchone()
    require(row is not None and row[0] == "operator", "SKILL_CORPUS_PRIVATE")
    body = json.loads(cas.read(OPERATOR, "operator", ref, max_bytes=1024 * 1024))
    require(isinstance(body, dict) and body.get("schema") == "strata/NativeSkillCorpus/1" and
            body.get("policy") == POLICY and body.get("source_commit") == DOVETAIL_COMMIT and
            isinstance(body.get("bodies"), list) and len(body["bodies"]) == len(CORE_SKILLS), "SKILL_CORPUS")
    for path, item in zip(CORE_SKILLS, body["bodies"], strict=True):
        require(isinstance(item, dict) and set(item) == {"path", "sha256", "text", "explicit_only"} and
                item["path"] == "initial/dovetail/" + path and isinstance(item["text"], str) and
                len(item["text"].encode("utf-8")) <= MAX_TEXT and
                hashlib.sha256(item["text"].encode("utf-8")).hexdigest() == item["sha256"] and
                item["explicit_only"] is (path in EXPLICIT_SKILLS), "SKILL_CORPUS")
    return body


def validate_skill_bootstrap(cas, ref, plan):
    from .launch_integrity import read_manifest, safe
    body = read_skill_corpus(cas, ref)
    require(plan.bootstrap_manifest is not None and plan.bootstrap_digest is not None,
            "SKILL_BOOTSTRAP_REQUIRED")
    manifest = read_manifest(plan.bootstrap_manifest, plan.bootstrap_digest)
    files = {str(safe(e["path"])).casefold(): e["sha256"] for e in manifest["inventory"]["files"]}
    for path, item in zip(CORE_SKILLS, body["bodies"], strict=True):
        require(files.get(str(safe(Path(body["installed_root"]) / path)).casefold()) == item["sha256"],
                "SKILL_BODY_UNPINNED")
    return body


def project_initial_skills(database, cas, plan, grant, ref):
    body = read_skill_corpus(cas, ref)
    broker = NativeBroker(database, cas, plan.job_id, plan.profile_digest())
    for item in body["bodies"]:
        broker.project(grant.thread_id, item["path"], item["text"])
