"""One-use preparation, in-custody seal and protected reference launch."""

import argparse
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from mcbench.contracts import Strict
from mcbench.inference_transport import strict_json
from mcbench.storage import Database, canonical, digest, require
from .craft_reference import (
    CraftReferencePlan, CraftReferencePlanV2, CraftReferenceStore, private_path, write_new,
)
from .reference_launch import ReferenceLaunchPlanV4, ReferenceLauncher, same_path
from .telemetry_auth import private_read
from .writer_preparation import WriterPreparationPlan, WriterPreparations


class ProtectedReferencePlan(Strict):
    schema_: Literal["strata/ProtectedReferencePlan/1"] = Field(alias="schema")
    preparation: WriterPreparationPlan
    setup: CraftReferencePlan | CraftReferencePlanV2
    launch: ReferenceLaunchPlanV4
    evidence_directory: str

    @model_validator(mode="after")
    def scope(self):
        prep, setup, launch = self.preparation, self.setup, self.launch
        evidence, workspace = private_path(self.evidence_directory), private_path(prep.workspace_directory)
        require(not evidence.is_relative_to(workspace) and not workspace.is_relative_to(evidence),
                "PROTECTED_REFERENCE_SCOPE")
        require(same_path(prep.evidence_directory, evidence / "preparation")
                and same_path(launch.evidence_directory, evidence / "launch")
                and same_path(setup.game_directory, workspace / "guarded")
                and same_path(setup.fixture_directory, workspace / "guarded/world"),
                "PROTECTED_REFERENCE_SCOPE")
        require(launch.custody_id == prep.id and launch.instance_id == setup.instance_id
                and launch.setup_digest == digest(setup.model_dump(by_alias=True))
                and same_path(launch.executable.path, prep.java.path), "PROTECTED_REFERENCE_BINDING")
        require(prep.evidence_kind == setup.evidence_kind == "synthetic"
                and launch.mode == "synthetic-fixture", "PROTECTED_REFERENCE_PROFILE_UNQUALIFIED")
        return self


class ProtectedReferences:
    def __init__(self, database):
        self.database = database
        private_path(database.path)
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS protected_references (instance TEXT PRIMARY KEY, "
                "workspace TEXT UNIQUE NOT NULL, plan TEXT NOT NULL, state TEXT NOT NULL, body TEXT NOT NULL)")

    def _record(self, instance, state, body):
        body["status"] = state.lower()
        with self.database.transaction() as db:
            db.execute("UPDATE protected_references SET state=?,body=? WHERE instance=?",
                       (state, canonical(body).decode(), instance))
            self.database.event(db, "private.protected_reference", {"instance": instance, "state": state, **body})

    def run(self, value):
        plan = ProtectedReferencePlan.model_validate(value)
        evidence, workspace = private_path(plan.evidence_directory), private_path(plan.preparation.workspace_directory)
        require(not evidence.exists() and not workspace.exists(), "PROTECTED_REFERENCE_OUTPUT_EXISTS")
        require(not private_path(self.database.path).is_relative_to(workspace), "PROTECTED_REFERENCE_SCOPE")
        instance = plan.setup.instance_id
        body = {"schema": "strata/ProtectedReferenceResult/1", "status": "intent",
            "plan_digest": digest(plan.model_dump(by_alias=True)), "evidence_kind": plan.setup.evidence_kind,
            "capability": "native-private-reference-custody/1", "scoring_eligible": False,
            "setup_authority_qualified": False, "model_calls": 0, "game_launched": False}
        with self.database.transaction() as db:
            require(db.execute("SELECT 1 FROM protected_references WHERE instance=? OR workspace=?",
                               (instance, str(workspace))).fetchone() is None, "PROTECTED_REFERENCE_ALREADY_RESERVED")
            db.execute("INSERT INTO protected_references VALUES(?,?,?,?,?)", (instance, str(workspace),
                canonical(plan.model_dump(by_alias=True)).decode(), "INTENT", canonical(body).decode()))
            self.database.event(db, "private.protected_reference", {"instance": instance, **body})
        try:
            evidence.mkdir()
            write_new(evidence / "plan.json", plan.model_dump(by_alias=True))
            store = CraftReferenceStore(self.database)
            launcher = ReferenceLauncher(store)
            def continue_reference(custody):
                custody.check()
                body["seal"] = store.seal(plan.setup, evidence / "authority")
                self._record(instance, "SEALED_IN_CUSTODY", body)
                custody.check()
                self._record(instance, "DISPATCHING", body)
                body["launch"] = launcher.run(plan.launch.model_dump(by_alias=True), custody=custody)
                require(body["launch"]["status"] == "stopped_reference",
                        body["launch"].get("error", "PROTECTED_REFERENCE_LAUNCH_UNCERTAIN"))
                require(custody.completed, "PROTECTED_REFERENCE_CUSTODY_UNCERTAIN")
                custody.check()
                self._record(instance, "DISPATCH_RETURNED", body)
            body["preparation"] = WriterPreparations(self.database).run(
                plan.preparation.model_dump(by_alias=True), continuation=continue_reference)
            require(body["preparation"]["status"] == "stopped_reference",
                    body["preparation"].get("error", "PROTECTED_REFERENCE_PREPARATION_UNCERTAIN"))
            require(not body["preparation"]["custody"]["live"], "PROTECTED_REFERENCE_CUSTODY_UNCERTAIN")
            self._record(instance, "STOPPED", body)
        except BaseException as error:
            body["error"] = getattr(error, "code", type(error).__name__)
            self._record(instance, "UNCERTAIN", body)
        finally:
            if evidence.exists():
                write_new(evidence / "result.json", body)
        return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    value = strict_json(private_read(private_path(args.plan), 32 * 1024**2))
    database = Database(private_path(args.database))
    try:
        result = ProtectedReferences(database).run(value)
        print(json.dumps({"status": result["status"], "error": result.get("error"), "scoring_eligible": False}))
        return 0 if result["status"] == "stopped" else 1
    finally:
        database.close()


if __name__ == "__main__":
    raise SystemExit(main())
