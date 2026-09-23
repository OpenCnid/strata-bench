"""Synthetic npm packages exercise offline byte verification; no npm/game execution."""

import base64
import hashlib
import io
import json
import tarfile

import pytest

from mcbench.npm_runtime import binary_paths, verify_installed_packages
from mcbench.storage import Fault


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def installed(tmp_path):
    root, cache, generated = (tmp_path / name for name in ("root", "cache", "generated"))
    root.mkdir()
    data = {"package.json": json.dumps({"name": "fixture", "version": "1.0.0", "license": "fixture"}).encode(),
            "cli.js": b"#!/usr/bin/env node\n// fixture", ".gitignore": b"fixture\n", "LICENSE": b"fixture"}
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for path, raw in data.items():
            member = tarfile.TarInfo("fixture prefix/" + path)
            member.size = len(raw)
            archive.addfile(member, io.BytesIO(raw))
    raw = stream.getvalue()
    sha = hashlib.sha512(raw).digest()
    archive_path = cache / sha.hex()[:2] / sha.hex()[2:4] / sha.hex()[4:]
    archive_path.parent.mkdir(parents=True)
    archive_path.write_bytes(raw)
    package = {"version": "1.0.0", "resolved": "https://registry.npmjs.org/fixture/-/fixture-1.0.0.tgz",
               "integrity": "sha512-" + base64.b64encode(sha).decode(), "bin": {"fixture": "cli.js"}}
    manifest = {"name": "test", "version": "1.0.0", "dependencies": {"fixture": "1.0.0"}}
    lock = {"name": "test", "version": "1.0.0", "lockfileVersion": 3,
            "packages": {"": manifest, "node_modules/fixture": package}}
    write_json(root / "package.json", manifest)
    write_json(root / "package-lock.json", lock)
    write_json(root / "node_modules/.package-lock.json", lock | {"packages": {"node_modules/fixture": package}})
    for path, raw in data.items():
        output = root / "node_modules/fixture" / (".npmignore" if path == ".gitignore" else path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(raw)
    for suffix in ("", ".cmd", ".ps1"):
        for directory in (root, generated):
            path = directory / ("node_modules/.bin/fixture" + suffix)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic reviewed shim " + suffix.encode())
    return root, cache, generated, archive_path


def test_complete_bytes_and_explicit_ignore_normalization(installed):
    report = verify_installed_packages(*installed[:3])
    assert len(report["packages"]) == 1 and len(report["files"]) == 8
    assert report["packages"][0]["files"][".npmignore"]["archive_path"] == "fixture prefix/.gitignore"
    assert report["generated_shims"] == {"node_modules/.bin/fixture": "node_modules/fixture/cli.js"}
    assert not report["campaign_admission"] and not report["license_qualification"]
    assert not report["writer_custody_qualified"]


@pytest.mark.parametrize("change", ["file", "missing", "cache", "shim", "generated", "hidden",
    "extra", "empty", "hardlink", "manifest", "version", "origin", "integrity", "collision", "traversal"])
def test_no_unreviewed_or_changed_installed_content(installed, change):
    root, cache, generated, archive_path = installed
    if change == "file":
        (root / "node_modules/fixture/cli.js").write_bytes(b"changed")
    elif change == "missing":
        (root / "node_modules/fixture/cli.js").unlink()
    elif change == "cache":
        archive_path.write_bytes(b"changed")
    elif change == "shim":
        (root / "node_modules/.bin/fixture.cmd").write_bytes(b"changed")
    elif change == "generated":
        (generated / "node_modules/.bin/fixture.ps1").write_bytes(b"changed")
    elif change == "hidden":
        write_json(root / "node_modules/.package-lock.json", {})
    elif change == "extra":
        (root / "node_modules/extra.js").write_bytes(b"unreviewed")
    elif change == "empty":
        (root / "node_modules/unreviewed").mkdir()
    elif change == "hardlink":
        (root.parent / "shared").hardlink_to(root / "node_modules/fixture/cli.js")
    elif change == "manifest":
        write_json(root / "package.json", {})
    else:
        lock = json.loads((root / "package-lock.json").read_bytes())
        package = lock["packages"]["node_modules/fixture"]
        if change == "version":
            package["version"] = "2.0.0"
        elif change == "origin":
            package["resolved"] = "https://unapproved.example/fixture.tgz"
        elif change == "integrity":
            package["integrity"] = "sha512-invalid"
        elif change == "collision":
            lock["packages"]["node_modules/other"] = dict(package)
        elif change == "traversal":
            package["bin"] = {"fixture": "../escape"}
        write_json(root / "package-lock.json", lock)
        write_json(root / "node_modules/.package-lock.json", lock | {
            "packages": {k: v for k, v in lock["packages"].items() if k}})
    with pytest.raises(Fault):
        verify_installed_packages(root, cache, generated)


def test_generated_input_cannot_be_the_installed_tree(installed):
    with pytest.raises(Fault, match="NPM_GENERATOR_OVERLAP"):
        verify_installed_packages(installed[0], installed[1], installed[0])


def test_scoped_and_nested_bin_locations():
    assert binary_paths({"node_modules/@scope/pkg": {"bin": {"first": "bin/run.js"}},
        "node_modules/@scope/pkg/node_modules/other": {"bin": "bin/run.js"}}) == {
        "node_modules/.bin/first": "node_modules/@scope/pkg/bin/run.js",
        "node_modules/@scope/pkg/node_modules/.bin/other": "node_modules/@scope/pkg/node_modules/other/bin/run.js"}


@pytest.mark.parametrize("case", ["symlink", "hardlink", "traversal", "duplicate", "quota"])
def test_lock_bound_unsafe_archives_still_reject(installed, case):
    import gzip
    root, cache, generated, _ = installed
    member = tarfile.TarInfo("package/file.js")
    if case == "symlink":
        member.type, member.linkname = tarfile.SYMTYPE, "target"
    elif case == "hardlink":
        member.type, member.linkname = tarfile.LNKTYPE, "target"
    elif case == "traversal":
        member.name = "package/../outside"
    elif case == "quota":
        member.size = 1024**3 + 1
    raw = gzip.compress(member.tobuf() + (member.tobuf() if case == "duplicate" else b"") + b"\0" * 1024)
    if case == "duplicate":
        # Let the first empty member match, so the second triggers collision.
        (root / "node_modules/fixture/file.js").write_bytes(b"")
    sha = hashlib.sha512(raw).digest()
    path = cache / sha.hex()[:2] / sha.hex()[2:4] / sha.hex()[4:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    lock = json.loads((root / "package-lock.json").read_bytes())
    lock["packages"]["node_modules/fixture"]["integrity"] = "sha512-" + base64.b64encode(sha).decode()
    write_json(root / "package-lock.json", lock)
    write_json(root / "node_modules/.package-lock.json", lock | {"packages": {k: v for k, v in lock["packages"].items() if k}})
    with pytest.raises(Fault, match="NPM_ARCHIVE_UNSAFE|UNSAFE_PATH|NPM_ARCHIVE_COLLISION|NPM_ARCHIVE_QUOTA"):
        verify_installed_packages(root, cache, generated)


@pytest.mark.parametrize("changed", [False, True])
def test_operator_command_retains_report_or_typed_refusal(installed, changed):
    from typer.testing import CliRunner
    from mcbench.cli import app
    if changed:
        (installed[0] / "node_modules/.bin/fixture.cmd").write_bytes(b"changed")
    result = CliRunner().invoke(app, ["pack", "inspect-npm-runtime", *map(str, installed[:3])])
    body = json.loads(result.stdout)
    if changed:
        assert result.exit_code == 2 and body == {"status": "blocked", "code": "NPM_SHIM_CHANGED", "started": False}
    else:
        assert result.exit_code == 0 and body["schema"] == "strata/NpmInstalledRuntime/1"
        assert not body["campaign_admission"] and len(body["files"]) == 8
