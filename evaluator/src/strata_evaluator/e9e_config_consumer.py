"""Fixed operator-only Sophisticated Core consumer control for E9E 1.27.0.

The getter can initialize its cache or append unknown IDs to its configuration.
Only the complete pinned COMMON list is queried, after exact live-list guards.
This is a reference control, never a gameplay tool or scoring authority.
"""

import hashlib
import json
import re
import tomllib

from mcbench.inference_transport import strict_json
from mcbench.pack_modes import _read
from mcbench.storage import require

PINS = {
    "mods/sophisticatedcore-1.19.2-0.6.4.730.jar":
        "0de1a4c730674ad9f27611fa17b866f7ca5dca15841854d64867693c2a5862fe",
    "config/configswapper/expert/config/sophisticatedcore-common.toml":
        "375d814abf3b8d82a8b70e9c55ae51604034dc31ab91b1577ebf36e1e40d06e5",
}
COMMON = "config/configswapper/expert/config/sophisticatedcore-common.toml"
MARKER = "STRATA_SOPHISTICATED_CONSUMER "


def expected_values(entries):
    require(type(entries) is list and 1 <= len(entries) <= 256, "CONFIG_CONSUMER_ENTRIES")
    result = {}
    for entry in entries:
        require(type(entry) is str and re.fullmatch(
            r"[a-z0-9_.-]+:[a-z0-9_./-]+\|(?:true|false|alse)", entry) is not None,
            "CONFIG_CONSUMER_ENTRIES")
        name, value = entry.split("|")
        require(name not in result, "CONFIG_CONSUMER_DUPLICATE")
        # Exact pinned implementation uses Boolean.valueOf, including vendor 'alse'.
        result[name] = value == "true"
    return result


def prepare_control(root):
    """Render only from the pinned real artifacts, with no installation writes."""
    require(root.is_absolute() and root.is_dir(), "UNSAFE_PATH")
    files = {name: _read(root, name) for name in PINS}
    require(all(hashlib.sha256(files[name]).hexdigest() == sha for name, sha in PINS.items()),
            "CONFIG_CONSUMER_ARTIFACT")
    entries = tomllib.loads(files[COMMON].decode("utf-8"))["common"]["enabledItems"]
    expected_values(entries)
    require(len(entries) == 145, "CONFIG_CONSUMER_ENTRIES")
    return {"script": _SCRIPT.replace("__ENTRIES__", json.dumps(entries)),
            "entries": entries, "source_sha256": dict(PINS),
            "policy": "e9e-sophisticated-common-consumer/1"}


def inspect_control(log, entries):
    """Check bounded preserved stdout; process/source binding is a separate audit."""
    require(type(log) is str and len(log.encode("utf-8")) <= 64 * 1024**2,
            "CONFIG_CONSUMER_QUOTA")
    lines = [line.split(MARKER, 1)[1] for line in log.splitlines() if MARKER in line]
    require(len(lines) == 1 and len(lines[0].encode("utf-8")) <= 65536,
            "CONFIG_CONSUMER_RECORD")
    value = strict_json(lines[0])
    require(type(value) is dict and set(value) == {"schema", "before", "after", "rows"}
            and value["schema"] == "strata/SophisticatedConsumerObservation/1",
            "CONFIG_CONSUMER_RECORD")
    expected = expected_values(entries)
    require(value["before"] == entries == value["after"], "CONFIG_CONSUMER_RAW_CHANGED")
    rows = value["rows"]
    require(type(rows) is list and len(rows) == len(expected), "CONFIG_CONSUMER_ROWS")
    for row, (item, enabled) in zip(rows, expected.items(), strict=True):
        require(type(row) is dict and set(row) == {"item_id", "first", "second"}
                and row["item_id"] == item and type(row["first"]) is bool
                and type(row["second"]) is bool, "CONFIG_CONSUMER_ROWS")
        require(row["first"] == row["second"] == enabled, "CONFIG_CONSUMER_MISMATCH")
    return {"schema": "strata/SophisticatedConsumerInspection/1", "visibility": "evaluator",
            "policy": "e9e-sophisticated-common-consumer/1", "result": "pass",
            "item_count": len(rows), "getter_calls": 2 * len(rows), "observation": value,
            "cache_initialization_possible": True, "raw_configuration_unchanged": True,
            "source_authentication_qualified": False, "mechanics_qualified": False,
            "scoring_eligible": False, "gate_result": "not_run"}


_SCRIPT = r'''// Operator-only fixed consumer control; no model/player or unknown-item query.
const StrataConsumerConfig = Java.loadClass('net.p3pp3rf1y.sophisticatedcore.Config');
// KubeJS blocks direct FML class loading. Fixed metadata reflection leaves its filter intact.
const StrataConsumerTracker = StrataConsumerConfig.COMMON.getClass()
    .forName('net.minecraftforge.fml.config.ConfigTracker').getField('INSTANCE').get(null);
const StrataConsumerLocation = Java.loadClass('net.minecraft.resources.ResourceLocation');
const StrataConsumerArrays = Java.loadClass('java.util.Arrays');
const strataConsumerExpected = __ENTRIES__;
let strataConsumerTicks = 0;
ServerEvents.tick(event => {
    strataConsumerTicks++;
    if (strataConsumerTicks != 20) return;
    const file = 'sophisticatedcore-common.toml';
    let config = StrataConsumerTracker.fileMap().get(file);
    if (config == null || String(config.getModId()) != 'sophisticatedcore' ||
        String(config.getType().name()) != 'COMMON' ||
        config.getSpec() !== StrataConsumerConfig.COMMON_SPEC ||
        !StrataConsumerConfig.COMMON_SPEC.isLoaded()) throw new Error('STRATA_CONSUMER_SOURCE');
    let data = config.getConfigData();
    const path = StrataConsumerArrays.asList('common', 'enabledItems');
    function copyRaw() {
        let values = data['getRaw(java.util.List)'](path);
        if (values == null || values.size() != strataConsumerExpected.length)
            throw new Error('STRATA_CONSUMER_RAW_SIZE');
        let copy = [];
        for (let i = 0; i < values.size(); i++) {
            let text = String(values.get(i));
            if (text != strataConsumerExpected[i]) throw new Error('STRATA_CONSUMER_RAW_MISMATCH');
            copy.push(text);
        }
        return copy;
    }
    let before = copyRaw();
    let rows = [];
    for (let i = 0; i < before.length; i++) {
        // Query only IDs proven in the loaded list; the after-check detects appends.
        let id = before[i].split('|')[0];
        let location = new StrataConsumerLocation(id);
        let first = StrataConsumerConfig.COMMON.enabledItems[
            'isItemEnabled(net.minecraft.resources.ResourceLocation)'](location);
        let second = StrataConsumerConfig.COMMON.enabledItems[
            'isItemEnabled(net.minecraft.resources.ResourceLocation)'](location);
        rows.push({item_id: id, first: first, second: second});
    }
    let after = copyRaw();
    if (StrataConsumerTracker.fileMap().get(file) !== config ||
        config.getConfigData() !== data || !StrataConsumerConfig.COMMON_SPEC.isLoaded())
        throw new Error('STRATA_CONSUMER_CHANGED');
    console.log('STRATA_SOPHISTICATED_CONSUMER ' + JSON.stringify({
        schema: 'strata/SophisticatedConsumerObservation/1', before: before, after: after, rows: rows}));
});
'''
