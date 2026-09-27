"""Operator-only native probe artifact binding; no launch or dispatch authority.

The evaluator compiles these records from complete prepared pairs. The native
consumer reads committed operator records only, without loading evaluator code.
Held world/resource custody and a disposable runtime remain separate gates.
"""

import json
import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from .contracts import Digest, Id, Ref, Strict
from .native_export import OPERATOR, private_json
from .storage import canonical, digest, extended_path, require

POLICY = "disposable-native-artifact-binding/1"


class NativeProbeDestination(Strict):
    job_id: Id
    campaign_id: Id
    agent_id: Id
    account: Id
    operation_id: Id
    supply_helper_artifacts: bool


class NativeProbeCatalogSkill(Strict):
    name: Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{0,63}$")]
    description: Annotated[str, Field(min_length=1, max_length=512)]
    revision_id: Id
    files: dict[str, Ref] = Field(min_length=1, max_length=1024)


class NativeProbeArtifactBinding(Strict):
    schema_: Literal["strata/NativeProbeArtifactBinding/1"] = Field(alias="schema")
    policy: Literal["disposable-native-artifact-binding/1"]
    is_example: bool
    destination: NativeProbeDestination
    pair_namespace: Annotated[str, Field(pattern=r"^evaluation:.+", max_length=256)]
    pair_id: Id
    pair_plan_digest: Digest
    views_plan_digest: Digest
    workspace: str
    profile_directory: str
    model: Annotated[str, Field(min_length=1, max_length=128)]
    provider: Annotated[str, Field(min_length=1, max_length=128)]
    helper_limit: int = Field(ge=0, le=32)
    helper_depth: int = Field(ge=0, le=2)
    control_arm: Literal["full", "frozen-persistence", "frozen-skills", "no-self-play"]
    public_goal: Annotated[str, Field(min_length=1, max_length=8000)]
    instructions: Annotated[str, Field(min_length=1, max_length=8000)]
    broker_files: dict[Literal["executor", "helper"], dict[str, Ref]]
    catalog: dict[str, NativeProbeCatalogSkill]


def read_binding(db, cas, ref):
    body = NativeProbeArtifactBinding.model_validate(private_json(db, cas, ref))
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='native_probe_bindings'").fetchone(),
            "NATIVE_PROBE_UNCOMMITTED")
    row = db.execute("SELECT body FROM native_probe_bindings WHERE ref=?", (ref,)).fetchone()
    require(row is not None and row[0] == canonical(body.model_dump()).decode(), "NATIVE_PROBE_UNCOMMITTED")
    siblings = {}
    for member in db.execute("SELECT arm,source_agent,ref FROM native_probe_bindings WHERE namespace=? AND pair=?",
                             (body.pair_namespace, body.pair_id)):
        siblings.setdefault(member["arm"], {})[member["source_agent"]] = member["ref"]
    registered = db.execute("SELECT digest FROM native_probe_binding_sets WHERE namespace=? AND pair=?",
                            (body.pair_namespace, body.pair_id)).fetchone()
    require(registered is not None and registered[0] == digest(siblings), "NATIVE_PROBE_ROSTER")
    for table, key, expected in (("probe_pair_staging", "id", body.pair_plan_digest),
                                 ("probe_native_views", "pair", body.views_plan_digest)):
        source = db.execute(f"SELECT state,plan FROM {table} WHERE namespace=? AND {key}=?",
                            (body.pair_namespace, body.pair_id)).fetchone()
        require(source is not None and source["state"] == "PREPARED" and
                digest(json.loads(source["plan"])) == expected, "NATIVE_PROBE_SOURCE_CHANGED")
    for files in body.broker_files.values():
        for value in files.values():
            visibility = db.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?",
                                    (value,)).fetchone()
            require(visibility is not None and visibility[0] == "operator", "NATIVE_PROBE_ARTIFACT_SOURCE")
            cas.verify(OPERATOR, "operator", value)
    return body


def require_binding_account(db, body):
    from .budgets import Budgets
    d = body.destination
    chain = Budgets.ancestors(db, d.account)
    leaf = chain[0]
    require(leaf["category"] == "evaluation" and leaf["campaign"] == d.campaign_id and
            leaf["agent"] == d.agent_id and all(a["category"] in (None, "evaluation") and
            a["campaign"] in ("*", d.campaign_id) for a in chain[1:]), "NATIVE_PROBE_ACCOUNT")


def require_binding_scope(db, cas, plan):
    body = read_binding(db, cas, plan.probe_binding_ref)
    d = body.destination
    require(plan.purpose == "probe" and all(getattr(plan, field) == getattr(d, field) for field in (
        "job_id", "campaign_id", "agent_id", "account", "operation_id")) and
        plan.epoch == 1 and plan.role == "executor" and plan.depth == 0 and plan.parent_job_id is None and
        all(getattr(plan, field) == getattr(body, field) for field in ("model", "provider", "helper_limit")) and
        extended_path(Path(plan.workspace)) == Path(body.workspace) and
        extended_path(Path(plan.profile_directory)) == Path(body.profile_directory) and
        plan.session_storage == "ephemeral" and plan.budget_mode == "per_dispatch" and
        plan.skill_activation_ref is None and plan.helper_skill_activation_ref is None and
        plan.resume_component_ref is None and
        plan.helper_probe_binding_ref == (plan.probe_binding_ref if d.supply_helper_artifacts else None),
        "NATIVE_PROBE_SCOPE")
    require(plan.prompt == body.public_goal, "NATIVE_PROBE_PROMPT")
    require_binding_account(db, body)
    from .native_broker_policy import NO_HELPER_POLICIES
    require((plan.helper_limit == 0) == (plan.broker_policy in NO_HELPER_POLICIES), "NATIVE_PROBE_HELPERS")
    return body


def artifact_inputs(db, cas, plan, role):
    """Return a fresh approved role map, never the private binding/provenance."""
    body = require_binding_scope(db, cas, plan)
    require(role in body.broker_files and (role == "executor" or
            plan.helper_probe_binding_ref == plan.probe_binding_ref), "NATIVE_PROBE_HELPERS")
    return dict(body.broker_files[role])


def require_probe_catalog(db, cas, plan, request, role):
    body = require_binding_scope(db, cas, plan)
    require(role in body.broker_files and (role == "executor" or
            plan.helper_probe_binding_ref == plan.probe_binding_ref), "NATIVE_PROBE_HELPERS")
    blocks = []
    for item in request.get("input", []):
        if item.get("role") == "developer" and item.get("type") == "message":
            for part in item.get("content", []):
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    blocks.extend(re.findall(r"<skills_instructions>(.*?)</skills_instructions>", part["text"], re.S))
    require(len(blocks) == 1, "NATIVE_PROBE_CATALOG")
    text = blocks[0].replace("\\", "/")
    roots = re.findall(r"^- `(r\d+)` = `([^`]+)`$", text, re.M)
    require(len(dict(roots)) == len(roots), "NATIVE_PROBE_CATALOG")
    roots, actual = dict(roots), {}
    entries = re.findall(r"^- ([^:\n]+): (.*?) \(file: ([^)\n]+)\)$", text, re.M)
    for name, description, location in entries:
        alias, _, tail = location.partition("/")
        path = roots[alias] + "/" + tail if alias in roots else location
        require(name not in actual, "NATIVE_PROBE_CATALOG")
        actual[name] = (description, path)
    # No unrelated host skill may hide outside the learned overlay namespace.
    root = Path(plan.workspace).as_posix().rstrip("/")
    expected = {name: (value.description, root + "/.agents/skills/" + name + "/SKILL.md")
                for name, value in body.catalog.items()}
    require(actual == expected, "NATIVE_PROBE_CATALOG")
