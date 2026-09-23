"""Private sequential staging; original per-file pins remain copy authority."""

import base64
import hashlib
import os
from pathlib import Path
import time

from mcbench.launch_integrity import safe
from mcbench.storage import require, safe_relative

POLICY = "sequential-bundles512mib/1"
HEADER = "strata/WriterStagingBundles/1"
MAX_PART = 512 * 1024**2
MAX_TOTAL = 1024**3


def stage_bundles(directory, sources, deadline):
    """Caller holds original input and workspace leases through final cleanup.

    A bundle never splits a source file. The writer consumes each whole bundle
    in manifest order and verifies every destination against its original pin.
    New bundle digests are transport pins, not replacement source authority.
    """
    directory = Path(directory)
    safe(directory)  # Validate through Win32 paths; retain the Java-compatible manifest spelling.
    require(directory.is_dir() and not any(directory.iterdir()), "WRITER_STAGING_NOT_EMPTY")
    require(0 < len(sources) <= 12000 and all(0 <= pin.bytes <= MAX_PART for pin in sources.values())
            and sum(pin.bytes for pin in sources.values()) <= MAX_TOTAL, "WRITER_BYTE_QUOTA")
    lines, pins, part, offset, total = [HEADER], [], None, 0, 0
    part_hash = None
    target = None

    def close_part():
        nonlocal part
        if part is not None:
            part.flush()
            os.fsync(part.fileno())
            part.close()
            part = None
            require(target.stat().st_size == offset, "WRITER_STAGING_CHANGED")
            pins.append({"path": str(target), "bytes": offset, "sha256": part_hash.hexdigest()})

    try:
        for relative, pin in sorted(sources.items()):
            safe_relative(relative)
            require(time.monotonic() < deadline, "WRITER_STAGING_TIMEOUT")
            if part is None or offset + pin.bytes > MAX_PART:
                close_part()
                target = Path(directory) / f"bundle-{len(pins):04d}.bin"
                part = target.open("xb")
                part_hash, offset = hashlib.sha256(), 0
            start, copied, source_hash = offset, 0, hashlib.sha256()
            with Path(pin.path).open("rb") as source:
                while chunk := source.read(65536):
                    require(time.monotonic() < deadline, "WRITER_STAGING_TIMEOUT")
                    copied += len(chunk)
                    require(copied <= pin.bytes, "WRITER_SOURCE_CHANGED")
                    require(part.write(chunk) == len(chunk), "WRITER_STAGING_CHANGED")
                    source_hash.update(chunk)
                    part_hash.update(chunk)
            require(copied == pin.bytes and source_hash.hexdigest() == pin.sha256,
                    "WRITER_SOURCE_CHANGED")
            offset += copied
            total += copied
            lines.append("\t".join([base64.b64encode(relative.encode()).decode(),
                base64.b64encode(str(target).encode()).decode(), pin.sha256, str(pin.bytes), str(start)]))
        close_part()
    finally:
        if part is not None:
            part.close()
    manifest = "\n".join(lines).encode("utf-8")
    require(len(pins) <= 3 and len(manifest) <= 8 * 1024**2, "WRITER_MANIFEST_QUOTA")
    return pins, manifest, {"policy": POLICY, "files": len(sources), "bundles": len(pins), "bytes": total}
