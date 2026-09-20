"""Private log evidence: a launcher exit code cannot certify a game-server save.

Recognized pinned vanilla/Forge log signatures are failure evidence. Their
absence is never a clean-save, snapshot-integrity or pack-qualification proof.
Raw log text, paths and crash report contents stay out of the summary.
"""

import hashlib
import re
from pathlib import Path

from .storage import reject_links, require

POLICY = "vanilla-forge-server-critical-log-signatures/1"
MAX_BYTES = 256 * 1024**2
MAX_LINE = 65536
MAX_SIGNALS = 4096
ANSI = re.compile(rb"\x1b\[[0-9;]*m")
RECORD = re.compile(rb"\[[0-9:., -]+\] \[([^\]\r\n]+)/([A-Z]+)\]"
                    rb"(?: \[([^\]\r\n]+)\])?: (.*)")


def critical_signal(line: bytes) -> str | None:
    record = RECORD.fullmatch(ANSI.sub(b"", line).rstrip(b"\r\n"))
    if record is None:
        return None
    thread, level, logger, message = record.groups()
    if level not in (b"ERROR", b"FATAL"):
        return None
    if thread == b"Server Watchdog":
        return "SERVER_WATCHDOG_FAILURE"
    if logger in (None, b"minecraft/MinecraftServer", b"MinecraftServer") and thread == b"Server thread":
        if message.startswith((b"Encountered an unexpected exception", b"Exception in server tick loop",
                               b"This crash report has been saved to:")):
            return "SERVER_CRASH"
    if thread == b"Server thread" and level == b"FATAL" and message.startswith(b"Preparing crash report"):
        return "SERVER_CRASH"
    if logger in (b"minecraft/LevelChunk", b"LevelChunk") and (
            b"exception trying to write state" in message and b"will not persist" in message):
        return "BLOCK_ENTITY_SAVE_FAILED"
    # These are core persistence errors; mod/plugin startup ERROR messages have
    # separate compatibility gates and are not silently interpreted as crashes.
    if logger in (b"minecraft/ChunkMap", b"minecraft/ChunkStorage", b"minecraft/IOWorker",
                  b"minecraft/DimensionDataStorage") and message.startswith(
                      (b"Failed to save", b"Failed to write", b"Failed to store", b"Couldn't save", b"Error saving")):
        return "WORLD_SAVE_FAILED"
    return None


def inspect_server_log(path: Path) -> dict:
    reject_links(path)
    require(path.is_file() and path.stat().st_size <= MAX_BYTES, "SERVER_LOG_UNAVAILABLE")
    hasher = hashlib.sha256()
    offset = 0
    lines = 0
    signals = []
    with path.open("rb") as stream:
        while line := stream.readline(MAX_LINE + 1):
            require(len(line) <= MAX_LINE and line.endswith(b"\n"), "SERVER_LOG_INCOMPLETE")
            require(offset + len(line) <= MAX_BYTES, "SERVER_LOG_UNAVAILABLE")
            lines += 1
            if code := critical_signal(line):
                require(len(signals) < MAX_SIGNALS, "SERVER_LOG_QUOTA")
                signals.append({"code": code, "line": lines, "byte_offset": offset,
                                "line_sha256": hashlib.sha256(line).hexdigest()})
            hasher.update(line)
            offset += len(line)
    return {"schema": "strata/ServerLogHealth/1", "policy": POLICY,
            "result": "fail" if signals else "pass", "scope": "recognized_log_signatures_only",
            "bytes": offset, "lines": lines, "sha256": hasher.hexdigest(),
            "critical_signals": signals, "clean_save_proven": False,
            "snapshot_integrity_proven": False, "gate_result": "not_run"}
