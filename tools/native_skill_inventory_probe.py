"""Inspect pinned installed Dovetail text without starting a model or game.

The output is private operator evidence. This metadata probe does not acquire
runtime file leases or qualify native invocation, script execution or isolation.
"""

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from mcbench.native_skills import OPERATOR, prepare_skill_corpus, read_skill_corpus, validate_skill_bootstrap
from mcbench.storage import CAS, Database, canonical, digest, reject_links


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.absolute()
    reject_links(output)
    output.mkdir(parents=True, exist_ok=False)
    database = Database(output / "controller.sqlite")
    try:
        cas = CAS(database, output / "cas")
        ref = prepare_skill_corpus(cas, args.installed_root, supporting_files=True)
        corpus = read_skill_corpus(cas, ref)
        inventory = cas.json(OPERATOR, "operator", corpus["source_inventory_ref"])
        manifest = {"schema": "strata/NativeBootstrap/1", "inventory": {"files": [
            {"path": str(args.installed_root.absolute() / path), "sha256": sha}
            for path, sha in inventory["files"].items()]}}
        raw = canonical(manifest)
        manifest_path = output / "static-bootstrap-inventory.json"
        manifest_path.write_bytes(raw)
        validate_skill_bootstrap(cas, ref, SimpleNamespace(bootstrap_manifest=str(manifest_path),
            bootstrap_digest=hashlib.sha256(raw).hexdigest()))
        audit = {"schema": "strata/NativeSkillInventoryAudit/1", "evidence_kind": "installed_source_metadata",
            "source_commit": corpus["source_commit"], "installed_tree_digest": corpus["installed_tree_digest"],
            "corpus_ref": ref, "policy": corpus["policy"], "projected_files": len(corpus["files"]),
            "projected_bytes": sum(len(f["text"].encode()) for f in corpus["files"]),
            "native_catalog_skill_count": len(corpus["bodies"]), "files_digest": corpus["files_digest"],
            "source_file_count": len(inventory["files"]), "acquired_runtime_leases": False,
            "native_invocation_verified": False, "executes_scripts": False, "model_requests": 0,
            "game_launches": 0}
        (output / "audit.json").write_bytes(canonical(audit))
        print(json.dumps(audit | {"audit_digest": digest(audit)}))
    finally:
        database.close()


if __name__ == "__main__":
    main()
