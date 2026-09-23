"""Bundle transport controls; JVM component cases do not prove writer isolation."""

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import pytest

from mcbench.launch_integrity import FileLease, IntegrityError
from mcbench.storage import Fault
from strata_evaluator.craft_reference import PrivateFile
from strata_evaluator import writer_staging as staging


def sources_at(root, payloads):
    root.mkdir()
    sources = {}
    for index, payload in enumerate(payloads):
        path = root / str(index)
        path.write_bytes(payload)
        sources[f"world/file-{index}"] = PrivateFile(path=str(path), bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest())
    return sources


@pytest.mark.skipif(os.name != "nt", reason="Windows deny-write sharing contract")
def test_bundles_split_only_between_sources_and_keep_original_pins(tmp_path, monkeypatch):
    monkeypatch.setattr(staging, "MAX_PART", 8)
    monkeypatch.setattr(staging, "MAX_TOTAL", 16)
    sources = sources_at(tmp_path / "source", [b"12345", b"", b"abcdef", b"7890"])
    output = tmp_path / "staging"
    output.mkdir()
    pins, manifest, report = staging.stage_bundles(output, sources, time.monotonic() + 10)
    assert [pin["bytes"] for pin in pins] == [5, 6, 4]
    assert report == {"policy": staging.POLICY, "files": 4, "bundles": 3, "bytes": 15}
    for line, original in zip(manifest.decode().splitlines()[1:], sources.values()):
        _, path, sha, size, offset = line.split("\t")
        part = Path(base64.b64decode(path).decode()).read_bytes()
        assert part[int(offset):int(offset) + int(size)] == Path(original.path).read_bytes()
        assert sha == original.sha256 and int(size) == original.bytes
    with FileLease({"schema": "strata/LaunchFileInventory/1", "files": pins, "trees": []}):
        for pin in pins:
            with pytest.raises(OSError):
                Path(pin["path"]).write_bytes(b"replacement")
    Path(pins[0]["path"]).write_bytes(b"abcde")
    with pytest.raises(IntegrityError, match="BOOTSTRAP_FILE_CHANGED"):
        FileLease({"schema": "strata/LaunchFileInventory/1", "files": pins, "trees": []})


@pytest.mark.parametrize("change", ["content", "truncated", "grown", "deadline", "nonempty", "quota"])
def test_invalid_sources_or_staging_cannot_publish_bundle_authority(tmp_path, monkeypatch, change):
    sources = sources_at(tmp_path / "source", [b"original"])
    path = Path(next(iter(sources.values())).path)
    if change in {"content", "truncated", "grown"}:
        path.write_bytes({"content": b"changed!", "truncated": b"short", "grown": b"too long!"}[change])
    output = tmp_path / "staging"
    output.mkdir()
    if change == "nonempty":
        (output / "retained").write_bytes(b"keep")
    if change == "quota":
        monkeypatch.setattr(staging, "MAX_PART", 7)
    deadline = time.monotonic() + (-1 if change == "deadline" else 10)
    with pytest.raises(Fault, match="WRITER_SOURCE_CHANGED|WRITER_STAGING_TIMEOUT|WRITER_STAGING_NOT_EMPTY|WRITER_BYTE_QUOTA"):
        staging.stage_bundles(output, sources, deadline)
    # Failed staging leaves evidence but closes every partial output handle.
    for partial in output.iterdir():
        with partial.open("ab"):
            pass


@pytest.fixture(scope="module")
def compiled_helper(tmp_path_factory):
    java, javac = os.environ.get("STRATA_WRITER_TEST_JAVA"), os.environ.get("STRATA_WRITER_TEST_JAVAC")
    if not java or not javac:
        pytest.skip("Explicit pinned Java/Javac required for copier component checks")
    classes = tmp_path_factory.mktemp("writer-classes")
    source = Path(__file__).parents[1] / "evaluator/java/StrataWriterPreparation.java"
    subprocess.run([javac, "-d", str(classes), str(source)], capture_output=True, check=True, timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    assert [path.name for path in classes.glob("*.class")] == ["StrataWriterPreparation.class"]
    return java, classes


@pytest.mark.parametrize("change", [None, "legacy", "gap", "overlap", "trailing", "content", "truncated",
    "escape", "duplicate_target", "oversize", "header", "revisit_bundle"])
def test_actual_java_copier_preserves_sources_and_rejects_malformed_bundle_ranges(
        tmp_path, monkeypatch, compiled_helper, change):
    java, classes = compiled_helper
    monkeypatch.setattr(staging, "MAX_PART", 8)
    sources = sources_at(tmp_path / "source", [b"12345", b"", b"abcdef", b"7890"])
    output, control, destination = (tmp_path / name for name in ("staging", "control", "destination"))
    for directory in (output, control, destination):
        directory.mkdir()
    pins, manifest, _ = staging.stage_bundles(output, sources, time.monotonic() + 10)
    lines = manifest.decode().splitlines()
    fields = [line.split("\t") for line in lines[1:]]
    if change in {"gap", "overlap"}:
        fields[1][4] = "6" if change == "gap" else "4"
    elif change in {"trailing", "content", "truncated"}:
        part = Path(pins[-1]["path"])
        part.write_bytes({"trailing": b"7890!", "content": b"bad!", "truncated": b"789"}[change])
    elif change == "escape":
        fields[0][0] = base64.b64encode(b"../escape").decode()
    elif change == "duplicate_target":
        fields[1][0] = fields[0][0]
    elif change == "oversize":
        fields[0][3] = str(512 * 1024**2 + 1)
    elif change == "revisit_bundle":
        fields[-1][1], fields[-1][4] = fields[0][1], "0"
    if change == "legacy":
        lines = ["\t".join([base64.b64encode(relative.encode()).decode(),
            base64.b64encode(pin.path.encode()).decode(), pin.sha256, str(pin.bytes)])
            for relative, pin in sorted(sources.items())]
    else:
        lines = ["unsupported" if change == "header" else lines[0], *["\t".join(row) for row in fields]]
    (control / "files.tsv").write_text("\n".join(lines), encoding="utf-8")
    challenge = "c" * 64
    for grant in ("prepare.grant", "finish.grant"):
        (control / grant).write_text(challenge, encoding="utf-8")
    result = subprocess.run([java, "-Xms16m", "-Xmx128m", "-XX:-UsePerfData", "-cp", str(classes),
        "StrataWriterPreparation", str(destination), str(control), challenge],
        capture_output=True, text=True, timeout=25,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if change in {None, "legacy"}:
        assert result.returncode == 0, result.stderr
        receipt = json.loads((control / "copied.json").read_bytes())
        assert receipt["files"] == 4 and receipt["bytes"] == 15 and receipt["challenge"] == challenge
        assert {path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file()} == set(sources)
        for relative, pin in sources.items():
            assert (destination / relative).read_bytes() == Path(pin.path).read_bytes()
    else:
        assert result.returncode != 0 and not (control / "copied.json").exists(), result.stdout
        assert "WRITER_" in result.stderr or "FileAlreadyExistsException" in result.stderr
    assert not (tmp_path / "escape").exists()
