"""Offline build of a distinct private vanilla player-body observer.

No launch, gameplay catalog, admission or runtime qualification is supplied.
"""

import hashlib
import io
from pathlib import Path
import subprocess
import zipfile

from mcbench.inference_transport import strict_json
from mcbench.inventory import file_hash
from mcbench.storage import canonical, reject_links, require
from mcbench.vanilla_clock import ASM_SHA, CLASS_PINS, ROOT

POLICY = "vanilla1192-private-roster-nbt/1"
SERVER_SHA = "d79def2f9aaf06d6b851e568150762b8e7ee24a898a314cf34b210cbd9ea14b6"


def _zip(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, raw in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return buffer.getvalue()


def prepare_player_body_agent(javac, asm, destination):
    javac, asm, destination = map(Path, (javac, asm, destination))
    for path in (javac, asm, destination):
        require(path.is_absolute(), "UNSAFE_PATH")
        reject_links(path)
    require(not destination.exists() and not destination.is_relative_to(ROOT), "BODY_BUILD_DESTINATION")
    compiler = strict_json((ROOT / "java/build-inputs.json").read_bytes())["compiler"]["javac_sha256"]
    require(file_hash(javac) == compiler and file_hash(asm) == ASM_SHA, "BODY_BUILD_INPUTS")
    sources = sorted((ROOT / "evaluator/java/livebody").glob("*.java"))
    require({p.name for p in sources} == {"PlayerNbt.java", "BodyAgent.java", "BodyObserver.java", "RosterCapture.java"},
            "BODY_BUILD_SOURCE")
    pins = {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sources}
    destination.mkdir(parents=True)
    classes = destination / "classes"
    classes.mkdir()
    result = subprocess.run([str(javac), "--release", "17", "-g:none", "-encoding", "UTF-8",
        "-classpath", str(asm), "-d", str(classes), *map(str, sources)], capture_output=True, timeout=60)
    (destination / "compiler.stdout").write_bytes(result.stdout)
    (destination / "compiler.stderr").write_bytes(result.stderr)
    require(result.returncode == 0, "BODY_BUILD_COMPILE")
    entries = {p.relative_to(classes).as_posix(): p.read_bytes() for p in classes.rglob("*.class")}
    require(entries and all(n.startswith("io/github/opencnid/strata/livebody/") for n in entries), "BODY_BUILD_CLASSES")
    callbacks = {n: raw for n, raw in entries.items() if not Path(n).name.startswith("BodyAgent")}
    entries = {n: raw for n, raw in entries.items() if n not in callbacks}
    entries["body-observer-callbacks.jar"] = _zip(callbacks)
    with zipfile.ZipFile(asm) as archive:
        entries.update({n: archive.read(n) for n in archive.namelist()
                        if n.startswith("org/objectweb/asm/") and n.endswith(".class")})
        entries["META-INF/strata-asm-manifest.mf"] = archive.read("META-INF/MANIFEST.MF")
    entries["META-INF/MANIFEST.MF"] = (
        "Manifest-Version: 1.0\r\nPremain-Class: io.github.opencnid.strata.livebody.BodyAgent\r\n"
        "Can-Redefine-Classes: false\r\nCan-Retransform-Classes: false\r\n\r\n").encode()
    jar = destination / "strata-private-body-0.1.0.jar"
    jar.write_bytes(_zip(entries))
    require(file_hash(javac) == compiler and file_hash(asm) == ASM_SHA
            and all(file_hash(ROOT / n) == sha for n, sha in pins.items()), "SOURCE_CHANGED")
    with zipfile.ZipFile(jar) as archive:
        require({n: archive.read(n) for n in archive.namelist()} == entries, "BODY_BUILD_CHANGED")
    receipt = {"schema": "strata/PrivatePlayerBodyAgent/1", "policy": POLICY,
        "jar_sha256": file_hash(jar), "jar_bytes": jar.stat().st_size, "compiler_sha256": compiler,
        "asm_sha256": ASM_SHA, "server_sha256": SERVER_SHA, "transform_class_pins": CLASS_PINS,
        "source_pins": pins, "entries": {n: hashlib.sha256(raw).hexdigest() for n, raw in entries.items()},
        "game_conformance_qualified": False, "live_state_verified": False, "native_probe_admission": False}
    (destination / "receipt.json").write_bytes(canonical(receipt))
    return receipt
