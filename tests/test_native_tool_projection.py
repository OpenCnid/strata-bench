"""Synthetic projection/dispatch negatives; captured CLI evidence stays private."""

import copy
import json

import pytest

from mcbench.native_admission import NativeAdmission, require_request_admission
from mcbench.native_broker_policy import SETTINGS_POLICY
from mcbench.native_tool_projection import (
    COLLABORATION, FUNCTIONS, NativeToolProjection, POLICY, read_tool_projection,
    pin_tool_projection, request_projection, require_tool_projection,
)
from mcbench.storage import Fault, Principal, canonical, digest
from test_native_admission import admitted as _admitted, begin

admitted = _admitted


def wire_tools(role):
    groups = {"functions": FUNCTIONS}
    if role == "executor":
        groups["collaboration"] = COLLABORATION
    namespaces = []
    for group, names in groups.items():
        tools = []
        for name in sorted(names):
            custom = name == "exec"
            tool = {"type": "custom" if custom else "function", "name": name,
                    "description": "synthetic " + name}
            tool.update({"format": {"type": "grammar", "syntax": "lark", "definition": "synthetic"}}
                        if custom else {"strict": False, "parameters": {"type": "object",
                            "properties": {"limit": {"type": "integer", "maximum": 1}}}})
            tools.append(tool)
        namespaces.append({"type": "namespace", "name": group, "description": "synthetic", "tools": tools})
    return {"type": "additional_tools", "id": "at_synthetic", "role": "developer", "tools": namespaces}


@pytest.fixture
def pinned(admitted):
    admission, gate, _, plan, request, prepare, put = admitted
    old_digest = plan.profile_digest()
    refs = {role + "_ref": put(request_projection({"input": [wire_tools(role)]}, role))
            for role in ("executor", "helper")}
    manifest = NativeToolProjection.model_validate({"schema": "strata/NativeToolProjection/1",
        "policy": POLICY, **{k: getattr(plan, k) for k in (
            "binary_digest", "binary_version", "dovetail_commit", "model")},
        "settings_policy": SETTINGS_POLICY, "settings_digest": digest(plan.config_overrides), **refs})
    plan.tool_projection_ref = put(manifest.model_dump())
    assert plan.profile_digest() != old_digest
    gate.db.connection.execute("UPDATE native_jobs SET plan=?", (plan.model_dump_json(),))
    def projected(op, thread="root", name="/root", parent=None, *, mutate=None):
        def change(body):
            body["input"].insert(0, wire_tools("executor" if parent is None else "helper"))
            if mutate:
                mutate(body)
        return request(op, thread, name, parent, child=parent is not None, mutate=change)
    return admitted, projected, manifest


def test_exact_root_and_helper_admit_distinct_ids_without_double_reservation(pinned):
    admitted, request, _ = pinned
    admission, gate, _, plan, _, prepare, _ = admitted
    root = request("one")
    prepare(root)
    before = gate.budgets.status("a1")
    prepare(root)
    assert gate.budgets.status("a1") == before
    assert gate._begin("a1", root[0], root[1])
    admission.enroll("one")
    child = request("two", "child", "/root/child", "root",
                    mutate=lambda b: b["input"][0].update(id="at_different-id"))
    prepare(child)
    assert gate._begin("a1", child[0], child[1])
    assert admission.enroll("two").role == "helper"
    assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 1000
    events = [json.loads(r[0]) for r in gate.db.connection.execute(
        "SELECT body FROM outbox WHERE kind='native.request_admitted'")]
    assert all(e["tool_projection_ref"] == plan.tool_projection_ref for e in events)
    assert {e["tool_projection_digest"] for e in events} == {
        digest(v) for v in read_tool_projection(gate.cas, plan).values()}


def projection(body):
    return body["input"][0]


CHANGES = [
    pytest.param(lambda b: b.update(tools=[]), id="extra-top-level-tools"),
    pytest.param(lambda b: b.update(functions=[]), id="legacy-functions"),
    pytest.param(lambda b: b["input"].pop(0), id="missing"),
    pytest.param(lambda b: b["input"].append(copy.deepcopy(projection(b))), id="duplicate"),
    pytest.param(lambda b: projection(b).update(role="user"), id="wrong-role"),
    pytest.param(lambda b: projection(b).update(extra="capability"), id="extra-block-field"),
    pytest.param(lambda b: projection(b).update(id="not-a-native-id"), id="invalid-id"),
    pytest.param(lambda b: projection(b)["tools"].append({"name": "shell"}), id="added-namespace"),
    pytest.param(lambda b: projection(b)["tools"][0]["tools"].append({"name": "shell"}), id="added-tool"),
    pytest.param(lambda b: projection(b)["tools"][0]["tools"][0].update(description="new semantics"),
                 id="description"),
    pytest.param(lambda b: projection(b)["tools"][0]["tools"][0]["format"].update(definition="new grammar"),
                 id="grammar"),
    pytest.param(lambda b: projection(b)["tools"][0]["tools"][1]["parameters"].update(type="array"),
                 id="schema"),
    pytest.param(lambda b: projection(b)["tools"][0]["tools"][1].update(strict=True), id="strictness"),
    pytest.param(lambda b: projection(b)["tools"][0]["tools"][1]["parameters"]["properties"]["limit"].update(
        maximum=True), id="boolean-is-not-one"),
]


@pytest.mark.parametrize("mutate", CHANGES)
@pytest.mark.parametrize("helper", [False, True], ids=["root", "helper"])
def test_changed_projection_rejects_before_participant_envelope_or_dispatch(pinned, mutate, helper):
    admitted, request, _ = pinned
    _, gate, _, _, _, prepare, _ = admitted
    if helper:
        begin(admitted, request("one"))
    tables = ("operations", "native_participants", "native_request_admissions", "inference_attempts")
    before = [gate.db.connection.execute("SELECT count(*) FROM " + t).fetchone()[0] for t in tables]
    costs = gate.budgets.status("a1")
    value = (request("bad", "child", "/root/child", "root", mutate=mutate) if helper else
             request("bad", mutate=mutate))
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_(SHAPE|MISMATCH)"):
        prepare(value)
    assert before == [gate.db.connection.execute("SELECT count(*) FROM " + t).fetchone()[0] for t in tables]
    assert costs == gate.budgets.status("a1")


def test_known_root_cannot_gain_helper_or_altered_continuation_tools(pinned):
    admitted, request, _ = pinned
    _, gate, _, _, _, prepare, _ = admitted
    begin(admitted, request("one"))
    for tools in (wire_tools("helper"), wire_tools("executor")):
        tools["tools"][0]["description"] += "changed"
        with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_(SHAPE|MISMATCH)"):
            prepare(request("later", mutate=lambda b: b["input"].__setitem__(0, tools)))
    assert gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 1


@pytest.mark.parametrize("field,value", [("model", "another-model"), ("binary_digest", "b" * 64),
    ("binary_version", "different"), ("dovetail_commit", "d" * 40), ("settings_digest", "f" * 64)])
def test_pin_binds_runtime_and_settings(pinned, field, value):
    admitted, _, manifest = pinned
    _, gate, _, plan, _, _, put = admitted
    changed = plan.model_copy(update={"tool_projection_ref": put(manifest.model_dump() | {field: value})})
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_SCOPE"):
        read_tool_projection(gate.cas, changed)


def test_projection_is_operator_private_and_hash_checked_again_at_dispatch(pinned):
    admitted, request, manifest = pinned
    _, gate, _, plan, _, prepare, _ = admitted
    value = request("one")
    prepare(value)
    before = gate.budgets.status("a1")
    original = gate.cas._path(manifest.executor_ref).read_bytes()
    gate.cas._path(manifest.executor_ref).write_bytes(b"changed after prepare")
    restarted = NativeAdmission(gate.db, gate.cas)
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE"):
        gate._begin("a1", value[0], value[1])
    assert restarted.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0
    assert gate.budgets.status("a1") == before
    gate.cas._path(manifest.executor_ref).write_bytes(original)
    gate.db.connection.execute("UPDATE objects SET visibility='agent' WHERE ref=?", (manifest.helper_ref,))
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_PRIVATE"):
        require_tool_projection(gate.cas, plan, {"input": [wire_tools("helper")]}, "helper")


def test_live_dispatch_rejects_legacy_unpinned_admission(admitted):
    _, gate, _, plan, request, prepare, _ = admitted
    value = request("one")
    prepare(value)
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_REQUIRED"):
        require_request_admission(gate.db.connection, plan, value[0], value[1], "a1",
                                  cas=gate.cas, simulation=False)
    assert gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0


def test_raw_request_changed_after_prepare_is_never_dispatched(pinned):
    admitted, request, _ = pinned
    _, gate, _, _, _, prepare, _ = admitted
    value = request("one")
    prepare(value)
    ref = gate.db.connection.execute("SELECT raw_ref FROM native_request_admissions").fetchone()[0]
    gate.cas._path(ref).write_bytes(b"tampered request")
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE"):
        gate._begin("a1", value[0], value[1])
    assert gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0


def test_agent_visible_projection_cannot_be_used_as_operator_pin(pinned):
    admitted, _, manifest = pinned
    _, gate, _, plan, _, _, _ = admitted
    ref = gate.cas.put(Principal("operator", "operator"), "operator", "agent",
                      canonical(manifest.model_dump() | {"model": "agent-visible"}))
    changed = plan.model_copy(update={"tool_projection_ref": ref})
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_PRIVATE"):
        read_tool_projection(gate.cas, changed)


def test_operator_setup_pins_only_preexisting_complete_projections(pinned):
    context, _, _ = pinned
    _, gate, _, plan, _, _, _ = context
    reviewed = read_tool_projection(gate.cas, plan)
    assert pin_tool_projection(gate.cas, plan, reviewed) == plan.tool_projection_ref
    for bad in ({"executor": reviewed["executor"]},
                {"executor": reviewed["helper"], "helper": reviewed["executor"]}):
        with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_SHAPE"):
            pin_tool_projection(gate.cas, plan, bad)


def test_omitted_pin_preserves_legacy_profile_identity(admitted):
    _, _, _, plan, _, _, _ = admitted
    original = plan.model_dump()
    original.pop("tool_projection_ref")
    from mcbench.native import NativeLaunch
    assert NativeLaunch.model_validate(original).profile_digest() == plan.profile_digest()


@pytest.mark.parametrize("helper", [False, True])
def test_legacy_running_live_job_cannot_reserve_without_projection(admitted, helper):
    _, gate, _, _, request, prepare, _ = admitted
    if helper:
        begin(admitted, request("one"))
    value = request("two", "child", "/root/child", "root", child=True) if helper else request("one")
    gate.db.connection.execute("UPDATE native_profile SET simulation=0")
    before = gate.budgets.status("a1")
    counts = tuple(gate.db.connection.execute("SELECT count(*) FROM " + table).fetchone()[0]
        for table in ("operations", "native_participants", "native_request_admissions"))
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_REQUIRED"):
        prepare(value)
    assert gate.budgets.status("a1") == before
    assert counts == tuple(gate.db.connection.execute("SELECT count(*) FROM " + table).fetchone()[0]
        for table in ("operations", "native_participants", "native_request_admissions"))
