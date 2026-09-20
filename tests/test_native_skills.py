"""Synthetic skill source and sealed-manifest fixtures; no native invocation."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from mcbench import native_skills
from mcbench.plugins import CORE_SKILLS, EXPLICIT_SKILLS
from mcbench.runtime import DOVETAIL_COMMIT
from mcbench.storage import Fault, canonical


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
