"""Fixed private E9E role/consumer evidence; never a gameplay capability.

Records loader metadata and selected getters, with exact pinned producer inputs.
Neither metadata matching nor stdout parsing grants profile/scoring authority.
"""

import hashlib
import io
from pathlib import PurePosixPath
import re
import tomllib
import zipfile

from mcbench.inference_transport import strict_json
from mcbench.inventory import file_hash
from mcbench.pack_modes import _read
from mcbench.storage import reject_links, require, safe_relative

PINS = {
    "mods/create-1.19.2-0.5.1.i.jar":
        "1bf5cca0903de37ed488084509a15b4960f2bd499e00b3fd715ac213e690ad46",
    "mods/sophisticatedcore-1.19.2-0.6.4.730.jar":
        "0de1a4c730674ad9f27611fa17b866f7ca5dca15841854d64867693c2a5862fe",
    "config/configswapper/expert/serverconfig/create-server.toml":
        "0954ef9b6df34a5f00948bd9e940039bfea5c281269c0bdce31e5eadad7c62bf",
}
MARKER = "STRATA_E9E_ROLE_CONTROL "
CURRENT = [
    (["logistics", "defaultExtractionTimer"], 8),
    (["schematics", "schematicannon", "schematicannonShotsPerGunpowder"], 400),
    (["schematics", "schematicannon", "schematicannonDelay"], 10),
]
LEGACY = [
    ["logistics", "defaultExtractionLimit"],
    ["schematics", "schematicannon", "schematicannonGunpowderWorth"],
    ["schematics", "schematicannon", "schematicannonFuelUsage"],
]
CONFIGS = {
    "bhmenu-client.toml": None, "nomoreworldsettings-client.toml": None,
    "inventorysorter-server.toml": None, "sophisticatedcore-server.toml": None,
    "sophisticatedcore-common.toml": ("sophisticatedcore", "COMMON"),
    "create-server.toml": ("create", "SERVER"),
}
# This exact IDependencyLocator loads a fixed resource through its own code source.
# It is not declared in JarJar metadata. Do not infer custom loaders from filenames.
PINNED_EMBEDDED = {
    "11674636141f3be9ea22c8b274e58380f33169c2e4f5e9605cf6865f467d90a9": {
        "META-INF/jarjar/crash_assistant-forge.jar":
            "6d034fcb47eda3cd10b2e05c741058e7641015ce7ca7f675aff9692df454631c",
    },
}


def mod_catalog(root):
    """Hash mod JARs, declared JarJar children and exact reviewed loader resources.

    This is a descriptor catalog, not proof of loading or transitive acquisition.
    Loader/runtime libraries outside mods remain separate provisioning evidence.
    """
    require(root.is_absolute() and root.is_dir(), "UNSAFE_PATH")
    reject_links(root)
    folder = root / "mods"
    reject_links(folder)
    paths = sorted(folder.glob("*.jar"))
    require(0 < len(paths) <= 512, "ROLE_CATALOG_QUOTA")
    rows = []
    total = 0

    def inspect(archive, logical, sha, size, depth):
        nonlocal total
        total += size
        require(depth <= 4 and len(rows) < 1024 and total <= 2 * 1024**3,
                "ROLE_CATALOG_QUOTA")
        names = archive.namelist()
        require(len(names) == len(set(names)) and len(names) <= 100000,
                "ROLE_CATALOG_ARCHIVE")

        def read(name, limit):
            info = archive.getinfo(name)
            require(info.file_size <= limit, "ROLE_CATALOG_QUOTA")
            raw = archive.read(name)
            require(len(raw) == info.file_size, "ROLE_CATALOG_ARCHIVE")
            return raw

        ids = []
        if "META-INF/mods.toml" in names:
            metadata = tomllib.loads(read("META-INF/mods.toml", 1024**2).decode("utf-8"))
            ids = [entry["modId"] for entry in metadata.get("mods", [])]
            require(all(type(value) is str and re.fullmatch(r"[a-z][a-z0-9_]{1,63}", value)
                        for value in ids) and len(set(ids)) == len(ids), "ROLE_CATALOG_MODS")
        rows.append({"path": logical, "file": PurePosixPath(logical).name,
                     "sha256": sha, "bytes": size, "mod_ids": sorted(ids)})
        for path, expected in PINNED_EMBEDDED.get(sha, {}).items():
            safe_relative(path)
            raw = read(path, 64 * 1024**2)
            require(hashlib.sha256(raw).hexdigest() == expected, "ROLE_CATALOG_EMBEDDED")
            with zipfile.ZipFile(io.BytesIO(raw)) as nested:
                inspect(nested, logical + "!/" + path, expected, len(raw), depth + 1)
        if "META-INF/jarjar/metadata.json" in names:
            metadata = strict_json(read("META-INF/jarjar/metadata.json", 1024**2))
            children = metadata["jars"]
            require(type(children) is list and len(children) <= 128, "ROLE_CATALOG_QUOTA")
            seen = set()
            for entry in children:
                path = entry["path"]
                safe_relative(path)
                require(path.endswith(".jar") and path not in seen, "ROLE_CATALOG_ARCHIVE")
                seen.add(path)
                raw = read(path, 64 * 1024**2)
                with zipfile.ZipFile(io.BytesIO(raw)) as nested:
                    inspect(nested, logical + "!/" + path, hashlib.sha256(raw).hexdigest(),
                            len(raw), depth + 1)

    for path in paths:
        reject_links(path)
        stat = path.stat()
        require(stat.st_nlink == 1 and stat.st_size <= 128 * 1024**2, "ROLE_CATALOG_QUOTA")
        sha = file_hash(path)
        with zipfile.ZipFile(path) as archive:
            inspect(archive, "mods/" + path.name, sha, stat.st_size, 0)
        require(file_hash(path) == sha, "SOURCE_CHANGED")
    require(paths == sorted(folder.glob("*.jar")), "SOURCE_CHANGED")
    return rows


def prepare_control(root):
    require(root.is_absolute() and root.is_dir(), "UNSAFE_PATH")
    require(all(file_hash(root / name) == sha for name, sha in PINS.items()),
            "ROLE_CONTROL_ARTIFACT")
    raw = _read(root, "world/serverconfig/create-server.toml")
    config = tomllib.loads(raw.decode("utf-8"))
    for path, expected in CURRENT:
        value = config
        for key in path:
            value = value[key]
        require(type(value) is int and value == expected, "ROLE_CONTROL_CONFIG")
    return {"policy": "e9e-role-create-consumer/1", "source_sha256": dict(PINS),
            "create_file_sha256": hashlib.sha256(raw).hexdigest(),
            "catalog": mod_catalog(root), "script": _SCRIPT}


def inspect_control(log, catalog):
    require(type(log) is str and len(log.encode("utf-8")) <= 64 * 1024**2,
            "ROLE_CONTROL_QUOTA")
    records = [line.split(MARKER, 1)[1] for line in log.splitlines() if MARKER in line]
    require(len(records) == 1 and len(records[0].encode("utf-8")) <= 1024**2,
            "ROLE_CONTROL_RECORD")
    value = strict_json(records[0])
    require(type(value) is dict and set(value) == {"schema", "mods", "configs", "create"}
            and value["schema"] == "strata/E9ERoleObservation/1", "ROLE_CONTROL_RECORD")
    mods = value["mods"]
    require(type(mods) is list and 2 <= len(mods) <= 1024, "ROLE_CONTROL_MODS")
    ids = []
    bindings = []
    for mod in mods:
        require(type(mod) is dict and set(mod) == {"id", "version", "file", "path", "loaded"}
                and mod["loaded"] is True and type(mod["id"]) is str
                and re.fullmatch(r"[a-z][a-z0-9_]{1,63}", mod["id"]) is not None,
                "ROLE_CONTROL_MODS")
        for key, limit in (("version", 256), ("file", 256), ("path", 4096)):
            require(type(mod[key]) is str and (0 if key == "path" else 1) <= len(mod[key]) <= limit
                    and all(ord(c) >= 32 for c in mod[key]), "ROLE_CONTROL_MODS")
        ids.append(mod["id"])
        if mod["id"] not in {"forge", "minecraft"}:
            matches = [row for row in catalog if row["file"] == mod["file"]
                       and mod["id"] in row["mod_ids"]]
            require(matches and len({row["path"] for row in matches}) == len(matches)
                    and len({row["sha256"] for row in matches}) == 1, "ROLE_CONTROL_CATALOG")
            require(mod["path"] or all("!/" in row["path"] for row in matches),
                    "ROLE_CONTROL_RUNTIME_PATH")
            bindings.append({"id": mod["id"],
                             "catalog_paths": sorted(row["path"] for row in matches),
                             "sha256": matches[0]["sha256"],
                             "runtime_path_available": bool(mod["path"])})
        else:
            require(bool(mod["path"]), "ROLE_CONTROL_RUNTIME_PATH")
    require(ids == sorted(set(ids)) and {"forge", "minecraft", "create", "sophisticatedcore"}
            <= set(ids) and "inventorysorter" not in ids, "ROLE_CONTROL_MODS")
    configs = value["configs"]
    require(type(configs) is list and len(configs) == len(CONFIGS), "ROLE_CONTROL_CONFIGS")
    for observed, (name, source) in zip(configs, CONFIGS.items(), strict=True):
        expected = {"file": name, "registered": source is not None}
        if source:
            expected.update(mod=source[0], type=source[1], loaded=True)
        require(type(observed) is dict and observed == expected and type(observed.get("registered")) is bool
                and (not source or observed.get("loaded") is True), "ROLE_CONTROL_CONFIGS")
    create = value["create"]
    require(type(create) is dict and set(create) == {"before", "after", "rows"},
            "ROLE_CONTROL_CREATE")
    expected_raw = [{"path": path, "declared": True, "present": True, "value": number}
                    for path, number in CURRENT] + [
                        {"path": path, "declared": False, "present": False, "value": None}
                        for path in LEGACY]
    for snapshot in (create["before"], create["after"]):
        require(type(snapshot) is list and snapshot == expected_raw, "ROLE_CONTROL_RAW")
        require(all(type(row["declared"]) is bool and type(row["present"]) is bool
                    and (row["value"] is None or type(row["value"]) in (int, float))
                    for row in snapshot), "ROLE_CONTROL_RAW")
    rows = create["rows"]
    require(type(rows) is list and len(rows) == len(CURRENT), "ROLE_CONTROL_GETTERS")
    for row, (path, number) in zip(rows, CURRENT, strict=True):
        require(type(row) is dict and set(row) == {"path", "first", "second"}
                and row["path"] == path and type(row["first"]) in (int, float)
                and type(row["second"]) in (int, float) and row["first"] == row["second"] == number,
                "ROLE_CONTROL_GETTERS")
    return {"schema": "strata/E9ERoleInspection/1", "visibility": "evaluator", "result": "pass",
            "policy": "e9e-role-create-consumer/1", "observation": value, "bindings": bindings,
            "loaded_mod_count": len(mods), "getter_calls": 6,
            "inventorysorter_loaded": False, "selected_raw_unchanged": True,
            "cache_initialization_possible": True, "source_authentication_qualified": False,
            "transitive_provenance_qualified": False, "mechanics_qualified": False,
            "scoring_eligible": False, "gate_result": "not_run"}


_SCRIPT = r'''// Fixed operator-only role/config reference. No player/model or config mutation.
const StrataRoleAnchor = Java.loadClass('net.p3pp3rf1y.sophisticatedcore.Config');
const StrataRoleCreate = Java.loadClass('com.simibubi.create.infrastructure.config.AllConfigs');
const StrataRoleArrays = Java.loadClass('java.util.Arrays');
const StrataRoleList = Java.loadClass('java.util.ArrayList');
const StrataRoleTracker = StrataRoleAnchor.COMMON.getClass()
    .forName('net.minecraftforge.fml.config.ConfigTracker').getField('INSTANCE').get(null);
const StrataRoleMods = StrataRoleAnchor.COMMON.getClass()
    .forName('net.minecraftforge.fml.ModList').getMethod('get', []).invoke(null, []);
let strataRoleTicks = 0;
ServerEvents.tick(event => {
    if (++strataRoleTicks != 20) return;
    const names = ['bhmenu-client.toml', 'nomoreworldsettings-client.toml',
        'inventorysorter-server.toml', 'sophisticatedcore-server.toml',
        'sophisticatedcore-common.toml', 'create-server.toml'];
    let configs = [];
    for (let i = 0; i < names.length; i++) {
        let config = StrataRoleTracker.fileMap().get(names[i]);
        let row = {file: names[i], registered: config != null};
        if (config != null) {
            row.mod = String(config.getModId()); row.type = String(config.getType().name());
            row.loaded = config.getSpec().isLoaded();
        }
        configs.push(row);
    }
    // Copy through a public implementation; Java immutable-list classes are package-private.
    let mods = []; let nativeMods = new StrataRoleList(StrataRoleMods.getMods());
    if (nativeMods.size() < 2 || nativeMods.size() > 1024 ||
        nativeMods.size() != StrataRoleMods.size()) throw new Error('STRATA_ROLE_MOD_QUOTA');
    for (let i = 0; i < nativeMods.size(); i++) {
        let info = nativeMods.get(i); let file = info.getOwningFile().getFile();
        let id = String(info.getModId());
        mods.push({id: id, version: String(info.getVersion()), file: String(file.getFileName()),
            path: String(file.getFilePath()), loaded: StrataRoleMods.isLoaded(id)});
    }
    mods.sort((left, right) => left.id < right.id ? -1 : left.id > right.id ? 1 : 0);
    let server = StrataRoleCreate.server();
    let config = StrataRoleTracker.fileMap().get('create-server.toml');
    if (config == null || String(config.getModId()) != 'create' ||
        String(config.getType().name()) != 'SERVER' || config.getSpec() !== server.specification ||
        !server.specification.isLoaded()) throw new Error('STRATA_ROLE_CREATE_SOURCE');
    let data = config.getConfigData(); let spec = server.specification.getSpec();
    const paths = [['logistics', 'defaultExtractionTimer'],
        ['schematics', 'schematicannon', 'schematicannonShotsPerGunpowder'],
        ['schematics', 'schematicannon', 'schematicannonDelay'],
        ['logistics', 'defaultExtractionLimit'],
        ['schematics', 'schematicannon', 'schematicannonGunpowderWorth'],
        ['schematics', 'schematicannon', 'schematicannonFuelUsage']];
    const expected = [8, 400, 10];
    function snapshot() {
        let result = [];
        for (let i = 0; i < paths.length; i++) {
            let path = StrataRoleArrays.asList(paths[i]);
            let declared = spec['getRaw(java.util.List)'](path) != null;
            let raw = data['getRaw(java.util.List)'](path);
            let present = data['contains(java.util.List)'](path);
            let number = null;
            if (i < 3) {
                if (!declared || !present || raw == null ||
                    (typeof raw != 'number' && (typeof raw != 'object' ||
                     (String(raw.getClass().getName()) != 'java.lang.Integer' &&
                      String(raw.getClass().getName()) != 'java.lang.Long'))))
                    throw new Error('STRATA_ROLE_RAW_TYPE');
                number = Number(raw);
                if (number != expected[i]) throw new Error('STRATA_ROLE_RAW_VALUE');
            } else if (declared || present || raw != null) throw new Error('STRATA_ROLE_LEGACY_PRESENT');
            result.push({path: paths[i], declared: declared, present: present, value: number});
        }
        return result;
    }
    let before = snapshot(); let rows = [];
    let getters = [server.logistics.defaultExtractionTimer,
        server.schematics.schematicannonShotsPerGunpowder, server.schematics.schematicannonDelay];
    for (let i = 0; i < getters.length; i++) {
        let first = Number(getters[i].get()); let second = Number(getters[i].get());
        if (first != expected[i] || second != expected[i]) throw new Error('STRATA_ROLE_GETTER_VALUE');
        rows.push({path: paths[i], first: first, second: second});
    }
    let after = snapshot();
    if (StrataRoleCreate.server() !== server || config.getConfigData() !== data ||
        StrataRoleTracker.fileMap().get('create-server.toml') !== config ||
        !server.specification.isLoaded()) throw new Error('STRATA_ROLE_SOURCE_CHANGED');
    let output = JSON.stringify({schema: 'strata/E9ERoleObservation/1',
        mods: mods, configs: configs, create: {before: before, after: after, rows: rows}});
    if (output.length > 1024 * 1024) throw new Error('STRATA_ROLE_OUTPUT_QUOTA');
    console.log('STRATA_E9E_ROLE_CONTROL ' + output);
});
'''
