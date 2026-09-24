"""Prepare an offline snapshot agent for exact E9E runtime data consumers.

Inputs are operator-acquired immutable publisher URLs, not automatic downloads.
The output remains a new, uninstalled harness addition until profile admission.
"""

import hashlib
import io
from pathlib import Path
import re
import subprocess
import zipfile

from .inventory import file_hash
from .storage import canonical, reject_links, require

LEGACY_POLICY = "e9e1270-runtime-data-snapshot/1"
EXTENDED_POLICY = "e9e1270-runtime-data-snapshot/2"
POLICY = "e9e1270-runtime-data-snapshot/3"
LEGACY_SOURCES = {
    "whitelist.txt": ("Porting-Dead-Mods/Cable-Facades", "configs/whitelist.txt"),
    "blacklist.txt": ("Porting-Dead-Mods/Cable-Facades", "configs/blacklist.txt"),
    "contributorRevolvers.json": ("BluSunrize/ImmersiveEngineering", "contributorRevolvers.json"),
}
EXTENDED_SOURCES = LEGACY_SOURCES | {
    "ars-supporters.json": ("baileyholl/Ars-Nouveau", "supporters.json"),
    "supplementaries-credits.json": ("MehVahdJukaar/Supplementaries", "credits.json"),
}
SOURCES = EXTENDED_SOURCES | {
    "kiwi-contributors.json": ("Snownee/Kiwi", "contributors.json"),
    "quark-contributors.properties": ("VazkiiMods/Quark", "contributors.properties"),
    "industrial-contributors.json": ("Buuz135/Industrial-Foregoing", "contributors.json"),
}
CLASSES = {
    "com/portingdeadmods/cable_facades/CFConfig": "1ab0dee01c531ff6a89fd85aee2109f5e8036d342e0c283e76a9101b0aab8092",
    "blusunrize/immersiveengineering/ImmersiveEngineering$ThreadContributorSpecialsDownloader":
        "b47bfd98a885800760e9e7d7c24d60ec2d4e89da6cbc1ed9ad1e82a46283e2fb",
}
ADDED_CLASSES = {
    "com/hollingsworth/arsnouveau/setup/reward/Rewards": "79806bf34b647acc318e0ce0348f24b26fc4ac35d73e6d327976772a341a42a3",
    "net/mehvahdjukaar/supplementaries/common/utils/Credits": "f1b57b79214f42dbf7693645e62fe2ff15ca5944503b7671cc08948825b38df7",
}
REWARD_CLASSES = {
    "snownee/kiwi/contributor/impl/KiwiTierProvider": "16f2505174fcf123aa8d671517d932aa8e7b277313af8075123a2bfa35ec2557",
    "vazkii/quark/base/handler/ContributorRewardHandler$ThreadContributorListLoader":
        "6853ffed6b7763eaea5bad8bbacc7df24704eab1d7e06099a57707bc3ee75338",
    "com/buuz135/industrial/IndustrialForegoing": "e225e2107cd4ec42fe06f1aa40c520801a6a9b506e01b26a04803a5dd21a9ce1",
    "com/buuz135/sushigocrafting/SushiGoCrafting": "cc3e4161ef0914297e440a4a757a454cd40b12239c63f4e43ba6697794c59c7c",
}
SERVER_REWARD_CLASSES = REWARD_CLASSES | {
    "snownee/kiwi/contributor/impl/KiwiTierProvider": "3704088d89c1c60f3387a3ea2c4fe73bd613ce45cde6c66d332927be2ac265e8",
    "com/buuz135/industrial/IndustrialForegoing": "0de36bb1a4fcd62a46f277e64964699a7f0653e24545d44d141ee1fc0b25045d",
}
SNAPSHOTS = {
    LEGACY_POLICY: ("strata/RuntimeDataSnapshot/1", LEGACY_SOURCES, CLASSES),
    EXTENDED_POLICY: ("strata/RuntimeDataSnapshot/2", EXTENDED_SOURCES, CLASSES | ADDED_CLASSES),
    POLICY: ("strata/RuntimeDataSnapshot/3", SOURCES, CLASSES | ADDED_CLASSES | REWARD_CLASSES),
}
ROOT = Path(__file__).resolve().parents[2]
JAVA_ROOT = ROOT / "java/runtime-data/src"
MANIFEST = ("Manifest-Version: 1.0\r\nPremain-Class: io.github.opencnid.strata.fixed.Agent\r\n"
            "Can-Redefine-Classes: false\r\nCan-Retransform-Classes: false\r\n\r\n").encode("ascii")
AGENT_PATH = "harness/strata-runtime-data-0.1.0.jar"
ADDED_REMOTE_MODS = {"mods/ars_nouveau-1.19.2-3.23.0.jar", "mods/supplementaries-1.19.2-2.4.20.jar"}
REWARD_REMOTE_MODS = {"mods/Kiwi-1.19.2-forge-8.3.6.jar", "mods/Quark-3.4-418.jar",
                      "mods/industrial-foregoing-1.19.2-3.3.2.4-9.jar", "mods/sushigocrafting-1.19.2-0.3.8.jar"}
REMOTE_MODS = {"mods/cable_facades-1.19.2-Forge-1.2.2.jar",
               "mods/ImmersiveEngineering-1.19.2-9.2.4-170.jar"} | ADDED_REMOTE_MODS | REWARD_REMOTE_MODS
CLASS_ENTRIES = {"io/github/opencnid/strata/fixed/" + name for name in
                 ("Agent.class", "Data.class", "stratafixed/Handler.class", "stratafixed/Handler$1.class")}


def _raw(path, maximum):
    require(path.is_absolute(), "UNSAFE_PATH")
    reject_links(path)
    require(path.is_file() and path.stat().st_nlink == 1 and path.stat().st_size <= maximum,
            "RUNTIME_DATA_INPUT")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, "RUNTIME_DATA_QUOTA")
    return raw


def validate_sources(rows):
    require(isinstance(rows, list) and len(rows) == len(SOURCES), "RUNTIME_DATA_SOURCES")
    bodies, checked = {}, []
    for row in rows:
        require(set(row) == {"name", "path", "sha256", "url", "commit"}
                and row["name"] in SOURCES and row["name"] not in bodies, "RUNTIME_DATA_SOURCES")
        repo, relative = SOURCES[row["name"]]
        require(isinstance(row["commit"], str) and re.fullmatch(r"[0-9a-f]{40}", row["commit"])
                and row["url"] == f"https://raw.githubusercontent.com/{repo}/{row['commit']}/{relative}",
                "RUNTIME_DATA_ORIGIN")
        raw = _raw(Path(row["path"]), 1024**2)
        require(hashlib.sha256(raw).hexdigest() == row["sha256"], "HASH_MISMATCH")
        # Preserve exact publisher bytes. This only rejects invalid encoding/NUL;
        # the original mods remain responsible for parsing and rule semantics.
        raw.decode("utf-8")
        require(b"\0" not in raw, "RUNTIME_DATA_INPUT")
        bodies[row["name"]] = raw
        checked.append(row | {"bytes": len(raw)})
    return bodies, checked


def validate_snapshot(report_raw, jar_raw):
    """Check sealed resource bytes; never follow archived source filesystem paths."""
    from .inference_transport import strict_json
    report = strict_json(report_raw)
    require(isinstance(report.get("policy"), str) and report["policy"] in SNAPSHOTS, "RUNTIME_DATA_SNAPSHOT")
    schema, sources, _ = SNAPSHOTS[report["policy"]]
    require(report.get("schema") == schema
            and report.get("jar_sha256") == hashlib.sha256(jar_raw).hexdigest()
            and report.get("jar_bytes") == len(jar_raw) <= 1024**2, "RUNTIME_DATA_SNAPSHOT")
    with zipfile.ZipFile(io.BytesIO(jar_raw)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) == len(CLASS_ENTRIES) + 2 + len(sources)
                and set(names) == CLASS_ENTRIES | {"META-INF/MANIFEST.MF", "strata-fixed/index.txt"}
                    | {"strata-fixed/" + n for n in sources}
                and sum(e.file_size for e in archive.infolist()) <= 4 * 1024**2, "RUNTIME_DATA_SNAPSHOT")
        entries = {n: archive.read(n) for n in names}
    require(entries.get("META-INF/MANIFEST.MF") == MANIFEST
            and report.get("entries") == [{"path": n, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
                                          for n, raw in sorted(entries.items())], "RUNTIME_DATA_SNAPSHOT")
    inputs = report.get("inputs")
    require(isinstance(inputs, list) and len(inputs) == len(sources)
            and {r.get("name") for r in inputs} == set(sources), "RUNTIME_DATA_SNAPSHOT")
    for row in inputs:
        repo, path = sources[row["name"]]
        require(isinstance(row.get("commit"), str) and re.fullmatch(r"[0-9a-f]{40}", row["commit"])
                and row.get("url") == f"https://raw.githubusercontent.com/{repo}/{row['commit']}/{path}",
                "RUNTIME_DATA_ORIGIN")
        raw = entries.get("strata-fixed/" + row["name"])
        require(raw is not None and hashlib.sha256(raw).hexdigest() == row["sha256"]
                and len(raw) == row["bytes"], "RUNTIME_DATA_SNAPSHOT")
    index = "".join(hashlib.sha256(entries["strata-fixed/" + n]).hexdigest() + " " + n + "\n"
                    for n in sorted(sources)).encode("ascii")
    require(entries.get("strata-fixed/index.txt") == index
            and report.get("index_sha256") == hashlib.sha256(index).hexdigest(), "RUNTIME_DATA_SNAPSHOT")
    return report


def prepare_runtime_data(rows, javac: Path, destination: Path):
    bodies, checked = validate_sources(rows)
    require(destination.is_absolute() and javac.is_absolute(), "UNSAFE_PATH")
    reject_links(destination)
    reject_links(javac)
    require(not destination.exists(), "DESTINATION_EXISTS")
    for path in [javac, ROOT, *(Path(r["path"]) for r in checked)]:
        require(not path.is_relative_to(destination) and not destination.is_relative_to(path), "UNSAFE_PATH")
    compiler_sha = file_hash(javac)
    source_files = sorted(JAVA_ROOT.rglob("*.java"))
    require(len(source_files) == 3, "RUNTIME_DATA_SOURCE_INVENTORY")
    source_pins = {p.relative_to(ROOT).as_posix(): hashlib.sha256(_raw(p, 65536)).hexdigest() for p in source_files}
    version = subprocess.run([str(javac), "-version"], capture_output=True, text=True, timeout=15, check=True)
    require(re.fullmatch(r"javac 17(?:\.[0-9]+)*(?:\+[0-9]+)?\s*", version.stdout), "RUNTIME_DATA_JDK")
    destination.mkdir(parents=True)
    classes = destination / "classes"
    classes.mkdir()
    compiled = subprocess.run([str(javac), "--release", "17", "-g:none", "-encoding", "UTF-8",
        "-d", str(classes), *(str(p) for p in source_files)], capture_output=True, timeout=60)
    (destination / "compiler.stdout").write_bytes(compiled.stdout)
    (destination / "compiler.stderr").write_bytes(compiled.stderr)
    require(compiled.returncode == 0, "RUNTIME_DATA_COMPILE")
    index = "".join(hashlib.sha256(bodies[n]).hexdigest() + " " + n + "\n" for n in sorted(bodies)).encode("ascii")
    entries = {"META-INF/MANIFEST.MF": MANIFEST, "strata-fixed/index.txt": index}
    entries.update({"strata-fixed/" + name: raw for name, raw in bodies.items()})
    entries.update({p.relative_to(classes).as_posix(): _raw(p, 65536) for p in classes.rglob("*.class")})
    require(set(entries) == CLASS_ENTRIES | {"META-INF/MANIFEST.MF", "strata-fixed/index.txt"}
            | {"strata-fixed/" + n for n in SOURCES}, "RUNTIME_DATA_CLASS_INVENTORY")
    jar = destination / "strata-runtime-data-0.1.0.jar"
    with zipfile.ZipFile(jar, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(entries.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, raw)
    require(validate_sources(rows)[0] == bodies and file_hash(javac) == compiler_sha, "SOURCE_CHANGED")
    require(all(file_hash(ROOT / p) == sha for p, sha in source_pins.items()), "SOURCE_CHANGED")
    with zipfile.ZipFile(jar) as archive:
        require({name: archive.read(name) for name in archive.namelist()} == entries, "HASH_MISMATCH")
    result = {"schema": "strata/RuntimeDataSnapshot/3", "policy": POLICY,
        "inputs": checked, "source_pins": source_pins, "javac_sha256": compiler_sha,
        "javac_version": version.stdout.strip(), "jar_sha256": file_hash(jar), "jar_bytes": jar.stat().st_size,
        "index_sha256": hashlib.sha256(index).hexdigest(), "entries": [
            {"path": n, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)} for n, raw in sorted(entries.items())],
        "installed": False, "game_conformance_qualified": False, "all_runtime_downloads_qualified": False,
        "historical_download_bytes_recovered": False, "campaign_admission": False}
    # More admitted bodies must not create a receipt the bounded consumer rejects.
    validate_snapshot(canonical(result), _raw(jar, 1024**2))
    with (destination / "preparation.json").open("xb") as stream:
        stream.write(canonical(result))
    return result


def inspect_runtime_data_log(raw, report, *, role="server"):
    """Require the role's exact class forms and actual reads, not startup alone."""
    require(len(raw) <= 16 * 1024**2 and b"STRATA_FIXED_DATA_REFUSED/1" not in raw
            and b"STRATA_FIXED_DATA_JOURNAL_REFUSED/1" not in raw, "RUNTIME_DATA_EXECUTION")
    lines = [line[line.index("STRATA_FIXED_DATA_"):] for line in raw.decode("utf-8", errors="strict").splitlines()
             if "STRATA_FIXED_DATA_" in line]
    require("STRATA_FIXED_DATA_READY/1 " + report["index_sha256"] in lines, "RUNTIME_DATA_EXECUTION")
    require(isinstance(report.get("policy"), str) and report["policy"] in SNAPSHOTS, "RUNTIME_DATA_EXECUTION")
    require(role in {"client", "server"}, "RUNTIME_DATA_ROLE")
    _, sources, classes = SNAPSHOTS[report["policy"]]
    if report["policy"] == POLICY and role == "server":
        classes = classes | SERVER_REWARD_CLASSES
    require(len(report["inputs"]) == len(sources) and {r["name"] for r in report["inputs"]} == set(sources),
            "RUNTIME_DATA_EXECUTION")
    required = {"STRATA_FIXED_DATA_BOUND/1 " + name + " " + sha for name, sha in classes.items()}
    required.add("STRATA_FIXED_DATA_READY/1 " + report["index_sha256"])
    required.update("STRATA_FIXED_DATA_READ/1 " + r["name"] + " " + r["sha256"] for r in report["inputs"])
    require(required == set(lines), "RUNTIME_DATA_EXECUTION")
    return {**({"role": role} if report["policy"] == POLICY else {}),
            "policy": report["policy"], "jar_sha256": report["jar_sha256"],
            "index_sha256": report["index_sha256"], "bound_classes": sorted(classes),
            "read_inputs": [{"name": r["name"], "sha256": r["sha256"]} for r in report["inputs"]],
            "all_runtime_downloads_qualified": False}


def inspect_runtime_data_journal(path: Path, report, *, process_id: int, role="server"):
    """Inspect a stopped, privately held process's own bounded agent journal.

    The caller separately binds the process, role and snapshot artifact. This is not
    a signed producer, scoring authority or isolation qualification.
    """
    require(type(process_id) is int and process_id > 0, "RUNTIME_DATA_PROCESS")
    require(re.fullmatch(rf"strata-fixed-{process_id}-[0-9a-f]{{8}}(?:-[0-9a-f]{{4}}){{3}}-[0-9a-f]{{12}}\.log",
                         path.name), "RUNTIME_DATA_PROCESS")
    raw = _raw(path, 1024**2)
    require(raw.endswith(b"\n") and 0 < len(raw.splitlines()) <= 32
            and all(line.startswith(b"STRATA_FIXED_DATA_") and len(line) < 131072
                    for line in raw.splitlines()), "RUNTIME_DATA_JOURNAL")
    result = inspect_runtime_data_log(raw, report, role=role)
    require(raw == _raw(path, 1024**2), "SOURCE_CHANGED")
    return result | {"journal": {"name": path.name, "process_id": process_id,
                                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}}
