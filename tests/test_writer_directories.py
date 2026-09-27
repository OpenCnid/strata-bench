"""Directory schema and actual Java copier checks; no sandbox/game qualification."""

import base64
import json
import os
import subprocess
import time

import pytest

from strata_evaluator.writer_preparation import parse_preparation_plan
from strata_evaluator.writer_staging import stage_bundles
from test_writer_preparation import plan
from test_writer_staging import compiled_helper, sources_at

plan, compiled_helper = plan, compiled_helper


@pytest.mark.parametrize("directories", [["world"], ["world", "world/empty", "world/empty/nested"]])
def test_explicit_directory_inventory_is_part_of_new_plan(plan, directories):
    value = plan | {
        "schema": "strata/PrivateWriterPreparationPlan/4",
        "network_policy": "native-online-private-server/1",
        "staging_policy": "sequential-bundles512mib/1",
        "directories": directories,
    }
    assert parse_preparation_plan(value).directories == directories


@pytest.mark.parametrize(
    "directories",
    [
        [],
        ["world", "WORLD"],
        ["world", "world/level.dat"],
        ["world", "world/empty/nested"],
        ["world", "../escape"],
        ["world", "NUL"],
    ],
)
def test_incomplete_colliding_or_unsafe_directories_refuse(plan, directories):
    value = plan | {
        "schema": "strata/PrivateWriterPreparationPlan/4",
        "network_policy": "native-online-private-server/1",
        "staging_policy": "sequential-bundles512mib/1",
        "directories": directories,
    }
    with pytest.raises(ValueError, match="WRITER_DIRECTORY_SCOPE|UNSAFE_PATH"):
        parse_preparation_plan(value)


@pytest.mark.parametrize(
    "directories",
    [
        ["world", "world/empty", "world/empty/nested"],
        ["../escape"],
        ["world//empty"],
        ["world", "WORLD"],
        ["world/file-0"],
    ],
)
def test_actual_java_preserves_empty_directories_and_refuses_bad_manifests(
    tmp_path, compiled_helper, directories
):
    java, classes = compiled_helper
    sources = sources_at(tmp_path / "source", [b"file bytes"])
    staging, control, target = (tmp_path / name for name in ("staging", "control", "target"))
    for directory in (staging, control, target):
        directory.mkdir()
    _, manifest, _ = stage_bundles(staging, sources, time.monotonic() + 10)
    (control / "files.tsv").write_bytes(manifest)
    (control / "directories.tsv").write_bytes(
        b"\n".join(base64.b64encode(p.encode()) for p in directories)
    )
    challenge = "c" * 64
    for name in ("prepare.grant", "finish.grant"):
        (control / name).write_text(challenge)
    result = subprocess.run(
        [
            java,
            "-cp",
            str(classes),
            "StrataWriterPreparation",
            str(target),
            str(control),
            challenge,
        ],
        capture_output=True,
        text=True,
        timeout=25,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if directories == ["world", "world/empty", "world/empty/nested"]:
        assert result.returncode == 0, result.stderr
        receipt = json.loads((control / "copied.json").read_bytes())
        assert receipt["schema"] == "strata/WriterJavaCopied/3" and receipt["directories"] == 3
        assert {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_dir()} == set(
            directories
        )
    else:
        assert result.returncode != 0 and not (control / "copied.json").exists()
    assert not (tmp_path / "escape").exists()
