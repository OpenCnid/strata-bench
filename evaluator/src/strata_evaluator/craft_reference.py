"""Private prelaunch fixture seal and authenticated craft-evidence join.

This verifies bytes, a registered Strata roster and native resource witnesses.
It never turns an operator setup assertion into scoring/mechanics qualification.
Keep this service/database, all paths, keys and reports outside gameplay access.
"""

import argparse
import hashlib
import json
import os
import shutil
import stat
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from mcbench.contracts import Digest, Id, Positive, Strict, UInt
from mcbench.inference_transport import strict_json
from mcbench.storage import Database, canonical, digest, reject_links, require, safe_relative

from .scorer import Predicate
from .telemetry_auth import (
    BoundSpoolAuthority, inspect_authenticated_spool, issue_authority, parse_authority, private_read,
)

MAX_PLAN_BYTES = 32 * 1024**2
Actor = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")]


class FilePin(Strict):
    sha256: Digest
    bytes: UInt


class PrivateFile(FilePin):
    path: str


class CraftReferencePlan(Strict):
    schema_: Literal["strata/PrivateCraftReferencePlan/1"] = Field(alias="schema")
    instance_id: Id
    campaign_id: Id
    epoch: Positive
    start_server_tick: UInt
    cutoff_server_tick: Positive
    evidence_kind: Literal["synthetic", "authentic_operator_reference"]
    team_id: Id
    roster: dict[Id, Actor] = Field(min_length=1)
    predicate: Predicate
    game_directory: str
    fixture_directory: str
    fixture_files: dict[str, FilePin] = Field(min_length=1)
    supporting_files: dict[Id, PrivateFile] = Field(min_length=1)
    recipe_digests: dict[str, Digest] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent(self):
        require(self.start_server_tick < self.cutoff_server_tick, "CRAFT_TICK_WINDOW")
        require(len(set(self.roster.values())) == len(self.roster), "CRAFT_ROSTER_DUPLICATE")
        require(self.predicate.kind == "craft" and self.predicate.team_id == self.team_id
                and set(self.predicate.actors) == set(self.roster.values())
                and len(self.predicate.actors) == len(self.roster)
                and set(self.predicate.recipes) == set(self.recipe_digests), "CRAFT_SETUP_SCOPE")
        seen = set()
        for name in self.fixture_files:
            safe_relative(name)
            require(name.casefold() not in seen, "PATH_COLLISION")
            seen.add(name.casefold())
        game, fixture = private_path(self.game_directory), private_path(self.fixture_directory)
        require(fixture != game and fixture.is_relative_to(game), "CRAFT_FIXTURE_SCOPE")
        return self


def private_path(value):
    path = Path(value)
    require(path.is_absolute(), "CRAFT_PRIVATE_PATH")
    reject_links(path)
    require(not any((parent / ".git").exists() for parent in (path, *path.parents)),
            "CRAFT_PRIVATE_PATH")
    return path.resolve()


def check_file(path, pin):
    reject_links(path)
    require(path.is_file(), "CRAFT_FILE_CHANGED")
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == pin.bytes,
            "CRAFT_FILE_CHANGED")
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    require(actual == pin.sha256 and path.stat().st_size == pin.bytes, "CRAFT_FILE_CHANGED")


def check_tree(root, pins):
    require(root.is_dir(), "CRAFT_FIXTURE_MISSING")
    found = set()
    for folder, directories, files in os.walk(root, followlinks=False):
        for name in directories:
            reject_links(Path(folder) / name)
        for name in files:
            path = Path(folder) / name
            relative = path.relative_to(root).as_posix()
            require(relative in pins and relative not in found,
                    "CRAFT_FIXTURE_INVENTORY_CHANGED")
            check_file(path, pins[relative])
            found.add(relative)
    require(found == set(pins), "CRAFT_FIXTURE_INVENTORY_CHANGED")


def check_setup(plan):
    """Complete selected fixture tree, not an arbitrary partial file allowlist.

    The controller must separately hold launch ownership/leases; scans do not
    claim protection against a concurrent writer or identify the launched world.
    """
    check_tree(private_path(plan.fixture_directory), plan.fixture_files)
    for pin in plan.supporting_files.values():
        check_file(private_path(pin.path), pin)
    return {"files": len(plan.fixture_files), "bytes": sum(pin.bytes for pin in plan.fixture_files.values()),
            "supporting_files": len(plan.supporting_files)}


def copy_pinned(source, target, pin):
    check_file(source, pin)
    reject_links(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    reject_links(target)
    with source.open("rb") as original, target.open("xb") as output:
        total = 0
        while chunk := original.read(1024**2):
            total += len(chunk)
            require(total <= pin.bytes, "CRAFT_FILE_CHANGED")
            output.write(chunk)
        output.flush()
        os.fsync(output.fileno())
    check_file(target, pin)


def check_archive(directory, plan):
    check_tree(directory / "fixture", plan.fixture_files)
    check_tree(directory / "supporting", {digest(role): pin for role, pin in plan.supporting_files.items()})


def write_new(path, body):
    with path.open("xb") as stream:
        stream.write(canonical(body) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


class CraftReferenceStore:
    def __init__(self, database):
        private_path(database.path)
        self.database = database
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS craft_reference_seals (instance TEXT PRIMARY KEY, "
                       "digest TEXT NOT NULL, body TEXT NOT NULL, authority TEXT NOT NULL, path TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS craft_reference_imports (instance TEXT PRIMARY KEY, "
                       "spool TEXT NOT NULL, body TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS craft_reference_launches (instance TEXT PRIMARY KEY, "
                       "body TEXT NOT NULL)")

    def seal(self, plan, directory):
        plan = CraftReferencePlan.model_validate(plan)
        body = plan.model_dump(by_alias=True)
        require(len(canonical(body)) <= MAX_PLAN_BYTES, "ARTIFACT_QUOTA")
        directory = private_path(directory)
        require(not self.database.path.is_relative_to(private_path(plan.game_directory)),
                "CRAFT_PRIVATE_PATH")
        require(not directory.exists(), "CRAFT_SEAL_EXISTS")
        check = check_setup(plan)
        copied_bytes = check["bytes"] + sum(pin.bytes for pin in plan.supporting_files.values())
        require(shutil.disk_usage(directory.parent).free >= copied_bytes + 5 * 1024**3,
                "CRAFT_STORAGE_RESERVE_LOW")
        with self.database.transaction() as db:
            require(db.execute("SELECT 1 FROM craft_reference_seals WHERE instance=?",
                               (plan.instance_id,)).fetchone() is None, "CRAFT_SEAL_EXISTS")
            authority = issue_authority(directory, Path(plan.game_directory),
                instance_id=plan.instance_id, campaign_id=plan.campaign_id, epoch=plan.epoch,
                setup_digest=digest(body))
            # Commit the complete plan before the DB grant. Crash remnants are
            # deliberately retained; neither a used nor partial grant is renewed.
            write_new(directory / "setup.json", body)
            for name, pin in plan.fixture_files.items():
                copy_pinned(Path(plan.fixture_directory) / name, directory / "fixture" / name, pin)
            for role, pin in plan.supporting_files.items():
                copy_pinned(Path(pin.path), directory / "supporting" / digest(role), pin)
            check_archive(directory, plan)
            check_setup(plan)
            require(not Path(authority.key_file + ".claimed").exists(), "CRAFT_GRANT_ALREADY_USED")
            db.execute("INSERT INTO craft_reference_seals VALUES (?,?,?,?,?)",
                       (plan.instance_id, digest(body), canonical(body).decode(),
                        authority.fingerprint(), str(directory / "authority.json")))
            self.database.event(db, "private.craft_reference_sealed", {"instance": plan.instance_id,
                "setup_digest": digest(body), "authority_digest": authority.fingerprint(),
                "evidence_kind": plan.evidence_kind, "qualified": False})
        return {"instance_id": plan.instance_id, "setup_digest": digest(body),
                "authority_digest": authority.fingerprint(), "checked": check,
                "scoring_authority_qualified": False}

    def _load(self, instance):
        row = self.database.connection.execute("SELECT * FROM craft_reference_seals WHERE instance=?",
                                               (instance,)).fetchone()
        require(row is not None, "CRAFT_SEAL_MISSING")
        plan = CraftReferencePlan.model_validate(strict_json(row["body"]))
        require(plan.instance_id == instance and not self.database.path.is_relative_to(
            private_path(plan.game_directory)), "CRAFT_SETUP_SCOPE")
        require(digest(plan.model_dump(by_alias=True)) == row["digest"], "CRAFT_SEAL_CHANGED")
        path = private_path(row["path"])
        setup = strict_json(private_read(path.with_name("setup.json"), MAX_PLAN_BYTES))
        require(digest(setup) == row["digest"], "CRAFT_SEAL_CHANGED")
        check_archive(path.parent, plan)
        authority = parse_authority(strict_json(private_read(path, 65536)))
        require(isinstance(authority, BoundSpoolAuthority) and authority.setup_digest == row["digest"]
                and authority.fingerprint() == row["authority"]
                and (authority.instance_id, authority.campaign_id, authority.epoch) ==
                    (instance, plan.campaign_id, plan.epoch), "CRAFT_AUTHORITY_CHANGED")
        return row, plan, authority, path

    def preflight(self, instance):
        row, plan, authority, _ = self._load(instance)
        require(not Path(authority.key_file + ".claimed").exists(), "CRAFT_GRANT_ALREADY_USED")
        key = private_read(authority.key_file, 32)
        require(len(key) == 32 and hashlib.sha256(key).hexdigest() == authority.key_sha256,
                "TELEMETRY_AUTH_KEY_CHANGED")
        check = check_setup(plan)
        require(not Path(authority.key_file + ".claimed").exists(), "CRAFT_GRANT_ALREADY_USED")
        result = {"setup_digest": row["digest"], "authority_digest": row["authority"], "checked": check,
                "ready_for_operator_reference": True, "campaign_admission": False,
                "launch_ownership_qualified": False}
        with self.database.transaction() as db:
            require(db.execute("SELECT 1 FROM craft_reference_launches WHERE instance=?",
                               (instance,)).fetchone() is None, "CRAFT_LAUNCH_ALREADY_RESERVED")
            require(not Path(authority.key_file + ".claimed").exists(), "CRAFT_GRANT_ALREADY_USED")
            db.execute("INSERT INTO craft_reference_launches VALUES (?,?)", (instance, canonical(result).decode()))
            self.database.event(db, "private.craft_reference_launch_reserved", {"instance": instance, **result})
        return result

    def inspect(self, instance, spool):
        row, plan, _, path = self._load(instance)
        require(not private_path(spool).is_relative_to(private_path(plan.game_directory)),
                "CRAFT_PRIVATE_PATH")
        launch = self.database.connection.execute("SELECT body FROM craft_reference_launches WHERE instance=?",
                                                   (instance,)).fetchone()
        require(launch is not None, "CRAFT_LAUNCH_UNREGISTERED")
        launch_body = strict_json(launch["body"])
        require(launch_body["setup_digest"] == row["digest"] and launch_body["authority_digest"] == row["authority"],
                "CRAFT_LAUNCH_CHANGED")
        report = inspect_authenticated_spool(Path(spool), path)
        accepted, rejected, output = [], [], 0
        recipe_checks = {name: name in report["recipe_snapshots"] and digest(report["recipe_snapshots"][name]) == expected
                         for name, expected in plan.recipe_digests.items()}
        # No caller-supplied valid_setup/team_id/expert_mode or derived witnesses.
        # Recompute the native witness and exact recipe from the signed bytes.
        for witness in report["craft_witnesses"]:
            reason = None
            if witness["resource_witness"] != "pass":
                reason = witness["error_code"]
            elif witness["actor_id"] not in plan.roster.values():
                reason = "CRAFT_WRONG_ROSTER"
            elif not plan.start_server_tick <= witness["server_tick"] <= plan.cutoff_server_tick:
                reason = "CRAFT_OUTSIDE_TICK_WINDOW"
            elif not all(recipe_checks.values()) or witness["recipe_id"] not in plan.recipe_digests or digest(
                    report["recipe_snapshots"][witness["recipe_id"]]) != plan.recipe_digests[witness["recipe_id"]]:
                reason = "CRAFT_RECIPE_CHANGED"
            elif witness["item_id"] != plan.predicate.item_id or not all(
                    witness["consumed"].get(k, 0) >= v for k, v in plan.predicate.ingredients.items()):
                reason = "CRAFT_PREDICATE_MISMATCH"
            if reason:
                rejected.append({"transaction_id": witness["transaction_id"], "reason": reason})
            else:
                accepted.append(witness)
                output += witness["count"]
        result = {"schema": "strata/PrivateCraftReferenceInspection/1", "visibility": "evaluator",
            "instance_id": instance, "campaign_id": plan.campaign_id, "epoch": plan.epoch,
            "evidence_kind": plan.evidence_kind, "setup_digest": row["digest"],
            "predicate_digest": digest(plan.predicate.model_dump()), "team_id": plan.team_id,
            "team_binding": "registered_strata_roster", "authority_digest": row["authority"],
            "start_server_tick": plan.start_server_tick, "cutoff_server_tick": plan.cutoff_server_tick,
            "recipe_bindings": recipe_checks,
            "server_boot_id": report["server_boot_id"], "spool_sha256": report["file_sha256"],
            "candidate_output": output, "candidate_complete": output >= plan.predicate.minimum_output,
            "accepted_resource_witnesses": accepted, "rejected_resource_witnesses": rejected,
            "telemetry_authentication_verified": True, "scoring_eligible": False,
            "scoring_authority_qualified": False, "setup_mechanics_qualified": False,
            "launch_ownership_qualified": False, "gate_result": "not_run"}
        # Legacy source-only references retain their original report shape.
        # A tracked dispatch may not be replaced by that weaker path after an
        # uncertain launch, failed identity binding or incomplete stop.
        if self.database.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                                            "AND name='reference_dispatches'").fetchone():
            dispatch = self.database.connection.execute("SELECT * FROM reference_dispatches WHERE instance=?",
                                                         (instance,)).fetchone()
            if dispatch:
                body = strict_json(dispatch["body"])
                require(dispatch["state"] == "STOPPED" and body.get("launch_binding_verified") is True
                        and body.get("spool_sha256") == report["file_sha256"]
                        and body.get("binding", {}).get("native_observation") == report.get("launch_identity"),
                        "CRAFT_LAUNCH_UNQUALIFIED")
                result.update(launch_binding_verified=True, launch_plan_digest=body["plan_digest"])
        with self.database.transaction() as db:
            old = db.execute("SELECT * FROM craft_reference_imports WHERE instance=?", (instance,)).fetchone()
            if old:
                require(old["spool"] == report["file_sha256"] and old["body"] == canonical(result).decode(),
                        "CRAFT_IMPORT_CONFLICT")
                return json.loads(old["body"])
            db.execute("INSERT INTO craft_reference_imports VALUES (?,?,?)",
                       (instance, report["file_sha256"], canonical(result).decode()))
            self.database.event(db, "private.craft_reference_imported", result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    seal = commands.add_parser("seal")
    seal.add_argument("--plan", required=True, type=Path)
    seal.add_argument("--directory", required=True, type=Path)
    for verb in ("preflight", "inspect"):
        command = commands.add_parser(verb)
        command.add_argument("--instance", required=True)
        if verb == "inspect":
            command.add_argument("--spool", required=True, type=Path)
            command.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "seal":
        plan = CraftReferencePlan.model_validate(strict_json(private_read(args.plan, MAX_PLAN_BYTES)))
        require(not private_path(args.database).is_relative_to(private_path(plan.game_directory))
                and not private_path(args.plan).is_relative_to(private_path(plan.game_directory)),
                "CRAFT_PRIVATE_PATH")
    database = Database(private_path(args.database))
    try:
        store = CraftReferenceStore(database)
        if args.command == "seal":
            result = store.seal(plan, args.directory)
        elif args.command == "preflight":
            result = store.preflight(args.instance)
        else:
            _, plan, _, authority = store._load(args.instance)
            output = private_path(args.output)
            require(not output.is_relative_to(private_path(plan.game_directory))
                    and not output.is_relative_to(authority.parent), "CRAFT_PRIVATE_PATH")
            require(not output.exists(), "CRAFT_REPORT_EXISTS")
            report = store.inspect(args.instance, args.spool)
            write_new(output, {"schema": "strata/ReportArtifact/1", "content_digest": digest(report), "report": report})
            result = {"digest": digest(report), "report_bytes": len(canonical(report))}
        print(json.dumps(result))
    finally:
        database.close()


if __name__ == "__main__":
    main()
