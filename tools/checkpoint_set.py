"""Stage or verify a complete private checkpoint set; never start a game or model.

Configuration comes from the durable campaign, not caller-provided overrides.
Verification is a point-in-time staging check, not runtime restore qualification.
"""

import argparse
import json
from pathlib import Path

from mcbench.checkpoints import Checkpoints
from mcbench.records import CampaignConfig
from mcbench.storage import CAS, Database, Fault, reject_links, require


def run(database, objects, checkpoint_id, epoch, directory, *, verify):
    for path in (database, objects, directory):
        reject_links(path.absolute())
    require(database.is_file() and objects.is_dir(), "CHECKPOINT_STORE_MISSING")
    db = Database(database)
    try:
        service = Checkpoints(db, CAS(db, objects))
        manifest, _ = service.load(checkpoint_id)
        row = db.connection.execute("SELECT config FROM campaigns WHERE id=?", (manifest.campaign_id,)).fetchone()
        require(row is not None, "CHECKPOINT_IDENTITY")
        config = CampaignConfig.model_validate_json(row[0])
        method = service.verify_set if verify else service.materialize_set
        return method(checkpoint_id, config, epoch, directory)
    finally:
        db.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--materialize", action="store_true")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--objects", type=Path, required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--epoch", type=int, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.database, args.objects, args.checkpoint, args.epoch, args.directory, verify=args.verify)
    except (Fault, OSError, ValueError) as error:
        print(json.dumps({"status": "fail", "code": error.code if isinstance(error, Fault) else type(error).__name__,
                          "dispatch_authorized": False}))
        return 1
    print(json.dumps({"status": "pass", **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
