"""Compose the selected Forge client software without launcher state or execution.

The caller supplies the original sealed vanilla inventory and acquired SRG
artifact. Only reviewed metadata transformations and named libraries are used.
This prepares software; vendor content, settings and launch remain separate.
"""

import copy
import hashlib
from pathlib import Path

from .forge_runtime import FORGE, INSTALLER_SHA256, INSTALLER_URL, MC, _coordinate, read_input
from .inference_transport import strict_json
from .inventory import file_hash, scan_tree
from .storage import require, reject_links, safe_relative
from .vanilla_client import _libraries, _path
from .vanilla_runtime import _archive, _license_metadata

POLICY = "e9e1270-forge43423-client-software/1"
LAUNCHER_SHA256 = "b7f241fa462def6a7fb8d4aa4f17e27fba4bdac7354bba2af43ce91b89eb980f"
VERSION = "forge-43.4.23"
MAX_TOTAL = 2 * 1024**3
LOADER_LIBRARIES = [f"net.minecraftforge:{name}:{FORGE}" for name in
                    ("fmlcore", "javafmllanguage", "lowcodelanguage", "mclanguage")]
LOADER_LIBRARIES.append(f"net.minecraftforge:forge:{FORGE}:universal")
LAUNCH_POLICY = "e9e1270-installed-client-config/1"
ROLE_ROOT = "{strata.role_root}"


def launch_arguments(root: Path, software, *, server_port: int):
    """Resolve the prepared software into credential-free Windows arguments.

    The operator must bind ``software`` to its retained preparation receipt and
    hold the returned installation paths for execution. This read-only resolver
    neither authenticates nor launches, and does not qualify the complete role.
    """
    _path(root)
    require(root.is_dir() and not any(c in str(root) for c in ';\r\n\x00${}'), "UNSAFE_PATH")
    require(type(server_port) is int and 1024 <= server_port <= 65535, "FORGE_CLIENT_PORT")
    require(software.get("schema") == "strata/ForgeClientSoftware/1"
            and software.get("policy") == POLICY
            and software.get("launcher_metadata_sha256") == LAUNCHER_SHA256,
            "FORGE_CLIENT_SOFTWARE_MISMATCH")
    files = software.get("files")
    require(isinstance(files, list) and 0 < len(files) <= 21000, "FORGE_CLIENT_SOFTWARE_MISMATCH")
    seen = set()
    for row in files:
        relative = safe_relative(row["path"])
        require(relative.parts[0] in {"assets", "java", "libraries", "versions"}
                and row["path"].casefold() not in seen, "FORGE_CLIENT_SOFTWARE_MISMATCH")
        seen.add(row["path"].casefold())
        path = root / relative
        require(file_hash(path) == row["digest"] and path.stat().st_size == row["bytes"]
                and path.stat().st_nlink == 1, "FORGE_CLIENT_SOFTWARE_MISMATCH")
    reject_links(root / "natives")
    require((root / "natives").is_dir(), "FORGE_CLIENT_NATIVES")
    return _arguments(root, software,
        read_input(root / f"versions/{VERSION}/{VERSION}.json", 1024**2),
        read_input(root / "versions/1.19.2/1.19.2.json", 1024**2), server_port=server_port)


def argument_template(software, launcher_raw, vanilla_raw, *, server_port):
    """Credential-free, relocatable form; caller binds all input bytes to CAS."""
    return _arguments(Path(ROLE_ROOT), software, launcher_raw, vanilla_raw, server_port=server_port)


def _arguments(root, software, launcher_raw, vanilla_raw, *, server_port):
    require(type(server_port) is int and 1024 <= server_port <= 65535, "FORGE_CLIENT_PORT")
    require(software.get("schema") == "strata/ForgeClientSoftware/1"
            and software.get("policy") == POLICY
            and software.get("launcher_metadata_sha256") == LAUNCHER_SHA256,
            "FORGE_CLIENT_SOFTWARE_MISMATCH")
    require(hashlib.sha256(launcher_raw).hexdigest() == LAUNCHER_SHA256, "FORGE_LAUNCHER_METADATA_MISMATCH")
    metadata = strict_json(launcher_raw)
    vanilla, _ = _libraries(strict_json(vanilla_raw))
    seen = {row["path"].casefold() for row in software["files"]}
    # Re-derive ordering from pinned metadata; a reordered receipt is not a
    # license to change class resolution or select a different native library.
    def identity(name):
        return tuple(name.split(":")[:2] + name.split(":")[3:])
    replacements = {identity(row["name"]) for row in metadata["libraries"]}
    classpath = ["libraries/" + _coordinate(row["name"]) for row in metadata["libraries"]]
    classpath += [row["path"] for row in vanilla if identity(row["coordinate"]) not in replacements]
    classpath += [f"versions/{VERSION}/{VERSION}.jar"]
    jvm = metadata["arguments"]["jvm"]
    require(jvm.count("-p") == 1, "FORGE_METADATA_INVALID")
    modules = jvm[jvm.index("-p") + 1].split("${classpath_separator}")
    require(all(p.startswith("${library_directory}/") for p in modules), "FORGE_METADATA_INVALID")
    modules = ["libraries/" + p.removeprefix("${library_directory}/") for p in modules]
    require(software.get("classpath") == classpath and software.get("module_path") == modules
            and set(p.casefold() for p in classpath + modules + [
                "java/bin/java.exe", "assets/log_configs/client-1.12.xml",
                "versions/1.19.2/1.19.2.json", f"versions/{VERSION}/{VERSION}.json"
            ]) <= seen, "FORGE_RUNTIME_INVENTORY_MISMATCH")
    substitutions = {"${library_directory}": str(root / "libraries"), "${classpath_separator}": ";",
                     "${version_name}": VERSION}
    resolved = []
    for arg in jvm:
        for key, value in substitutions.items():
            arg = arg.replace(key, value)
        require("${" not in arg, "FORGE_METADATA_INVALID")
        resolved.append(arg)
    return ["-XX:ActiveProcessorCount=4", "-Dmax.bg.threads=1", "-Xms512m", "-Xmx6144m",
            "-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump",
            "-Dos.name=Windows 10", "-Dos.version=10.0", "-Djava.library.path=" + str(root / "natives"),
            "-Dminecraft.launcher.brand=strata-operator-installed-bootstrap",
            "-Dminecraft.launcher.version=development-1", "-cp",
            ";".join(str(root / p) for p in classpath), *resolved,
            "-Dlog4j.configurationFile=" + str(root / "assets/log_configs/client-1.12.xml"),
            metadata["mainClass"], "--username", "${auth_player_name}", "--version", VERSION,
            "--gameDir", str(root), "--assetsDir", str(root / "assets"), "--assetIndex", "1.19",
            "--uuid", "${auth_uuid}", "--accessToken", "${auth_access_token}",
            "--clientId", "", "--xuid", "", "--userType", "msa", "--versionType", "release",
            "--width", "854", "--height", "480", *metadata["arguments"]["game"],
            "--server", "127.0.0.1", "--port", str(server_port)]


def launcher_metadata(official, raw):
    """Exact retained CurseForge transformations; arbitrary JVM changes reject."""
    require(hashlib.sha256(raw).hexdigest() == LAUNCHER_SHA256, "FORGE_LAUNCHER_METADATA_MISMATCH")
    expected = copy.deepcopy(official)
    require(expected["id"] == "1.19.2-forge-43.4.23" and expected["inheritsFrom"] == "1.19.2"
            and expected["mainClass"] == "cpw.mods.bootstraplauncher.BootstrapLauncher", "FORGE_RELEASE_MISMATCH")
    expected.pop("_comment_")
    require(expected.pop("logging") == {}, "FORGE_LAUNCHER_METADATA_MISMATCH")
    expected.update(id=VERSION, assets="1.19", minimumLauncherVersion=0)
    for key in ("time", "releaseTime"):
        require(expected[key].endswith("+00:00"), "FORGE_LAUNCHER_METADATA_MISMATCH")
        expected[key] = expected[key][:-6] + "Z"
    args = expected["arguments"]["jvm"]
    indices = [i for i, arg in enumerate(args) if isinstance(arg, str) and arg.startswith("-DignoreList=")]
    require(len(indices) == 1, "FORGE_LAUNCHER_METADATA_MISMATCH")
    args[indices[0]] += "," + VERSION
    for entry in expected["libraries"]:
        artifact = entry["downloads"]["artifact"]
        artifact["url"] = "https://modloaders.forgecdn.net/647622546/maven/" + artifact["path"]
    actual = strict_json(raw)
    require(actual == expected, "FORGE_LAUNCHER_METADATA_MISMATCH")
    return actual


def prepare_client(installer, version_raw, launcher_raw, base_root: Path, base_files,
                   library_root: Path, srg_raw, srg_entry, destination: Path):
    for path in (base_root, library_root, destination):
        _path(path)
    require(not destination.exists(), "DESTINATION_EXISTS")
    require(all(not destination.is_relative_to(p) and not p.is_relative_to(destination)
                for p in (base_root, library_root)), "UNSAFE_PATH")
    require(hashlib.sha256(installer).hexdigest() == INSTALLER_SHA256, "FORGE_INSTALLER_MISMATCH")
    with _archive(installer, max_members=10000) as archive:
        profile = strict_json(archive.read("install_profile.json"))
        official = strict_json(archive.read("version.json"))
    launcher = launcher_metadata(official, launcher_raw)
    require(profile["minecraft"] == "1.19.2" and profile["version"] == official["id"], "FORGE_RELEASE_MISMATCH")
    expected_base = sorted(({k: r[k] for k in ("path", "digest", "bytes")} for r in base_files), key=lambda r: r["path"])
    require(scan_tree(base_root, max_files=21000, max_bytes=MAX_TOTAL) == expected_base, "FORGE_BASE_INVENTORY_MISMATCH")
    require(all(r["role"] == "client" and r["path"].split("/")[0] in {"assets", "java", "libraries", "versions"}
                for r in base_files), "FORGE_BASE_INVENTORY_MISMATCH")
    base = {r["path"]: r for r in base_files}
    require(file_hash(base_root / "versions/1.19.2/1.19.2.json") == hashlib.sha256(version_raw).hexdigest(),
            "FORGE_BASE_INVENTORY_MISMATCH")
    vanilla, _ = _libraries(strict_json(version_raw))
    require({r["path"] for r in vanilla} == {p for p in base if p.startswith("libraries/")}, "FORGE_BASE_INVENTORY_MISMATCH")
    # Group/artifact/classifier identity, not filename coincidence, selects overrides.
    def identity(name):
        return tuple(name.split(":")[:2] + name.split(":")[3:])
    replacements = {identity(r["name"]): r["name"] for r in official["libraries"]}
    excluded = [base[r["path"]] | {"disposition": "superseded_by_forge", "replacement": replacements[identity(r["coordinate"])]}
                for r in vanilla if identity(r["coordinate"]) in replacements]
    excluded_paths = {r["path"] for r in excluded}
    files = [r | {"source_path": str(base_root / r["path"]), "provenance": "sealed_vanilla_inventory"}
             for r in base_files if r["path"] not in excluded_paths]
    selected = set(r["path"] for r in files)
    definitions = {r["name"]: r for r in profile["libraries"]}
    definitions.update({r["name"]: r for r in official["libraries"]})
    declared = [r["name"] for r in official["libraries"]] + LOADER_LIBRARIES
    require(len(declared) == len(set(declared)), "FORGE_METADATA_INVALID")
    forge_paths = []

    def add(path, raw, origin, source=None, **extra):
        require(path not in selected and path.casefold() not in {p.casefold() for p in selected}, "PATH_COLLISION")
        selected.add(path)
        row = {"path": path, "digest": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
               "origin": origin, **extra}
        if source is not None:
            row["source_path"] = str(source)
        files.append(row)
        return row

    for coordinate in declared:
        artifact = definitions[coordinate]["downloads"]["artifact"]
        path = _coordinate(coordinate)
        require(artifact["path"] == path and artifact["url"].startswith("https://"), "FORGE_METADATA_INVALID")
        source = library_root / path
        raw = read_input(source, 128 * 1024**2)
        require(len(raw) == artifact["size"] and hashlib.sha1(raw).hexdigest() == artifact["sha1"], "FORGE_FILE_MISMATCH")
        add("libraries/" + path, raw, artifact["url"], source, coordinate=coordinate,
            provenance="forge_publisher_library", license_review="pending")
        forge_paths.append("libraries/" + path)
    for variable in ("MC_EXTRA", "PATCHED"):
        coordinate = profile["data"][variable]["client"]
        require(coordinate.startswith("[") and coordinate.endswith("]"), "FORGE_METADATA_INVALID")
        path = _coordinate(coordinate[1:-1])
        source = library_root / path
        raw = read_input(source, 128 * 1024**2)
        require(profile["data"][variable + "_SHA"]["client"] == "'" + hashlib.sha1(raw).hexdigest() + "'", "FORGE_FILE_MISMATCH")
        add("libraries/" + path, raw, INSTALLER_URL + "#" + variable, source,
            provenance="forge_publisher_processor_output", license_review="pending")
    runtime = f"libraries/net/minecraft/client/{MC}/client-{MC}-srg.jar"
    require(srg_entry["role"] == "client" and srg_entry["path"] == runtime and
            srg_entry["bytes"] == len(srg_raw) and srg_entry["digest"] == hashlib.sha256(srg_raw).hexdigest(),
            "FORGE_DERIVATION_UNQUALIFIED")
    add(runtime, srg_raw, srg_entry["origin"], provenance="reproduced_srg", license_ref=srg_entry["license_ref"])
    alias = f"versions/{VERSION}/{VERSION}.jar"
    vanilla_jar = base_root / "versions/1.19.2/1.19.2.jar"
    add(alias, read_input(vanilla_jar, 128 * 1024**2), base["versions/1.19.2/1.19.2.jar"]["origin"], vanilla_jar,
        provenance="sealed_vanilla_alias", license_ref=base["versions/1.19.2/1.19.2.jar"]["license_ref"])
    metadata_path = f"versions/{VERSION}/{VERSION}.json"
    add(metadata_path, launcher_raw, "strata:reviewed-curseforge-metadata:" + LAUNCHER_SHA256,
        provenance="reviewed_launcher_transformation", license_review="pending")
    classpath = forge_paths[:len(official["libraries"])] + [r["path"] for r in vanilla if r["path"] not in excluded_paths] + [alias]
    args = launcher["arguments"]["jvm"]
    require(args.count("-p") == 1, "FORGE_METADATA_INVALID")
    modules = args[args.index("-p") + 1].split("${classpath_separator}")
    require(all(p.startswith("${library_directory}/") for p in modules), "FORGE_METADATA_INVALID")
    modules = ["libraries/" + p.removeprefix("${library_directory}/") for p in modules]
    require(set(classpath + modules) <= selected, "FORGE_RUNTIME_INVENTORY_MISMATCH")
    require(sum(r["bytes"] for r in files) <= MAX_TOTAL, "ARTIFACT_QUOTA")
    # All source selection/validation precedes writes. Never overwrite or reuse output.
    destination.mkdir(parents=True, exist_ok=False)
    generated = {runtime: srg_raw, metadata_path: launcher_raw}
    for row in files:
        target = destination / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            if "source_path" in row:
                source = Path(row["source_path"])
                reject_links(source)
                require(source.stat().st_nlink == 1, "UNSAFE_PATH")
                total = 0
                with source.open("rb") as stream:
                    while chunk := stream.read(1024**2):
                        total += len(chunk)
                        require(total <= row["bytes"], "SOURCE_CHANGED")
                        output.write(chunk)
            else:
                output.write(generated[row["path"]])
        require(target.stat().st_size == row["bytes"] and file_hash(target) == row["digest"], "SOURCE_CHANGED")
        if row.get("license_review") == "pending" and target.suffix == ".jar":
            row["license_metadata"], row["archive_notes"] = _license_metadata(target.read_bytes())
    require(scan_tree(base_root, max_files=21000, max_bytes=MAX_TOTAL) == expected_base, "SOURCE_CHANGED")
    for row in files:
        if "source_path" in row:
            require(file_hash(Path(row["source_path"])) == row["digest"], "SOURCE_CHANGED")
    expected = sorted(({k: r[k] for k in ("path", "digest", "bytes")} for r in files), key=lambda r: r["path"])
    require(scan_tree(destination, max_files=21000, max_bytes=MAX_TOTAL) == expected, "FORGE_RUNTIME_INVENTORY_MISMATCH")
    return {"schema": "strata/ForgeClientSoftware/1", "policy": POLICY, "software_root": str(destination),
            "files": sorted(files, key=lambda r: r["path"]), "excluded_libraries": excluded,
            "classpath": classpath, "module_path": modules, "loader_libraries": forge_paths[len(official["libraries"]):] +
            [runtime, "libraries/" + _coordinate(profile["data"]["MC_EXTRA"]["client"][1:-1]),
             "libraries/" + _coordinate(profile["data"]["PATCHED"]["client"][1:-1])],
            "installer_sha256": INSTALLER_SHA256, "launcher_metadata_sha256": LAUNCHER_SHA256,
            "independent_software_copy_verified": True, "complete_role_qualified": False,
            "license_review_complete": False, "launch_configuration_qualified": False,
            "game_conformance_claim": None}
