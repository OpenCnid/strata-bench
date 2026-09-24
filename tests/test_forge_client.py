"""Synthetic archives exercise selection and copying, not Minecraft startup."""

import copy
import hashlib
import io
import json
import zipfile

import pytest

from mcbench import forge_client as f
from mcbench.inventory import scan_tree
from mcbench.provisioning import PackProvider
from mcbench.storage import Fault


def jar(label):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
        archive.writestr("fixture.txt", label)
    return output.getvalue()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    base, libraries = tmp_path / "base", tmp_path / "libraries"
    base.mkdir()
    libraries.mkdir()
    def write(root, path, raw):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    def library(coordinate, root, prefix="", host="https://maven.minecraftforge.net/"):
        path = f._coordinate(coordinate)
        raw = jar(coordinate)
        write(root, prefix + path, raw)
        return {"name": coordinate, "downloads": {"artifact": {"path": path, "size": len(raw),
            "sha1": hashlib.sha1(raw).hexdigest(), "url": host + path}}}
    vanilla = {"libraries": [library(c, base, "libraries/", "https://libraries.minecraft.net/")
                             for c in ("example:replaced:1", "example:kept:1")]}
    version_raw = json.dumps(vanilla).encode()
    write(base, "versions/1.19.2/1.19.2.json", version_raw)
    write(base, "versions/1.19.2/1.19.2.jar", jar("vanilla"))
    write(base, "java/bin/java.exe", b"synthetic not executable")
    write(base, "assets/objects/fixture", b"synthetic asset")
    write(base, "assets/log_configs/client-1.12.xml", b"synthetic log config")
    official = {"_comment_": [], "id": "1.19.2-forge-43.4.23", "inheritsFrom": "1.19.2",
        "time": "2025-03-04T22:54:18+00:00", "releaseTime": "2025-03-04T22:54:18+00:00",
        "mainClass": "cpw.mods.bootstraplauncher.BootstrapLauncher", "logging": {},
        "libraries": [library(c, libraries) for c in ("example:replaced:2", "example:module:1")],
        "arguments": {"jvm": ["-DignoreList=fixture", "-p", "${library_directory}/example/module/1/module-1.jar"],
                      "game": ["--launchTarget", "forgeclient"]}}
    declared = official["libraries"] + [library(c, libraries) for c in f.LOADER_LIBRARIES]
    data = {}
    for variable, coordinate in [("MC_EXTRA", f"net.minecraft:client:{f.MC}:extra"),
                                 ("PATCHED", f"net.minecraftforge:forge:{f.FORGE}:client")]:
        raw = jar(coordinate)
        write(libraries, f._coordinate(coordinate), raw)
        data[variable] = {"client": "[" + coordinate + "]"}
        data[variable + "_SHA"] = {"client": "'" + hashlib.sha1(raw).hexdigest() + "'"}
    profile = {"minecraft": "1.19.2", "version": official["id"], "libraries": declared, "data": data}
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("install_profile.json", json.dumps(profile))
        archive.writestr("version.json", json.dumps(official))
    installer = output.getvalue()
    launcher = copy.deepcopy(official)
    launcher.pop("_comment_")
    launcher.pop("logging")
    launcher.update(id=f.VERSION, assets="1.19", minimumLauncherVersion=0)
    launcher["time"] = launcher["releaseTime"] = "2025-03-04T22:54:18Z"
    launcher["arguments"]["jvm"][0] += "," + f.VERSION
    for entry in launcher["libraries"]:
        a = entry["downloads"]["artifact"]
        a["url"] = "https://modloaders.forgecdn.net/647622546/maven/" + a["path"]
    launcher_raw = json.dumps(launcher).encode()
    monkeypatch.setattr(f, "INSTALLER_SHA256", sha(installer))
    monkeypatch.setattr(f, "LAUNCHER_SHA256", sha(launcher_raw))
    srg = jar("synthetic verified SRG")
    return dict(installer=installer, version_raw=version_raw, launcher_raw=launcher_raw,
        base_root=base, library_root=libraries, destination=tmp_path / "prepared",
        base_files=[r | {"role": "client", "origin": "synthetic source", "license_ref": "synthetic license"}
                    for r in scan_tree(base)], srg_raw=srg,
        srg_entry={"role": "client", "path": f"libraries/net/minecraft/client/{f.MC}/client-{f.MC}-srg.jar",
                   "digest": sha(srg), "bytes": len(srg), "origin": "synthetic derivation", "license_ref": "synthetic license"})


def test_exact_selection_copies_base_and_adds_runtime_without_launcher_state(inputs):
    (inputs["library_root"] / "unrelated-cache").write_bytes(b"not selected")
    result = f.prepare_client(**inputs)
    root = inputs["destination"]
    assert not (root / "libraries/example/replaced/1/replaced-1.jar").exists()
    assert (root / "libraries/example/replaced/2/replaced-2.jar").exists()
    assert (root / inputs["srg_entry"]["path"]).read_bytes() == inputs["srg_raw"]
    assert result["excluded_libraries"][0]["replacement"] == "example:replaced:2"
    assert len(result["classpath"]) == 4 and len(result["module_path"]) == 1
    assert len(result["loader_libraries"]) == 8
    assert all(r not in result["classpath"] for r in result["loader_libraries"])
    assert not result["complete_role_qualified"] and not result["license_review_complete"]
    assert not any("unrelated" in r["path"] for r in result["files"])
    (inputs["base_root"] / "assets/objects/fixture").write_bytes(b"changed after preparation")
    assert (root / "assets/objects/fixture").read_bytes() == b"synthetic asset"


def test_installed_launch_has_no_source_cache_or_credentials(inputs):
    result = f.prepare_client(**inputs)
    root = inputs["destination"]
    (root / "natives").mkdir()
    args = f.launch_arguments(root, result, server_port=25604)
    assert args[args.index("-cp") + 1].split(";") == [str(root / p) for p in result["classpath"]]
    assert args[args.index("-p") + 1].replace("\\", "/") == str(root / result["module_path"][0]).replace("\\", "/")
    assert args[args.index("--gameDir") + 1] == str(root)
    assert args[args.index("--accessToken") + 1] == "${auth_access_token}"
    assert args[-4:] == ["--server", "127.0.0.1", "--port", "25604"]
    assert "-Xmx6144m" in args and "-XX:ActiveProcessorCount=4" in args
    assert not any(str(inputs["library_root"]) in arg or str(inputs["base_root"]) in arg for arg in args)
    assert not any("gameBridge" in arg or "awaitGameAuthority" in arg for arg in args)


@pytest.mark.parametrize("change", ["classpath_order", "module", "changed_file", "missing_file",
                                   "duplicate_file", "escape", "missing_natives", "port", "metadata"])
def test_installed_launch_rejects_drift_or_unsafe_selection(inputs, change):
    result = f.prepare_client(**inputs)
    root = inputs["destination"]
    (root / "natives").mkdir()
    port = 25604
    if change == "classpath_order":
        result["classpath"].reverse()
    elif change == "module":
        result["module_path"] = []
    elif change == "changed_file":
        (root / "assets/objects/fixture").write_bytes(b"drift")
    elif change == "missing_file":
        (root / "java/bin/java.exe").unlink()
    elif change == "duplicate_file":
        result["files"].append(result["files"][0])
    elif change == "escape":
        result["files"][0]["path"] = "../outside"
    elif change == "missing_natives":
        (root / "natives").rmdir()
    elif change == "port":
        port = True
    else:
        path = root / f"versions/{f.VERSION}/{f.VERSION}.json"
        path.write_bytes(path.read_bytes() + b" ")
        for row in result["files"]:
            if row["path"] == path.relative_to(root).as_posix():
                row.update(digest=sha(path.read_bytes()), bytes=path.stat().st_size)
    with pytest.raises(Fault):
        f.launch_arguments(root, result, server_port=port)


@pytest.mark.parametrize("change", ["installer", "launcher", "base", "base_extra", "library", "generated", "srg", "role", "destination"])
def test_corrupt_missing_or_unqualified_inputs_fail_before_output(inputs, change):
    if change == "installer":
        inputs["installer"] += b"changed"
    elif change == "launcher":
        inputs["launcher_raw"] += b" "
    elif change == "base":
        (inputs["base_root"] / "assets/objects/fixture").write_bytes(b"changed")
    elif change == "base_extra":
        (inputs["base_root"] / "private-state").write_bytes(b"must not copy")
    elif change == "library":
        (inputs["library_root"] / "example/module/1/module-1.jar").unlink()
    elif change == "generated":
        (inputs["library_root"] / f._coordinate(f"net.minecraft:client:{f.MC}:extra")).write_bytes(b"changed")
    elif change == "srg":
        inputs["srg_raw"] += b"changed"
    elif change == "role":
        inputs["srg_entry"]["role"] = "server"
    else:
        inputs["destination"].mkdir()
    with pytest.raises(Fault):
        f.prepare_client(**inputs)
    assert inputs["destination"].exists() == (change == "destination")


def test_reviewed_metadata_digest_does_not_allow_arbitrary_jvm_change(inputs, monkeypatch):
    launcher = json.loads(inputs["launcher_raw"])
    launcher["arguments"]["jvm"].append("-Dunreviewed=true")
    inputs["launcher_raw"] = json.dumps(launcher).encode()
    monkeypatch.setattr(f, "LAUNCHER_SHA256", sha(inputs["launcher_raw"]))
    with pytest.raises(Fault, match="FORGE_LAUNCHER_METADATA_MISMATCH"):
        f.prepare_client(**inputs)
    assert not inputs["destination"].exists()


def test_changed_source_during_copy_retains_failure(inputs, monkeypatch):
    original = f.read_input
    def changing(path, limit):
        raw = original(path, limit)
        if path.name.endswith("-extra.jar"):
            (inputs["library_root"] / "example/module/1/module-1.jar").write_bytes(b"changed after validation")
        return raw
    monkeypatch.setattr(f, "read_input", changing)
    with pytest.raises(Fault, match="SOURCE_CHANGED"):
        f.prepare_client(**inputs)
    assert inputs["destination"].exists()
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        f.prepare_client(**inputs)


@pytest.mark.parametrize("change", [None, "unsealed", "receipt", "inventory", "lock", "artifact_request", "bytes"])
def test_provider_requires_same_acquisition_and_sealed_base(inputs, database, cas, tmp_path, monkeypatch, change):
    service = PackProvider(database, cas, simulation=True)
    inventory = service._put("vanilla", {"files": inputs["base_files"]})
    base = {"target": "vanilla", "state": "SEALED", "inventory": inventory, "sealed": "synthetic sealed lock"}
    request = {"target": "e9e", "state": "ACQUIRED", "receipt": "synthetic acquisition"}
    monkeypatch.setattr(service, "_row", lambda name, **kw: base if name == "vanilla" else request)
    monkeypatch.setattr(service, "_vanilla_distribution", lambda *args: (b"synthetic", inputs["version_raw"], {"request_id": "vanilla"}))
    output = inputs["srg_entry"]
    cas.put(service.principal, service.namespace("e9e"), "operator", inputs["srg_raw"],
            quota_bytes=service.quota, max_object_bytes=1024**2)
    derivation = {"schema": "strata/ForgeDerivedRuntime/1", "request_id": "e9e", "acquisition_receipt": request["receipt"],
        "base_inventory": inventory, "base_lock": base["sealed"], "installed_outputs_reproduced": True,
        "derived": [{"role": "client", "sha256": output["digest"], "bytes": output["bytes"], "runtime_path": output["path"]}]}
    if change in ("receipt", "inventory", "lock"):
        derivation[{"receipt": "acquisition_receipt", "inventory": "base_inventory", "lock": "base_lock"}[change]] = "wrong cohort"
    if change == "unsealed":
        base["state"] = "VERIFIED"
    if change == "bytes":
        derivation["derived"][0]["bytes"] += 1
    ref = service._put("e9e", derivation)
    artifacts = service._put("e9e", {"schema": "strata/ForgeRuntimeArtifacts/1", "request_id": "wrong" if change == "artifact_request" else "e9e",
                                     "is_example": True, "derivation": ref, "files": [output]})
    installer, launcher = tmp_path / "installer.jar", tmp_path / "launcher.json"
    installer.write_bytes(inputs["installer"])
    launcher.write_bytes(inputs["launcher_raw"])
    def run():
        return service.prepare_forge_client("e9e", "vanilla", installer, launcher, inputs["base_root"],
                                            inputs["library_root"], artifacts, inputs["destination"])
    if change:
        with pytest.raises(Fault):
            run()
        assert not inputs["destination"].exists()
    else:
        report = run()
        assert report["base_binding"]["inventory"] == inventory and report["derived_artifacts"] == artifacts
        assert report["inherited_license_namespace"] == "pack:vanilla"
