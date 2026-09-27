"""Distinct observer build, synthetic lifecycle and actual noninitializing JVM checks."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from strata_evaluator.player_body_agent import SERVER_SHA, prepare_player_body_agent


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    asm, server = os.environ.get("STRATA_VANILLA_ASM"), os.environ.get("STRATA_VANILLA_SERVER_JAR")
    if not asm or not server:
        pytest.skip("explicit pinned installed ASM and official server required")
    server = Path(server)
    assert server.is_absolute() and hashlib.sha256(server.read_bytes()).hexdigest() == SERVER_SHA
    javac = Path(shutil.which("javac"))
    root = tmp_path_factory.mktemp("body-agent")
    receipt = prepare_player_body_agent(javac, Path(asm), root / "build")
    classes = root / "fixtures"
    classes.mkdir()
    result = subprocess.run([str(javac), "--release", "17", "-classpath", str(root / "build/classes"),
        "-d", str(classes), "tests/java/livebody/BodyAgentTest.java", "tests/java/livebody/RosterCaptureTest.java"],
        capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    return root, javac.with_name("java.exe" if os.name == "nt" else "java"), server, receipt


def test_same_tick_roster_identity_and_sticky_failure_cases(built):
    root, java, _, _ = built
    result = subprocess.run([str(java), "-cp", os.pathsep.join(map(str, (root / "fixtures", root / "build/classes"))),
        "io.github.opencnid.strata.livebody.RosterCaptureTest"], capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout.strip() == b"roster-callback-cases-pass"


@pytest.mark.parametrize("mode,exit_code,attach", [
    ("verify", 0, True), ("forged", 126, True), ("changed", 126, True), ("verify", None, False),
    ("foreign", 126, True), ("duplicate", 126, True),
    ("bad-roster", None, True), ("oversize-config", None, True),
])
def test_actual_jvm_instrumentation_and_refusals(built, tmp_path, mode, exit_code, attach):
    root, java, server, receipt = built
    config, output = tmp_path / "body.properties", tmp_path / "private-output"
    config.write_text("\n".join(["campaign_id=synthetic-callback", "epoch=1", "run_id=class-conformance",
        "roster=00000000-0000-0000-0000-000000000001", "server_jar=" + str(server), "output=" + str(output)])
        + "\n", encoding="utf-8")
    if mode == "bad-roster":
        config.write_text(config.read_text().replace("00000000-0000-0000-0000-000000000001", "1-1-1-1-1"), encoding="utf-8")
    if mode == "oversize-config":
        config.write_bytes(config.read_bytes() + b"x" * 16385)
    arguments = [str(java), "-Xmx256m", "-XX:-CreateCoredumpOnCrash"]
    if attach:
        arguments.append("-XX:+DisableAttachMechanism")
    arguments += ["-javaagent:" + str(root / "build/strata-private-body-0.1.0.jar") + "=" + str(config),
        "-cp", str(root / "fixtures"), "io.github.opencnid.strata.livebody.BodyAgentTest", mode, str(server)]
    result = subprocess.run(arguments, capture_output=True, timeout=45, cwd=tmp_path)
    (tmp_path / "stdout.log").write_bytes(result.stdout)
    (tmp_path / "stderr.log").write_bytes(result.stderr)
    (tmp_path / "invocation.json").write_text(json.dumps({"arguments": arguments, "exit_code": result.returncode}), encoding="utf-8")
    if exit_code is None:
        expected = {"bad-roster": b"BODY_ROSTER", "oversize-config": b"BODY_CONFIG"}.get(mode, b"BODY_AGENT_ARGUMENTS")
        assert result.returncode != 0 and expected in result.stderr
        assert not output.exists()
        return
    assert result.returncode == exit_code, result.stderr.decode()
    rows = [json.loads(line) for line in (output / "events.jsonl").read_bytes().splitlines()]
    assert len(rows) == 1 and rows[0]["body"]["schema"] == "strata/PrivateBodyStart/1"
    assert rows[0]["body"]["module_sha256"] == receipt["jar_sha256"]
    assert rows[0]["body"]["config_sha256"] == hashlib.sha256(config.read_bytes()).hexdigest()
    assert not list(output.glob("*.nbt"))
    if mode == "verify":
        assert b"actual-instrumented-methods-pass; no game initialization or player capture" in result.stdout
