"""Writer plan/identity/state boundaries; no game or inference admission."""

import copy
import os
from pathlib import Path

import pytest

from mcbench.storage import Database, Fault
from strata_evaluator.writer_preparation import (
    WriterPreparationPlan, WriterPreparations, java_identity, grant, CODEX_SHA256,
)


def pin(path, digest="a" * 64):
    return {"path": str(path), "sha256": digest, "bytes": 8}


@pytest.fixture
def plan(tmp_path):
    return {"schema": "strata/PrivateWriterPreparationPlan/1", "id": "preparation",
        "evidence_kind": "synthetic", "codex": pin(tmp_path / "codex.exe", CODEX_SHA256),
        "java": pin(tmp_path / "java.exe"), "helper_class": pin(tmp_path / "StrataWriterPreparation.class"),
        "sandbox_home": str(tmp_path / "enrollment"), "writer_sid": "S-1-5-21-1-2-3-1003",
        "source_root": str(tmp_path / "source"), "sources": {"world/level.dat": pin(tmp_path / "source/level.dat")},
        "workspace_directory": str(tmp_path / "workspace"), "evidence_directory": str(tmp_path / "evidence"),
        "max_wall_s": 60}


@pytest.mark.parametrize("change,code", [
    ("runtime", "WRITER_RUNTIME_PIN"), ("java", "WRITER_HELPER_PROFILE"),
    ("helper", "WRITER_HELPER_PROFILE"), ("source_scope", "WRITER_SOURCE_SCOPE"),
    ("overlap", "WRITER_SOURCE_SCOPE"), ("workspace", "WRITER_WORKSPACE_SCOPE"),
    ("relative", "UNSAFE_PATH"), ("collision", "WRITER_SOURCE_SCOPE"),
    ("oversize", "WRITER_SOURCE_SCOPE"),
])
def test_changed_or_unsafe_preparation_scope_rejects_before_dispatch(plan, change, code):
    if change == "runtime":
        plan["codex"]["sha256"] = "b" * 64
    elif change == "java":
        plan["java"]["path"] = str(Path(plan["java"]["path"]).with_name("other.exe"))
    elif change == "helper":
        plan["helper_class"]["path"] += ".other"
    elif change == "source_scope":
        plan["sources"]["world/level.dat"]["path"] = plan["java"]["path"]
    elif change == "overlap":
        plan["evidence_directory"] = plan["source_root"]
    elif change == "workspace":
        plan["workspace_directory"] = plan["evidence_directory"]
    elif change == "relative":
        plan["sources"]["../escape"] = plan["sources"].pop("world/level.dat")
    elif change == "collision":
        plan["sources"]["WORLD/LEVEL.DAT"] = plan["sources"]["world/level.dat"]
    elif change == "oversize":
        plan["sources"]["world/level.dat"]["bytes"] = 512 * 1024**2 + 1
    with pytest.raises((Fault, ValueError), match=code):
        WriterPreparationPlan.model_validate(plan)


class HeldJob:
    def __init__(self, actual):
        self.actual = actual
        self.queried = []

    def member_identity(self, pid):
        self.queried.append(pid)
        if pid != self.actual["pid"]:
            raise Fault("PROCESS_MEMBER_UNOBSERVED")
        return self.actual.copy()


@pytest.fixture
def identity(tmp_path):
    actual = {"pid": 1234, "executable": str(tmp_path / "java.exe"), "process_started_unix_ms": 100000}
    value = {"schema": "strata/WriterJavaIdentity/2", "challenge": "c" * 64, **actual,
             "requested_root": str(tmp_path / "guarded")}
    return value, HeldJob(actual)


@pytest.mark.parametrize("field,value", [("challenge", "d" * 64), ("pid", 1235),
    ("pid", True), ("process_started_unix_ms", 99999), ("executable", "wrong.exe"),
    ("requested_root", "wrong"), ("schema", "strata/WriterJavaIdentity/1")])
def test_self_report_cannot_replace_retained_process_identity(identity, field, value):
    original, job = identity
    candidate = copy.deepcopy(original)
    candidate[field] = value
    with pytest.raises(Fault, match="WRITER_JAVA_IDENTITY|PROCESS_MEMBER_UNOBSERVED"):
        java_identity(candidate, original["challenge"], Path(original["requested_root"]),
                      original["executable"], job)


def test_matching_identity_queries_the_retained_job(identity):
    value, job = identity
    result = java_identity(value, value["challenge"], Path(value["requested_root"]), value["executable"], job)
    assert result == job.actual and job.queried == [1234]


@pytest.mark.skipif(os.name != "nt", reason="Windows native preparation publication")
def test_grant_publication_never_replaces_an_existing_authority(tmp_path):
    target = tmp_path / "prepare.grant"
    grant(target, "a" * 64)
    with pytest.raises(FileExistsError):
        grant(target, "b" * 64)
    assert target.read_text() == "a" * 64


@pytest.mark.skipif(os.name != "nt", reason="Windows native preparation admission")
def test_synthetic_preparation_cannot_admit_an_authentic_game_profile(plan, tmp_path):
    plan["evidence_kind"] = "authentic_operator_reference"
    database = Database(tmp_path / "operator.sqlite")
    try:
        preparations = WriterPreparations(database)
        with pytest.raises(Fault, match="WRITER_PROFILE_UNQUALIFIED"):
            preparations.run(plan)
        assert database.connection.execute("SELECT count(*) FROM writer_preparations").fetchone()[0] == 0
        assert not Path(plan["workspace_directory"]).exists()
    finally:
        database.connection.close()
