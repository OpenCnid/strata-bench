"""Synthetic skill source and sealed-manifest fixtures; no native invocation."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from mcbench import native_skills
from mcbench.plugins import CORE_SKILLS, EXPLICIT_SKILLS
from mcbench.runtime import DOVETAIL_COMMIT
from mcbench.storage import Fault, canonical, digest
from test_native_broker import broker as _broker, meta

broker = _broker


@pytest.fixture
def corpus(cas, tmp_path, monkeypatch):
    root = tmp_path / "plugin"
    files = []
    for path in CORE_SKILLS:
        target = root / path
        target.parent.mkdir(parents=True)
        raw = ("Pinned synthetic skill – " + path + "\r\n").encode()
        target.write_bytes(raw)
        files.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest()})
    inventory = {"files": files, "installed_tree_digest": "b" * 64, "source_commit": DOVETAIL_COMMIT}
    monkeypatch.setattr(native_skills, "inspect_plugin_tree", lambda _: inventory)
    return native_skills.prepare_skill_corpus(cas, root), root, files


def test_exact_bytes_explicit_policy_and_private_corpus(cas, corpus):
    ref, root, _ = corpus
    body = native_skills.read_skill_corpus(cas, ref)
    assert len(body["bodies"]) == 8
    for path, item in zip(CORE_SKILLS, body["bodies"], strict=True):
        assert item["text"].encode() == (root / path).read_bytes()
        assert item["explicit_only"] is (path in EXPLICIT_SKILLS)


@pytest.mark.parametrize("change", ["content", "path", "invocation", "source", "count"])
def test_tampered_or_incomplete_projection_rejected(cas, corpus, operator, change):
    body = native_skills.read_skill_corpus(cas, corpus[0])
    if change == "content":
        body["bodies"][0]["text"] += "tampered"
    elif change == "path":
        body["bodies"][0]["path"] = "initial/../../operator"
    elif change == "invocation":
        body["bodies"][0]["explicit_only"] = True
    elif change == "source":
        body["source_commit"] = "f" * 40
    else:
        body["bodies"].pop()
    ref = cas.put(operator, "operator", "operator", canonical(body))
    with pytest.raises(Fault, match="SKILL_CORPUS"):
        native_skills.read_skill_corpus(cas, ref)


def test_corpus_must_match_sealed_installed_bytes(cas, corpus, tmp_path):
    ref, root, files = corpus
    manifest = {"schema": "strata/NativeBootstrap/1", "inventory": {"files": [
        {"path": str(root / e["path"]), "sha256": e["sha256"]} for e in files]}}
    path = tmp_path / "manifest.json"
    raw = json.dumps(manifest).encode()
    path.write_bytes(raw)
    plan = SimpleNamespace(bootstrap_manifest=str(path), bootstrap_digest=hashlib.sha256(raw).hexdigest())
    assert native_skills.validate_skill_bootstrap(cas, ref, plan)["source_commit"] == DOVETAIL_COMMIT
    manifest["inventory"]["files"][0]["sha256"] = "f" * 64
    raw = json.dumps(manifest).encode()
    path.write_bytes(raw)
    plan.bootstrap_digest = hashlib.sha256(raw).hexdigest()
    with pytest.raises(Fault, match="SKILL_BODY_UNPINNED"):
        native_skills.validate_skill_bootstrap(cas, ref, plan)


@pytest.fixture
def supporting(cas, corpus):
    _, root, files = corpus
    for path in ["references/provenance.md", "scripts/check.py", "agents/grader.md", "assets/template.html",
                 "tests/fixture/SKILL.md", "references/Fixtures/hidden.md", "scripts/auth.json"]:
        path = "skills/better-skill-creator/" + path
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = ("Pinned support fixture – " + path).encode()
        target.write_bytes(raw)
        files.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest()})
    ref = native_skills.prepare_skill_corpus(cas, root, supporting_files=True)
    return ref, root, files


def test_versioned_supporting_projection_remains_immutable_and_scoped(broker, supporting, monkeypatch):
    b, _, _ = broker
    ref, _, _ = supporting
    body = native_skills.read_skill_corpus(b.cas, ref)
    assert len(body["files"]) == 12 and len(body["bodies"]) == 8
    assert sum(x["is_skill"] for x in body["files"]) == 8
    assert native_skills.instructions_for_corpus(b.cas, ref) == native_skills.SUPPORT_INSTRUCTIONS
    plan = SimpleNamespace(job_id=b.runtime_id, profile_digest=lambda: b.profile_digest)
    grant = b._grant(b.db.connection, "root")[0]
    monkeypatch.setattr(native_skills, "NativeBroker", lambda *args: b)
    native_skills.project_initial_skills(b.db, b.cas, plan, grant, ref)
    for item in body["files"]:
        assert b.call("artifact_read", {"path": item["path"]}, meta())["text"] == item["text"]
        with pytest.raises(Fault, match="BROKER_WRITE_FORBIDDEN"):
            b.call("artifact_write", {"path": item["path"], "text": "replace", "expected_ref": None}, meta())
        with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
            b.call("artifact_read", {"path": item["path"]}, meta("child"))
    assert not any("fixture" in f["path"].lower() or "auth.json" in f["path"] for f in body["files"])


@pytest.mark.parametrize("change", ["omitted", "duplicate", "text", "new_skill", "unknown", "nonobject", "source_missing_core"])
def test_support_corruption_is_rejected(cas, supporting, operator, change):
    body = native_skills.read_skill_corpus(cas, supporting[0])
    if change == "omitted":
        body["files"].pop()
    elif change == "duplicate":
        body["files"].append(body["files"][0])
    elif change == "text":
        body["files"][0]["text"] += "altered"
    elif change == "new_skill":
        next(f for f in body["files"] if not f["is_skill"])["is_skill"] = True
    elif change == "unknown":
        body["execute_scripts"] = True
    elif change == "nonobject":
        body["files"][0] = None
    else:
        source = cas.json(operator, "operator", body["source_inventory_ref"])
        del source["files"][CORE_SKILLS[0]]
        body["source_inventory_ref"] = cas.put(operator, "operator", "operator", canonical(source))
    body["files_digest"] = digest(body["files"])
    ref = cas.put(operator, "operator", "operator", canonical(body))
    with pytest.raises(Fault, match="SKILL_CORPUS"):
        native_skills.read_skill_corpus(cas, ref)


def test_support_source_completeness_is_bound_to_held_manifest(cas, supporting, operator, tmp_path):
    ref, root, files = supporting
    raw = canonical({"schema": "strata/NativeBootstrap/1", "inventory": {"files": [
        {"path": str(root / f["path"]), "sha256": f["sha256"]} for f in files]}})
    path = tmp_path / "manifest.json"
    path.write_bytes(raw)
    plan = SimpleNamespace(bootstrap_manifest=str(path), bootstrap_digest=hashlib.sha256(raw).hexdigest())
    native_skills.validate_skill_bootstrap(cas, ref, plan)
    body = native_skills.read_skill_corpus(cas, ref)
    source = cas.json(operator, "operator", body["source_inventory_ref"])
    removed = next(f for f in body["files"] if not f["is_skill"])
    body["files"].remove(removed)
    del source["files"][removed["path"].removeprefix("initial/dovetail/")]
    body["source_inventory_ref"] = cas.put(operator, "operator", "operator", canonical(source))
    body["files_digest"] = digest(body["files"])
    ref = cas.put(operator, "operator", "operator", canonical(body))
    native_skills.read_skill_corpus(cas, ref)
    with pytest.raises(Fault, match="SKILL_BODY_UNPINNED"):
        native_skills.validate_skill_bootstrap(cas, ref, plan)
