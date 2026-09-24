"""Real isolated JVMs with synthetic snapshot bodies; no game or network."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

from mcbench.runtime_data import ROOT, SOURCES, prepare_runtime_data, validate_sources, validate_snapshot
from mcbench.storage import Fault, canonical


def jdk():
    home = os.environ.get("JAVA_HOME")
    candidate = Path(home) / "bin/javac.exe" if home else Path("C:/Program Files/Eclipse Adoptium/jdk-17.0.20.101-hotspot/bin/javac.exe")
    if not candidate.is_file():
        found = shutil.which("javac")
        if not found:
            pytest.skip("JDK 17 unavailable")
        candidate = Path(found).resolve()
    return candidate


@pytest.fixture
def inputs(tmp_path):
    result = []
    for name, (repo, path) in SOURCES.items():
        p = tmp_path / name
        raw = b'# fixture\nexample:block\n' if name.endswith('.txt') else b'{"tag":"synthetic"}\n'
        p.write_bytes(raw)
        result.append({"name": name, "path": str(p), "sha256": hashlib.sha256(raw).hexdigest(),
            "commit": "a" * 40, "url": f"https://raw.githubusercontent.com/{repo}/{'a' * 40}/{path}"})
    return result


@pytest.mark.parametrize("change", ["hash", "branch", "foreign", "duplicate", "missing", "unknown", "nul", "quota"])
def test_invalid_snapshot_inputs_fail_before_compilation(inputs, tmp_path, change):
    if change == "hash":
        inputs[0]["sha256"] = "b" * 64
    elif change == "branch":
        inputs[0]["url"] = inputs[0]["url"].replace("a" * 40, "main")
    elif change == "foreign":
        inputs[0]["url"] = inputs[0]["url"].replace("raw.githubusercontent.com", "example.com")
    elif change == "duplicate":
        inputs[-1] = inputs[0]
    elif change == "missing":
        inputs.pop()
    elif change == "unknown":
        inputs[0]["extra"] = True
    else:
        raw = b"bad\0input" if change == "nul" else b"x" * (1024**2 + 1)
        Path(inputs[0]["path"]).write_bytes(raw)
        inputs[0]["sha256"] = hashlib.sha256(raw).hexdigest()
    destination = tmp_path / "output"
    with pytest.raises(Fault):
        prepare_runtime_data(inputs, jdk(), destination)
    assert not destination.exists()


@pytest.fixture
def built(inputs, tmp_path):
    output = tmp_path / "output"
    compiler = jdk()
    result = prepare_runtime_data(inputs, compiler, output)
    jar = output / "strata-runtime-data-0.1.0.jar"
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    subprocess.run([str(compiler), "--release", "17", "-cp", str(jar), "-d", str(fixture),
        str(ROOT / "tests/fixtures/RuntimeDataFixture.java")], capture_output=True, timeout=30, check=True)
    java = compiler.with_name("java.exe" if os.name == "nt" else "java")
    def run(*args, target=jar, flags=()):
        return subprocess.run([str(java), *flags, "-javaagent:" + str(target), "-cp", str(fixture) + os.pathsep + str(target),
            "io.github.opencnid.strata.fixed.RuntimeDataFixture", *args], cwd=tmp_path,
            capture_output=True, text=True, timeout=15)
    return result, jar, run


def test_snapshot_agent_delivers_exact_http_shaped_bytes_without_network(built, inputs):
    result, jar, run = built
    process = run()
    assert process.returncode == 0, process.stderr
    assert "FIXED_DATA_FIXTURE_PASS 18" in process.stdout
    assert "STRATA_FIXED_DATA_READY/1 " + result["index_sha256"] in process.stderr
    for row in inputs:
        assert row["name"] + " " + row["sha256"] in process.stdout
    assert result["installed"] is False and result["game_conformance_qualified"] is False
    assert result["all_runtime_downloads_qualified"] is False
    with zipfile.ZipFile(jar) as archive:
        assert len(archive.namelist()) == 9
        assert all(archive.read("strata-fixed/" + name) == raw for name, raw in validate_sources(inputs)[0].items())


def test_snapshot_manifest_cannot_admit_an_unreviewed_class_even_with_new_hash(built, tmp_path):
    report, jar, _ = built
    changed = tmp_path / "unreviewed.jar"
    with zipfile.ZipFile(jar) as source, zipfile.ZipFile(changed, "x") as output:
        for name in source.namelist():
            output.writestr(name.replace("Handler$1.class", "Unreviewed.class"), source.read(name))
    raw = changed.read_bytes()
    report = report | {"jar_sha256": hashlib.sha256(raw).hexdigest(), "jar_bytes": len(raw)}
    with pytest.raises(Fault, match="RUNTIME_DATA_SNAPSHOT"):
        validate_snapshot(canonical(report), raw)


@pytest.mark.parametrize("change", ["body", "index", "occupied_handler", "class_drift"])
def test_agent_refuses_corrupt_resources_and_never_falls_back_to_original_downloader(built, tmp_path, change):
    _, jar, run = built
    if change in {"body", "index"}:
        changed = tmp_path / "changed.jar"
        with zipfile.ZipFile(jar) as source, zipfile.ZipFile(changed, "x") as output:
            for name in source.namelist():
                raw = source.read(name)
                if name == ("strata-fixed/whitelist.txt" if change == "body" else "strata-fixed/index.txt"):
                    raw += b"changed"
                output.writestr(name, raw)
        process = run(target=changed)
        assert process.returncode != 0
        assert "FIXED_DATA_HASH" in process.stderr or "FIXED_DATA_INDEX" in process.stderr
    elif change == "occupied_handler":
        process = run(flags=("-Djava.protocol.handler.pkgs=occupied",))
        assert process.returncode != 0 and "FIXED_DATA_HANDLER_OCCUPIED" in process.stderr
    else:
        process = run("drift")
        assert process.returncode == 126 and "STRATA_FIXED_DATA_REFUSED/1" in process.stderr
    assert "FIXED_DATA_FIXTURE_PASS" not in process.stdout


def test_preparation_does_not_replace_existing_output(inputs, tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    sentinel = output / "keep"
    sentinel.write_text("prior evidence")
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        prepare_runtime_data(inputs, jdk(), output)
    assert sentinel.read_text() == "prior evidence"
