"""Explicit allowlist packaging: never copy a repository tree into a gameplay runtime."""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from .storage import canonical, reject_links, require


def package_gameplay(repository: Path, output: Path):
    repository, output = repository.absolute(), output.absolute()
    reject_links(repository)
    reject_links(output)
    require(not output.exists(), "TARGET_EXISTS")
    # The compiled client imports only built-in Node APIs and its sanitized error module.
    sources = {
        "cli.js": repository / "backends/mineflayer/dist/src/cli.js",
        "errors.js": repository / "backends/mineflayer/dist/src/errors.js",
        "skills/minecraft-keybindings/SKILL.md": repository / "gameplay/skills/minecraft-keybindings/SKILL.md",
    }
    for source in sources.values():
        reject_links(source)
        require(source.is_file(), "BUILD_REQUIRED")
    cli = sources["cli.js"].read_text(encoding="utf-8")
    require("./protocol.js" not in cli and "./errors.js" in cli, "UNSAFE_CLIENT_DEPENDENCY")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".gameplay-") as temporary:
        staging = Path(temporary) / "client"
        staging.mkdir()
        for relative, source in sources.items():
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        package = {"name": "@strata-bench/mcgame", "version": "0.1.0", "private": True,
                   "type": "module", "bin": {"mcgame": "cli.js"}, "engines": {"node": "24.19.0"}}
        (staging / "package.json").write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
        hashes = {path.relative_to(staging).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(staging.rglob("*")) if path.is_file()}
        manifest = {"schema": "strata/GameplayClientBundle/1", "files": hashes,
                    "requires_scoped_grant": True, "proves_runtime_isolation": False}
        (staging / "manifest.json").write_bytes(canonical(manifest) + b"\n")
        os.rename(staging, output)
    return manifest
