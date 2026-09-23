"""Exact pinned Dovetail skill bodies exposed through immutable broker files.

This enables native skill reads without granting shell or filesystem access.
Version 2 also exposes pinned supporting text. Script execution and learned-skill
activation are separate capabilities; readable code does not grant execution.
"""

import hashlib
import json
from pathlib import Path

from .broker import MAX_TEXT, NativeBroker
from .plugins import CORE_SKILLS, EXPLICIT_SKILLS, inspect_plugin_tree, _extended_path
from .runtime import DOVETAIL_COMMIT
from .storage import Principal, canonical, digest, require, safe_relative

POLICY = "dovetail-eight-immutable-bodies/1"
SUPPORT_POLICY = "dovetail-eight-immutable-text-support/1"
MAX_CORPUS = 20 * 1024 * 1024
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
SUPPORT_INSTRUCTIONS = (
    "Use the installed native Dovetail skill catalog and its invocation rules. "
    "Read an activated Dovetail skill body through strata_broker.artifact_read at "
    "initial/dovetail/skills/<skill-name>/SKILL.md. Read its supporting text using "
    "the same prefix and the relative path named by the skill. Use "
    "strata_broker.artifact_list to inspect your permitted artifacts. These initial "
    "files are immutable. Script source is readable text; this profile does not "
    "grant shell/script execution or learned-skill activation. Report unavailable "
    "capabilities explicitly. Only the eight top-level Dovetail skills are indexed; "
    "supporting files do not create additional skills or tools."
)


def support_path(path):
    """Reviewed public support surfaces; no nested tests, fixtures or VCS trees."""
    parts = safe_relative(path).parts
    roots = {tuple(safe_relative(p).parts[:2]) for p in CORE_SKILLS}
    if len(parts) < 3 or tuple(parts[:2]) not in roots:
        return False
    if len(parts) == 3:
        return parts[2] in {"SKILL.md", "LICENSE.md", "LICENSE.txt", "NOTICE", "requirements.txt"}
    return parts[2] in {"references", "scripts", "assets", "agents", "eval-viewer"} and not {
        p.casefold() for p in parts[3:]} & {
        "tests", "fixtures", ".git", "__pycache__", ".codex", ".ssh", ".aws", "auth.json",
        "credentials.json", "keys.json", "launcher_accounts.json", "auth-cache", "auth_cache"}


def prepare_skill_corpus(cas, installed_root, *, supporting_files=False):
    """Operator-only source inspection; no gameplay-controlled filesystem path."""
    require(type(supporting_files) is bool, "SKILL_CORPUS")
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
    if supporting_files:
        selected = sorted(path for path in pinned if support_path(path))
        require(set(CORE_SKILLS) <= set(selected) and len(selected) <= 1000, "SKILL_CORPUS_SIZE")
        files = []
        for path in selected:
            raw = _extended_path(root / path).read_bytes()
            require(len(raw) <= MAX_TEXT and hashlib.sha256(raw).hexdigest() == pinned[path]["sha256"],
                    "SKILL_BODY_CHANGED")
            files.append({"path": "initial/dovetail/" + path, "sha256": pinned[path]["sha256"],
                "text": raw.decode("utf-8", errors="strict"), "is_skill": path in CORE_SKILLS})
        source = {"schema": "strata/NativeSkillSourceInventory/1", "source_commit": DOVETAIL_COMMIT,
                  "installed_tree_digest": inventory["installed_tree_digest"],
                  "files": {p: v["sha256"] for p, v in pinned.items()}}
        source_ref = cas.put(OPERATOR, "operator", "operator", canonical(source), max_object_bytes=MAX_CORPUS)
        body |= {"schema": "strata/NativeSkillCorpus/2", "policy": SUPPORT_POLICY,
                 "source_inventory_ref": source_ref, "files": files, "files_digest": digest(files)}
    raw = canonical(body)
    require(len(raw) <= (MAX_CORPUS if supporting_files else 1024 * 1024), "SKILL_CORPUS_SIZE")
    return cas.put(OPERATOR, "operator", "operator", raw,
                   max_object_bytes=MAX_CORPUS if supporting_files else MAX_TEXT)


def read_skill_corpus(cas, ref):
    row = cas.database.connection.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?",
                                    (ref,)).fetchone()
    require(row is not None and row[0] == "operator", "SKILL_CORPUS_PRIVATE")
    raw = cas.read(OPERATOR, "operator", ref, max_bytes=MAX_CORPUS)
    body = json.loads(raw)
    require(isinstance(body, dict) and (body.get("schema"), body.get("policy")) in {
                ("strata/NativeSkillCorpus/1", POLICY), ("strata/NativeSkillCorpus/2", SUPPORT_POLICY)} and
            body.get("source_commit") == DOVETAIL_COMMIT and
            isinstance(body.get("bodies"), list) and len(body["bodies"]) == len(CORE_SKILLS), "SKILL_CORPUS")
    for path, item in zip(CORE_SKILLS, body["bodies"], strict=True):
        require(isinstance(item, dict) and set(item) == {"path", "sha256", "text", "explicit_only"} and
                item["path"] == "initial/dovetail/" + path and isinstance(item["text"], str) and
                len(item["text"].encode("utf-8")) <= MAX_TEXT and
                hashlib.sha256(item["text"].encode("utf-8")).hexdigest() == item["sha256"] and
                item["explicit_only"] is (path in EXPLICIT_SKILLS), "SKILL_CORPUS")
    if body["policy"] == POLICY:
        require(len(raw) <= 1024 * 1024, "SKILL_CORPUS_SIZE")
    if body["policy"] == SUPPORT_POLICY:
        require(set(body) == {"schema", "policy", "source_commit", "installed_tree_digest", "installed_root",
            "bodies", "source_inventory_ref", "files", "files_digest"}, "SKILL_CORPUS")
        source_ref = body.get("source_inventory_ref")
        require(isinstance(source_ref, str), "SKILL_CORPUS")
        source_row = cas.database.connection.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?",
                                                     (source_ref,)).fetchone()
        require(source_row is not None and source_row[0] == "operator", "SKILL_CORPUS_PRIVATE")
        source = json.loads(cas.read(OPERATOR, "operator", source_ref, max_bytes=MAX_CORPUS))
        require(isinstance(source, dict) and set(source) == {
                "schema", "source_commit", "installed_tree_digest", "files"} and
                source.get("schema") == "strata/NativeSkillSourceInventory/1" and
                source.get("source_commit") == DOVETAIL_COMMIT and
                source.get("installed_tree_digest") == body["installed_tree_digest"] and
                isinstance(source.get("files"), dict), "SKILL_CORPUS")
        expected = {"initial/dovetail/" + p: v for p, v in source["files"].items() if support_path(p)}
        require({"initial/dovetail/" + p for p in CORE_SKILLS} <= set(expected) and
                len({p.casefold() for p in expected}) == len(expected), "SKILL_CORPUS")
        files = body.get("files")
        require(isinstance(files, list) and all(isinstance(f, dict) for f in files) and
                len(files) == len(expected) <= 1000 and digest(files) == body.get("files_digest"),
                "SKILL_CORPUS")
        require([f.get("path") for f in files] == sorted(expected), "SKILL_CORPUS")
        for item in files:
            path = item["path"].removeprefix("initial/dovetail/")
            require(set(item) == {"path", "sha256", "text", "is_skill"} and isinstance(item["text"], str) and
                len(item["text"].encode("utf-8")) <= MAX_TEXT and
                hashlib.sha256(item["text"].encode("utf-8")).hexdigest() == item["sha256"] == expected[item["path"]]
                and item["is_skill"] is (path in CORE_SKILLS), "SKILL_CORPUS")
        by_path = {x["path"]: x for x in files}
        require(all(all(item[k] == by_path[item["path"]][k] for k in ("text", "sha256"))
                    for item in body["bodies"]), "SKILL_CORPUS")
    return body


def instructions_for_corpus(cas, ref):
    return SUPPORT_INSTRUCTIONS if read_skill_corpus(cas, ref)["policy"] == SUPPORT_POLICY else INSTRUCTIONS


def validate_skill_bootstrap(cas, ref, plan):
    from .launch_integrity import read_manifest, safe
    body = read_skill_corpus(cas, ref)
    require(plan.bootstrap_manifest is not None and plan.bootstrap_digest is not None,
            "SKILL_BOOTSTRAP_REQUIRED")
    manifest = read_manifest(plan.bootstrap_manifest, plan.bootstrap_digest)
    files = {str(safe(e["path"])).casefold(): e["sha256"] for e in manifest["inventory"]["files"]}
    projected = body.get("files", body["bodies"])
    if body["policy"] == SUPPORT_POLICY:
        root = safe(body["installed_root"])
        held = {}
        for entry in manifest["inventory"]["files"]:
            path = safe(entry["path"])
            if path.is_relative_to(root):
                relative = path.relative_to(root).as_posix()
                if support_path(relative):
                    held["initial/dovetail/" + relative] = entry["sha256"]
        require(held == {f["path"]: f["sha256"] for f in projected}, "SKILL_BODY_UNPINNED")
    for item in projected:
        path = item["path"].removeprefix("initial/dovetail/")
        require(files.get(str(safe(Path(body["installed_root"]) / path)).casefold()) == item["sha256"],
                "SKILL_BODY_UNPINNED")
    return body


def project_initial_skills(database, cas, plan, grant, ref):
    body = read_skill_corpus(cas, ref)
    broker = NativeBroker(database, cas, plan.job_id, plan.profile_digest())
    for item in body.get("files", body["bodies"]):
        broker.project(grant.thread_id, item["path"], item["text"])
    from .native_piloting import PURPOSE, GAME_CONTRACT_PATH, game_contract
    if getattr(plan, "purpose", None) == PURPOSE and grant.role == "executor":
        broker.project(grant.thread_id, GAME_CONTRACT_PATH, game_contract())
