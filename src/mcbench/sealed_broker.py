"""Isolated stdlib bootstrap; its bytes are held by the native supervisor.

Run with -I -S -B. No site initialization, environment import paths or CWD
imports. Only exact sealed module origins may be imported after verification.
"""

import argparse
import importlib.machinery
from pathlib import Path
import sys

# This exact sibling is sealed by the supervisor before this process starts.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from launch_integrity import FileLease, check, read_manifest  # noqa: E402


class SealedSourceLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        # -B suppresses writes but still permits reading timestamp-matched pyc.
        # Compile only the pinned source; never load an unlisted bytecode cache.
        return compile(self.get_data(self.path), self.path, "exec", dont_inherit=True,
                       optimize=sys.flags.optimize)


class SealedImports:
    def __init__(self, files):
        self.files = {self.identity(path) for path in files}

    @staticmethod
    def identity(path):
        value = str(Path(path).resolve()).casefold()
        return value.removeprefix("\\\\?\\")

    def find_spec(self, fullname, path=None, target=None):
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if spec is None:
            return None
        check(spec.origin is not None and self.identity(spec.origin) in self.files,
              "BOOTSTRAP_IMPORT_FORBIDDEN")
        check(not isinstance(spec.loader, importlib.machinery.SourcelessFileLoader),
              "BOOTSTRAP_BYTECODE_FORBIDDEN")
        if isinstance(spec.loader, importlib.machinery.SourceFileLoader):
            spec.loader = SealedSourceLoader(spec.name, spec.origin)
        return spec


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    check(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, "BOOTSTRAP_PYTHON_FLAGS")
    manifest = read_manifest(args.manifest, args.sha256)
    check(Path(sys.executable).samefile(manifest["python"]), "BOOTSTRAP_INTERPRETER")
    with FileLease(manifest["inventory"]) as lease:
        sys.path[:] = manifest["python_paths"]
        sys.meta_path.insert(0, SealedImports(lease.paths))
        from mcbench.broker_stdio import run_config
        run_config(Path(manifest["broker_config"]), integrity_guard=lease.recheck,
                   bootstrap_digest=args.sha256)


if __name__ == "__main__":
    main()
