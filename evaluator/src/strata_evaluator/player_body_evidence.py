"""Independent content checks for the exact private vanilla body observer.

Only callers with stopped, immutable private custody may turn content checks
into a producer claim. A file/header/PID alone never authenticates its writer.
"""

import hashlib
import io
import re
import uuid
import zipfile

from mcbench.inference_transport import strict_json
from mcbench.storage import require

from .player_body_agent import POLICY, SERVER_SHA
from .saved_blocks import MAX_NBT, NbtReader, field

MODULE_SHA = "999ad44d16b5d6255963c3571e70842ec4c4c642f28d993665c513671855cba6"
CALLBACK_SHA = "4ad380be5417d3f6497c04f12cec58dfb1b1bec80062a116ccd10ca1af5621dc"
TRANSFORMED = {
    "agh": "7fd484f40c27da62ae7e453159cb62f63e5ccaf4cdb6ad6a959d9b000cd92bba",
    "net/minecraft/server/MinecraftServer": "eb269f90f263802dfcf1f59ef42832d958195cc141cc2d4019a29ad06925e6c5",
}
REQUIRED_CLASSES = {*TRANSFORMED, "bbn", "pj", "pt", "ayz"}
MAX_TOTAL = 64 * 1024**2
MAX_JOURNAL = 1024**2
MAX_BINDINGS = 4 * 1024**2


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _uint(value, maximum=9_007_199_254_740_991):
    return type(value) is int and 0 <= value <= maximum


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)


def validate_body_scope(scope, roster, config_sha256, pid):
    require(isinstance(scope, dict) and set(scope) == {"campaign_id", "epoch", "run_id"}
            and all(isinstance(scope[k], str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", scope[k])
                    for k in ("campaign_id", "run_id"))
            and _uint(scope["epoch"], 999999999) and scope["epoch"] > 0
            and _digest(config_sha256) and _uint(pid) and pid > 0, "BODY_EXPECTED_SCOPE")
    require(isinstance(roster, list) and 1 <= len(roster) <= 64
            and all(isinstance(v, str) and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", v)
                    for v in roster) and len(set(roster)) == len(roster), "BODY_EXPECTED_ROSTER")


def official_body_class_pins(server_bytes):
    """Derive originals from the exact official JAR, never caller-declared hashes."""
    require(type(server_bytes) is bytes and len(server_bytes) <= 64 * 1024**2
            and sha(server_bytes) == SERVER_SHA, "BODY_SERVER_PIN")
    with zipfile.ZipFile(io.BytesIO(server_bytes)) as jar:
        entries = [entry for entry in jar.infolist() if entry.filename.endswith(".class")]
        require(1 <= len(entries) <= 16384 and len({e.filename for e in entries}) == len(entries)
                and all(e.file_size <= 4 * 1024**2 for e in entries), "BODY_CLASS_INVENTORY")
        return {e.filename[:-6]: sha(jar.read(e)) for e in entries}


def verify_player_body_output(read, names, *, server_bytes, scope, roster, config_sha256, pid):
    """Verify one immutable output inventory against independently supplied scope.

    read(name, byte_limit) resolves only this private registered inventory.
    server_bytes must come from the held/sealed installed implementation. The
    return value deliberately makes no owned producer or live-state claim.
    """
    validate_body_scope(scope, roster, config_sha256, pid)
    expected_names = {"events.jsonl", "loaded-classes.txt", *(v + ".nbt" for v in roster)}
    require(isinstance(names, (list, tuple, set)) and len(names) == len(expected_names)
            and set(names) == expected_names, "BODY_OUTPUT_INVENTORY")
    captured = {}

    def get(name, limit):
        raw = read(name, limit)
        require(type(raw) is bytes and 0 < len(raw) <= limit, "BODY_OUTPUT_QUOTA")
        captured[name] = (raw, limit)
        return raw

    journal = get("events.jsonl", MAX_JOURNAL)
    lines = journal.splitlines(keepends=True)
    require(len(lines) == 4 and all(line.endswith(b"\n") for line in lines), "BODY_JOURNAL_INCOMPLETE")
    records, previous = [], 0
    for seq, line in enumerate(lines, 1):
        record = strict_json(line)
        require(isinstance(record, dict) and set(record) == {"seq", "elapsed_ns", "body"}
                and type(record["seq"]) is int and record["seq"] == seq and _uint(record["elapsed_ns"])
                and record["elapsed_ns"] >= previous and isinstance(record["body"], dict), "BODY_JOURNAL_ORDER")
        previous = record["elapsed_ns"]
        records.append(record)
    start, running, capture, stop = [record["body"] for record in records]
    expected_start = {"schema": "strata/PrivateBodyStart/1", "policy": POLICY, **scope,
        "pid": pid, "config_sha256": config_sha256, "module_sha256": MODULE_SHA,
        "server_sha256": SERVER_SHA, "roster": roster}
    require(start == expected_start and type(start.get("epoch")) is int and type(start.get("pid")) is int,
            "BODY_PRODUCER_SCOPE")
    require(running == {"schema": "strata/PrivateBodyRunning/1"}, "BODY_JOURNAL_ORDER")
    require(set(capture) == {"schema", "tick", "begin_ns", "bodies"}
            and capture["schema"] == "strata/PrivateBodyCapture/1" and _uint(capture["tick"], 1_000_000)
            and capture["tick"] > 0 and _uint(capture["begin_ns"])
            and records[1]["elapsed_ns"] <= capture["begin_ns"] <= records[2]["elapsed_ns"], "BODY_CAPTURE_SCOPE")
    require(set(stop) == {"schema", "tick", "loaded_classes", "bindings_sha256"}
            and stop["schema"] == "strata/PrivateBodyStop/1" and _uint(stop["tick"], 1_000_000)
            and stop["tick"] >= capture["tick"] and _uint(stop["loaded_classes"], 16384)
            and stop["loaded_classes"] >= len(REQUIRED_CLASSES) and _digest(stop["bindings_sha256"]), "BODY_STOP_SCOPE")
    binding_raw = get("loaded-classes.txt", MAX_BINDINGS)
    require(sha(binding_raw) == stop["bindings_sha256"], "BODY_BINDINGS_CHANGED")
    try:
        binding_lines = binding_raw.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        require(False, "BODY_BINDINGS_FORMAT")
    require(len(binding_lines) == stop["loaded_classes"]
            and "\n".join(binding_lines).encode() == binding_raw, "BODY_BINDINGS_FORMAT")
    official = official_body_class_pins(server_bytes)
    bindings = {}
    for line in binding_lines:
        require(line.count("=") == 1, "BODY_BINDINGS_FORMAT")
        name, hashes = line.split("=")
        require(name in official and name not in bindings and hashes == official[name] + ":"
                + TRANSFORMED.get(name, official[name]), "BODY_LOADED_CLASS_PIN")
        bindings[name] = hashes
    require(REQUIRED_CLASSES <= bindings.keys() and list(bindings) == sorted(bindings), "BODY_INCOMPLETE_BINDINGS")
    bodies = capture["bodies"]
    require(isinstance(bodies, list) and len(bodies) == len(roster), "BODY_CAPTURE_ROSTER")
    result, total = {}, 0
    for identity, body in zip(roster, bodies, strict=True):
        require(isinstance(body, dict) and set(body) == {"uuid", "bytes", "sha256"} and body["uuid"] == identity
                and _uint(body["bytes"], MAX_NBT) and body["bytes"] > 0 and _digest(body["sha256"]), "BODY_CAPTURE_ROSTER")
        total += body["bytes"]
        require(total <= MAX_TOTAL, "BODY_OUTPUT_QUOTA")
        raw = get(identity + ".nbt", body["bytes"])
        require(len(raw) == body["bytes"] and sha(raw) == body["sha256"], "BODY_NBT_CHANGED")
        compound = NbtReader(raw).root()
        raw_uuid = field(compound, "UUID", 11)
        require(len(raw_uuid) == 16 and str(uuid.UUID(bytes=bytes(raw_uuid))) == identity, "BODY_NBT_IDENTITY")
        result[identity] = {"bytes": len(raw), "nbt_sha256": sha(raw), "root_fields": len(compound)}
    # Immutable custody is still required; this detects changed reads but cannot
    # establish that a concurrent writer never changed a file between reads.
    require(all(read(name, limit) == raw for name, (raw, limit) in captured.items()), "BODY_OUTPUT_CHANGED")
    return {"schema": "strata/PrivatePlayerBodyReport/1", "policy": POLICY, "visibility": "evaluator",
        **scope, "pid": pid, "config_sha256": config_sha256, "module_sha256": MODULE_SHA,
        "server_sha256": SERVER_SHA, "journal_sha256": sha(journal), "bindings_sha256": sha(binding_raw),
        "loaded_classes": len(bindings), "capture_tick": capture["tick"], "stop_tick": stop["tick"],
        "capture_begin_ns": capture["begin_ns"], "capture_end_ns": records[2]["elapsed_ns"],
        "bodies": result, "content_verified": True, "owned_producer_verified": False,
        "live_initial_state_verified": False, "transient_state_verified": False, "native_probe_admission": False}
