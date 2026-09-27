"""Versioned lexical packaging classifier for the frozen-skills intervention.

This does not determine whether prose encodes an implicit procedure. Every
accepted note remains ambiguous in that sense and requires a sampled audit.
It is not a general code-execution or prompt-injection security boundary.
"""

import json
import re
import unicodedata

from .storage import Principal, require, safe_relative

CLASSIFIER = "frozen-notes-markdown-no-code/1"


def classify_note(path, text):
    relative = safe_relative(path)
    require(relative.suffix.casefold() in {".md", ".txt"}, "FROZEN_NOTE_FORMAT")
    require(isinstance(text, str), "FROZEN_NOTE_FORMAT")
    value = unicodedata.normalize("NFKC", text).casefold()
    require(not any(unicodedata.category(c).startswith("C") and c not in "\r\n\t" for c in value),
            "FROZEN_NOTE_CODE")
    patterns = (
        r"```|~~~|(?m:^(?: {4}|\t)\S)|(?m:^\s*#!)",
        r"(?m:^---\s*\n)|<\s*/?\s*(?:script|iframe|object|embed|svg)\b|\bon\w+\s*=",
        r"\b(?:functions\s*\.|tools\s*[.\[]|all_tools\b|mcp__|call_id\b)",
        r"(?m:^\s*(?:async\s+)?(?:function|def|class)\s+\w+[^\n]*[:({])",
        r"(?m:^\s*(?:(?:const|let|var)\s+\w+\s*=|import\s+\w|from\s+[^\n]+\s+import\b))",
        r"(?m:^\s*(?:for|while|if|try|with)\b[^\n]*[:{]\s*$)",
        r"(?m:^\s*(?:\$?[\w.]+\s*(?:=|:=)|[\w.$]+\s*\())",
        r"[\w.$]+\s*\([^\n]*\)|[\])](?:\s*\(|\s*=)|=>|\$\(|\$\{|\b(?:eval|exec|invoke-expression)\b",
        r"(?m:^\s*(?:python\d*|node|powershell|pwsh|cmd|bash|sh)\s+[-/])",
        r"(?m:^\s*[\[{])|[\"'](?:tool|function|arguments|actions|steps|trigger)[\"']\s*:",
    )
    require(not any(re.search(pattern, value) for pattern in patterns), "FROZEN_NOTE_CODE")
    # Whole structured payloads can package tool arguments or procedures. Keep
    # the declared note format prose; ordinary inline resource IDs are allowed.
    try:
        parsed = json.loads(value)
    except ValueError:
        parsed = None
    require(not isinstance(parsed, (dict, list)), "FROZEN_NOTE_CODE")
    return {"classifier": CLASSIFIER, "verdict": "prose", "implicit_procedure_ambiguity": True}


def validate_tree(policy, files, initial, cas, *, namespace="operator", role="operator"):
    if policy.schema_ != "strata/NativeRetentionPolicy/2":
        return
    for path, ref in files.items():
        prefix = path.split("/", 1)[0]
        if prefix == "skills":
            require(initial.get(path) == ref, "FROZEN_SKILL_WRITE")
        elif prefix in {"notes", "handoff", "results"}:
            classify_note(path, cas.read(Principal(namespace, role), namespace, ref).decode("utf-8"))


def write_policy(db, cas, grant, path, text):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='native_retention_policies'").fetchone():
        return None
    row = db.execute("SELECT ref FROM native_retention_policies WHERE campaign=? AND agent=?",
                     (grant.campaign_id, grant.agent_id)).fetchone()
    if row is None:
        return None
    from .native_checkpoint import parse_retention_policy
    from .native_export import private_json
    policy = parse_retention_policy(private_json(db, cas, row[0]))
    if policy.schema_ != "strata/NativeRetentionPolicy/2":
        return None  # Old conformance/readback is explicitly not category-qualified.
    require(policy.campaign_id == grant.campaign_id and policy.agent_id == grant.agent_id, "NATIVE_ARM_SCOPE")
    require(path.split("/", 1)[0] != "skills", "FROZEN_SKILL_WRITE")
    return {"policy_ref": row[0], **classify_note(path, text)}
