"""Reproduce required Forge SRG runtime files from exact publisher inputs.

This runs only the two pinned offline mapping processors in fresh output. It
does not execute the installer, acquire software, start Minecraft or edit an
installation. Installed outputs are comparison targets, never generator inputs.
"""

import hashlib
from contextlib import contextmanager
import os
import threading
import time
from pathlib import Path

from .forge_runtime import INSTALLER_SHA256, MC, MCP, _coordinate, read_input
from .inference_transport import strict_json
from .inventory import file_hash, scan_tree
from .launch_integrity import FileLease, IntegrityError, safe
from .processes import ManagedProcess
from .storage import Fault, canonical, reject_links, require
from .vanilla_artifacts import metadata
from .vanilla_runtime import _archive

POLICY = "forge43423-srg-derivation/1"
PROCESSORS = {
    "merge": ("net.minecraftforge:installertools:1.4.1", "net.minecraftforge.installertools.ConsoleTool"),
    "rename": ("net.minecraftforge:ForgeAutoRenamingTool:0.1.22:all", "net.minecraftforge.fart.Main"),
}


@contextmanager
def _held_files(inventory):
    try:
        with FileLease(inventory) as lease:
            yield lease
    except IntegrityError as error:
        raise Fault("FORGE_DERIVATION_INPUT_LEASE_FAILED") from error


def _pin(path):
    raw = read_input(path, 128 * 1024**2)
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def _checked(path, sha1, size=None):
    raw = read_input(path, 128 * 1024**2)
    require(hashlib.sha1(raw).hexdigest() == sha1 and (size is None or len(raw) == size),
            "FORGE_DERIVATION_SOURCE_MISMATCH")
    return raw


def prepare_inputs(installer, manifest_raw, version_raw, libraries: dict[str, Path]):
    require(set(libraries) == {"client", "server"}, "ROLE_MISMATCH")
    require(len(installer) <= 16 * 1024**2 and hashlib.sha256(installer).hexdigest() == INSTALLER_SHA256,
            "FORGE_INSTALLER_MISMATCH")
    sources = metadata(manifest_raw, version_raw)
    version = strict_json(version_raw)
    with _archive(installer, max_members=10000) as archive:
        profile = strict_json(archive.read("install_profile.json"))
    definitions = {entry["name"]: entry["downloads"]["artifact"] for entry in profile["libraries"]}
    processors = {}
    for name, (coordinate, main) in PROCESSORS.items():
        found = [p for p in profile["processors"] if p["jar"] == coordinate and
                 (name != "merge" or p["args"][:2] == ["--task", "MERGE_MAPPING"])]
        require(len(found) == 1, "FORGE_PROCESSOR_MISMATCH")
        processors[name] = found[0] | {"main": main}
    require(processors["merge"]["args"] == ["--task", "MERGE_MAPPING", "--left", "{MAPPINGS}",
        "--right", "{MOJMAPS}", "--output", "{MERGED_MAPPINGS}", "--classes", "--reverse-right"] and
        processors["rename"]["args"] == ["--input", "{MC_SLIM}", "--output", "{MC_SRG}", "--names",
        "{MERGED_MAPPINGS}", "--ann-fix", "--ids-fix", "--src-fix", "--record-fix"], "FORGE_PROCESSOR_MISMATCH")
    retained, roles = {}, {}
    for role, root in libraries.items():
        require(root.is_absolute() and root == root.resolve(), "UNSAFE_PATH")
        reject_links(root)
        classpaths = {}
        for name, processor in processors.items():
            selected = []
            for coordinate in [processor["jar"], *processor["classpath"]]:
                entry = definitions[coordinate]
                require(entry["path"] == _coordinate(coordinate), "FORGE_METADATA_INVALID")
                path = root / entry["path"]
                raw = _checked(path, entry["sha1"], entry["size"])
                retained[str(path)] = _pin(path)
                selected.append(str(path))
                if coordinate == processor["jar"]:
                    with _archive(raw, max_members=50000) as archive:
                        manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8").replace("\r\n", "\n")
                        require("Main-Class: " + processor["main"] + "\n" in manifest, "FORGE_PROCESSOR_MISMATCH")
            classpaths[name] = selected
        mcp_path = root / (MCP + ".zip")
        mcp = definitions[f"de.oceanlabs.mcp:mcp_config:{MC}@zip"]
        raw = _checked(mcp_path, mcp["sha1"], mcp["size"])
        retained[str(mcp_path)] = _pin(mcp_path)
        with _archive(raw, max_members=50000) as archive:
            member = strict_json(archive.read("config.json"))["data"]["mappings"]
            require(member == "config/joined.tsrg", "FORGE_METADATA_INVALID")
            mapping = archive.read(member)
        mapping_path = root / (MCP + "-mappings.txt")
        require(read_input(mapping_path, 16 * 1024**2) == mapping, "FORGE_DERIVATION_SOURCE_MISMATCH")
        retained[str(mapping_path)] = _pin(mapping_path)
        slim_path = root / _coordinate(profile["data"]["MC_SLIM"][role][1:-1])
        _checked(slim_path, profile["data"]["MC_SLIM_SHA"][role][1:-1])
        retained[str(slim_path)] = _pin(slim_path)
        maps_path = root / _coordinate(profile["data"]["MOJMAPS"][role][1:-1])
        maps = version["downloads"][role + "_mappings"]
        require(maps["url"] == f"https://piston-data.mojang.com/v1/objects/{maps['sha1']}/{role}.txt",
                "FORGE_METADATA_INVALID")
        _checked(maps_path, maps["sha1"], maps["size"])
        retained[str(maps_path)] = _pin(maps_path)
        srg_path = root / _coordinate(profile["data"]["MC_SRG"][role][1:-1])
        merged_path = root / _coordinate(profile["data"]["MERGED_MAPPINGS"][role][1:-1])
        # Compare with the stopped installed outputs, but do not pass these to
        # either generator. Hash equality must be established by reproduction.
        expected = {"merged": _pin(merged_path), "srg": _pin(srg_path)}
        retained.update({r["path"]: r for r in expected.values()})
        roles[role] = {"inputs": {"MAPPINGS": str(mapping_path), "MOJMAPS": str(maps_path),
                                  "MC_SLIM": str(slim_path)}, "classpaths": classpaths,
                       "installed_comparison": expected,
                       "runtime_path": "libraries/" + srg_path.relative_to(root).as_posix()}
    return {"policy": POLICY, "installer_sha256": INSTALLER_SHA256, "source_verification": sources,
            "processors": processors, "roles": roles, "files": list(retained.values())}


def _run(argv, root, environment, label):
    process, threads, errors = None, [], []
    started = time.monotonic()
    result = {"argv": argv, "max_wall_s": 120, "result": "fail"}
    try:
        process = ManagedProcess(argv, root, environment, "")
        def drain(stream, name):
            try:
                total = 0
                with (root / (label + "." + name)).open("xb") as output:
                    while data := stream.read(65536):
                        total += len(data)
                        require(total <= 4 * 1024**2, "FORGE_DERIVATION_LOG_QUOTA")
                        output.write(data)
            except Exception as error:
                errors.append(type(error).__name__)
        for name in ("stdout", "stderr"):
            thread = threading.Thread(target=drain, args=(getattr(process.process, name), name), daemon=True)
            thread.start()
            threads.append(thread)
        while process.poll() is None:
            require(not errors, "FORGE_DERIVATION_LOG_FAILED")
            require(time.monotonic() - started <= 120, "FORGE_DERIVATION_TIMEOUT")
            time.sleep(.02)
        result["exit_code"] = process.poll()
        for thread in threads:
            thread.join(2)
        require(not errors and not any(t.is_alive() for t in threads), "FORGE_DERIVATION_LOG_FAILED")
        require(result["exit_code"] == 0, "FORGE_DERIVATION_PROCESS_FAILED")
        require(process.job is not None, "FORGE_DERIVATION_PROCESS_ACTIVE")
        drain_started = time.monotonic()
        while True:
            result["process_accounting"] = process.job.accounting()
            if result["process_accounting"]["active_processes"] == 0:
                break
            require(time.monotonic() - drain_started <= 2, "FORGE_DERIVATION_PROCESS_ACTIVE")
            time.sleep(.01)
        result["terminal_reconciliation_ms"] = (time.monotonic() - drain_started) * 1000
        result["result"] = "pass"
    finally:
        if process is not None:
            if process.poll() is None:
                process.stop()
            process.close()
            for thread in threads:
                thread.join(2)
        result["elapsed_s"] = time.monotonic() - started
        with (root / (label + ".json")).open("xb") as output:
            output.write(canonical(result))
    return result


def derive(plan, java_root: Path, java_files, destination: Path):
    """Caller binds Java file rows to a sealed inventory, never an untrusted plan.

    Windows held-file leases and owned jobs bound this selected execution. Other
    platforms require their own runtime qualification; this is not isolation.
    """
    require(os.name == "nt", "FORGE_DERIVATION_PLATFORM")
    require(java_root.is_absolute() and destination.is_absolute(), "UNSAFE_PATH")
    for path in (java_root, destination):
        reject_links(path)
        require(path == path.resolve(), "UNSAFE_PATH")
    require(not destination.exists(), "DESTINATION_EXISTS")
    require(not destination.is_relative_to(java_root) and not java_root.is_relative_to(destination), "UNSAFE_PATH")
    require(scan_tree(java_root, max_files=1024, max_bytes=512 * 1024**2) == java_files, "FORGE_JAVA_INVENTORY_MISMATCH")
    require(any(r["path"] == "bin/java.exe" for r in java_files), "FORGE_JAVA_INVENTORY_MISMATCH")
    pins = plan["files"] + [{"path": str(java_root / r["path"]), "sha256": r["digest"], "bytes": r["bytes"]}
                            for r in java_files]
    require(all(not Path(r["path"]).is_relative_to(destination) for r in pins), "UNSAFE_PATH")
    inventory = {"schema": "strata/LaunchFileInventory/1",
                 "files": [r | {"path": str(safe(r["path"]))} for r in pins],
                 "trees": [{"path": str(safe(java_root)),
                            "files": sorted(str(safe(java_root / r["path"])) for r in java_files)}]}
    with _held_files(inventory) as lease:
        destination.mkdir(parents=True, exist_ok=False)
        (destination / "temp").mkdir()
        environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
        environment.update(TEMP=str(destination / "temp"), TMP=str(destination / "temp"))
        with (destination / "plan.json").open("xb") as output:
            output.write(canonical(plan | {"java_inventory": inventory}))
        results, derived = [], []
        for role in ("client", "server"):
            item = plan["roles"][role]
            values = item["inputs"] | {"MERGED_MAPPINGS": str(destination / (role + "-merged.txt")),
                                       "MC_SRG": str(destination / (role + "-srg.jar"))}
            for name in ("merge", "rename"):
                processor = plan["processors"][name]
                args = [values.get(value[1:-1], value) if value.startswith("{") else value
                        for value in processor["args"]]
                argv = [str(java_root / "bin/java.exe"), "-Xmx1024m", "-XX:ActiveProcessorCount=4",
                        "-Djava.io.tmpdir=" + str(destination / "temp"), "-cp",
                        os.pathsep.join(item["classpaths"][name]), processor["main"], *args]
                results.append(_run(argv, destination, environment, role + "-" + name))
            for kind, output in (("merged", values["MERGED_MAPPINGS"]), ("srg", values["MC_SRG"])):
                actual = _pin(Path(output))
                expected = item["installed_comparison"][kind]
                require(all(actual[k] == expected[k] for k in ("sha256", "bytes")), "FORGE_DERIVATION_OUTPUT_MISMATCH")
            derived.append({"role": role, **_pin(Path(values["MC_SRG"])), "runtime_path": item["runtime_path"]})
        lease.recheck()
        report = {"schema": "strata/ForgeDerivedRuntime/1", "policy": POLICY,
                  "installer_sha256": INSTALLER_SHA256, "plan_sha256": file_hash(destination / "plan.json"),
                  "derived": derived, "processes": results, "installed_outputs_reproduced": True,
                  "complete_role_qualified": False, "game_conformance_claim": None}
        with (destination / "result.json").open("xb") as output:
            output.write(canonical(report))
    return report
