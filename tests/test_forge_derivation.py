"""Synthetic mapping inputs and owned process faults, never Minecraft evidence."""

import hashlib
import io
import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

from mcbench import forge_derivation as d
from mcbench.inventory import scan_tree
from mcbench.storage import Fault
from test_provisioning import prepare_fixture


def sha(raw, kind="sha256"):
    return hashlib.new(kind, raw).hexdigest()


def jar(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, raw in entries.items():
            archive.writestr(name, raw)
    return buffer.getvalue()


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    definitions, data, processors, contents = [], {}, [], {}
    def library(coordinate, raw):
        path = d._coordinate(coordinate)
        contents[path] = raw
        definitions.append({"name": coordinate, "downloads": {"artifact": {
            "path": path, "sha1": sha(raw, "sha1"), "size": len(raw), "url": "https://example.invalid/" + path}}})
    mcp = jar({"config.json": json.dumps({"data": {"mappings": "config/joined.tsrg"}}),
               "config/joined.tsrg": b"mapping"})
    library(f"de.oceanlabs.mcp:mcp_config:{d.MC}@zip", mcp)
    library("example:dependency:1", b"synthetic dependency")
    for name, (coordinate, main) in d.PROCESSORS.items():
        library(coordinate, jar({"META-INF/MANIFEST.MF": "Main-Class: " + main + "\n"}))
        args = (["--task", "MERGE_MAPPING", "--left", "{MAPPINGS}", "--right", "{MOJMAPS}",
                 "--output", "{MERGED_MAPPINGS}", "--classes", "--reverse-right"] if name == "merge" else
                ["--input", "{MC_SLIM}", "--output", "{MC_SRG}", "--names", "{MERGED_MAPPINGS}",
                 "--ann-fix", "--ids-fix", "--src-fix", "--record-fix"])
        processors.append({"jar": coordinate, "classpath": ["example:dependency:1"], "args": args})
    roots, downloads = {}, {}
    for role in ("client", "server"):
        root = roots[role] = tmp_path / role
        files = dict(contents)
        files[d.MCP + "-mappings.txt"] = b"mapping"
        for variable, coordinate, raw in [
            ("MC_SLIM", f"net.minecraft:{role}:{d.MC}:slim", (role + "-slim").encode()),
            ("MOJMAPS", f"net.minecraft:{role}:{d.MC}:mappings@txt", (role + "-mojmaps").encode()),
            ("MC_SRG", f"net.minecraft:{role}:{d.MC}:srg", (role + "-srg").encode()),
            ("MERGED_MAPPINGS", f"de.oceanlabs.mcp:mcp_config:{d.MC}:mappings-merged@txt", (role + "-merged").encode())]:
            files[d._coordinate(coordinate)] = raw
            data.setdefault(variable, {})[role] = f"[{coordinate}]"
            if variable == "MC_SLIM":
                data.setdefault("MC_SLIM_SHA", {})[role] = f"'{sha(raw, 'sha1')}'"
            if variable == "MOJMAPS":
                downloads[role + "_mappings"] = {"size": len(raw), "sha1": sha(raw, "sha1"),
                    "url": f"https://piston-data.mojang.com/v1/objects/{sha(raw, 'sha1')}/{role}.txt"}
        downloads[role] = {"size": 1, "sha1": sha(b"x", "sha1"),
                          "url": f"https://piston-data.mojang.com/v1/objects/{sha(b'x', 'sha1')}/{role}.jar"}
        for path, raw in files.items():
            p = root / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
    installer = jar({"install_profile.json": json.dumps({"libraries": definitions, "data": data, "processors": processors})})
    monkeypatch.setattr(d, "INSTALLER_SHA256", sha(installer))
    version = json.dumps({"id": "1.19.2", "type": "release", "javaVersion": {"majorVersion": 17}, "downloads": downloads}).encode()
    manifest = json.dumps({"versions": [{"id": "1.19.2", "type": "release", "sha1": sha(version, "sha1"),
        "url": f"https://piston-meta.mojang.com/v1/packages/{sha(version, 'sha1')}/1.19.2.json"}]}).encode()
    return {"installer": installer, "manifest_raw": manifest, "version_raw": version, "libraries": roots}


def test_plan_binds_fixed_processors_and_keeps_comparison_outputs_out_of_inputs(inputs):
    plan = d.prepare_inputs(**inputs)
    for role in ("client", "server"):
        item = plan["roles"][role]
        assert set(item["inputs"]) == {"MAPPINGS", "MOJMAPS", "MC_SLIM"}
        assert not set(item["inputs"].values()) & {r["path"] for r in item["installed_comparison"].values()}
        assert item["runtime_path"].endswith(f"/{role}-{d.MC}-srg.jar")
    assert set(plan["processors"]) == {"merge", "rename"}


@pytest.mark.parametrize("kind", ["installer", "version_raw"])
def test_changed_authoritative_metadata_rejects(inputs, kind):
    inputs[kind] += b" "
    with pytest.raises(Fault):
        d.prepare_inputs(**inputs)


@pytest.mark.parametrize("path", [d.MCP + ".zip", d.MCP + "-mappings.txt",
    f"net/minecraft/client/{d.MC}/client-{d.MC}-slim.jar",
    f"net/minecraft/client/{d.MC}/client-{d.MC}-mappings.txt",
    d._coordinate("net.minecraftforge:ForgeAutoRenamingTool:0.1.22:all")])
def test_changed_processor_inputs_reject(inputs, path):
    (inputs["libraries"]["client"] / path).write_bytes(b"wrong bytes")
    with pytest.raises(Fault):
        d.prepare_inputs(**inputs)


@pytest.mark.skipif(os.name != "nt", reason="Selected held-file/owned-job profile is Windows")
@pytest.mark.parametrize("wrong_output", [False, True])
def test_derivation_compares_reproduced_outputs_and_retains_failure(inputs, tmp_path, monkeypatch, wrong_output):
    plan = d.prepare_inputs(**inputs)
    java = tmp_path / "java"
    (java / "bin").mkdir(parents=True)
    (java / "bin/java.exe").write_bytes(b"synthetic no-execution fixture")
    rows = scan_tree(java)
    def run(argv, root, environment, label):
        role, step = label.split("-")
        path = Path(argv[argv.index("--output") + 1])
        path.write_bytes((role + ("-merged" if step == "merge" else "-srg")).encode() + (b"wrong" if wrong_output else b""))
        return {"result": "pass", "synthetic": True}
    monkeypatch.setattr(d, "_run", run)
    output = tmp_path / "derived"
    if wrong_output:
        with pytest.raises(Fault, match="FORGE_DERIVATION_OUTPUT_MISMATCH"):
            d.derive(plan, java, rows, output)
        assert output.exists() and not (output / "result.json").exists()
    else:
        report = d.derive(plan, java, rows, output)
        assert report["installed_outputs_reproduced"] and len(report["derived"]) == 2
        assert not report["complete_role_qualified"]
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        d.derive(plan, java, rows, output)


@pytest.mark.skipif(os.name != "nt", reason="Selected owned-job accounting is Windows")
@pytest.mark.parametrize("exit_code", [0, 3])
def test_owned_processor_lifecycle_logs_and_failure(tmp_path, exit_code):
    environment = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
    argv = [sys.executable, "-c", f"print('synthetic processor');raise SystemExit({exit_code})"]
    if exit_code:
        with pytest.raises(Fault, match="FORGE_DERIVATION_PROCESS_FAILED"):
            d._run(argv, tmp_path, environment, "fixture")
    else:
        result = d._run(argv, tmp_path, environment, "fixture")
        assert result["process_accounting"]["active_processes"] == 0
    report = json.loads((tmp_path / "fixture.json").read_bytes())
    assert report["result"] == ("fail" if exit_code else "pass")
    assert (tmp_path / "fixture.stdout").read_bytes().strip() == b"synthetic processor"


@pytest.fixture
def importable(database, cas, tmp_path):
    service, receipt, *_ = prepare_fixture(database, cas, tmp_path)
    receipt_ref = service.import_acquisition_receipt(receipt)
    roles, outputs = {}, []
    for role in ("client", "server"):
        source = tmp_path / (role + "-srg.jar")
        raw = (role + " synthetic derived bytes").encode()
        source.write_bytes(raw)
        runtime = f"libraries/net/minecraft/{role}/{d.MC}/{role}-{d.MC}-srg.jar"
        pin = {"sha256": sha(raw), "bytes": len(raw)}
        roles[role] = {"runtime_path": runtime, "installed_comparison": {"srg": pin}}
        outputs.append(pin | {"role": role, "path": str(source), "runtime_path": runtime})
    plan = service._put("pack1", {"policy": d.POLICY, "installer_sha256": d.INSTALLER_SHA256, "roles": roles})
    result = {"schema": "strata/ForgeDerivedRuntime/1", "policy": d.POLICY,
              "installer_sha256": d.INSTALLER_SHA256, "request_id": "pack1",
              "acquisition_receipt": receipt_ref, "plan_ref": plan, "plan_sha256": plan[11:],
              "installed_outputs_reproduced": True, "derived": outputs,
              "processes": [{"result": "pass", "exit_code": 0,
                             "process_accounting": {"active_processes": 0}} for _ in range(4)]}
    return service, result


def test_import_consumes_bytes_and_is_idempotent(importable):
    service, result = importable
    ref = service._put("pack1", result)
    imported = service.import_forge_runtime("pack1", ref)
    assert service.import_forge_runtime("pack1", ref) == imported
    assert not imported["complete_role_qualified"]
    for row in imported["files"]:
        raw = service.cas.read(service.principal, service.namespace("pack1"), "cas:sha256:" + row["digest"])
        assert sha(raw) == row["digest"] and row["origin"].startswith("strata:derived:" + ref)


@pytest.mark.parametrize("change", ["receipt", "request", "failed", "active", "malformed", "second_file"])
def test_import_rejects_before_any_artifact_import(importable, monkeypatch, change):
    service, result = importable
    if change == "receipt":
        result["acquisition_receipt"] = "cas:sha256:" + "0" * 64
    elif change == "request":
        result["request_id"] = "other"
    elif change == "failed":
        result["processes"][0]["exit_code"] = 1
    elif change == "active":
        result["processes"][0]["process_accounting"]["active_processes"] = 1
    elif change == "malformed":
        result["processes"][0]["process_accounting"] = None
    else:
        Path(result["derived"][1]["path"]).write_bytes(b"changed second output")
    ref = service._put("pack1", result)
    def unexpected(*args, **kwargs):
        pytest.fail("Rejected derivation must not import either artifact")
    monkeypatch.setattr(service.cas, "put_file", unexpected)
    with pytest.raises(Fault):
        service.import_forge_runtime("pack1", ref)
