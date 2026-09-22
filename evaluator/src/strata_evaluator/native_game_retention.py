"""Read-only joins for the explicit stopped-component development profiles."""

from mcbench.budgets import Budgets
from mcbench.inference_transport import strict_json
from mcbench.native_checkpoint import NativeCheckpointState, check_files
from mcbench.native_export import OPERATOR, inspect_native_export, private_json
from mcbench.native_game_retention import GameRetention
from mcbench.storage import digest, require
from mcbench.vanilla_persistence import verify_snapshot


def inspect_retention(db, cas, bundle, native, intent):
    plan = intent["plan"]
    if plan["schema"] == "strata/M0NativeGameSmoke/1":
        require("retention_source" not in plan and "run/retention-input.json" not in bundle.files,
                "NATIVE_GAME_RETENTION_PROFILE")
        return {"preregistered": False, "complete_checkpoint": False}
    require(plan["schema"] in {"strata/M0NativeGameSmoke/2", "strata/M0NativeGameSmoke/3",
                              "strata/M0NativeGameSmoke/4", "strata/M0NativeGameSmoke/5"},
            "NATIVE_GAME_RETENTION_PROFILE")
    anchor = plan["retention_source"]["sha256"]
    retention = GameRetention({"path": str(bundle.path("run/retention-input.json")), "sha256": anchor})
    retention.check_scope(native.model_dump())
    retention.check_identity(**{k: getattr(native, k) for k in
        ("model", "dovetail_commit", "binary_digest", "binary_version", "helper_limit")})
    require(all(cas.read(OPERATOR, "operator", ref) == text.encode()
                for ref, text in retention.body["objects"].items()), "NATIVE_GAME_RETENTION_INPUT")
    report = bundle.json("run/native-result.json")["retention"]
    require(bundle.json("run/result.json")["native_retention"] == report
            and private_json(db, cas, report["input_ref"]) == retention.body
            and report["input_ref"] == "cas:sha256:" + anchor, "NATIVE_GAME_RETENTION_INPUT")
    c, a = retention.config, retention.agent
    require(db.execute("SELECT simulation FROM controller_profile").fetchone()[0] == 1,
            "NATIVE_GAME_RETENTION_PROFILE")
    row = db.execute("SELECT * FROM campaigns WHERE id=?", (c.campaign_id,)).fetchone()
    require(row is not None and row["state"] == "DRAFT" and strict_json(row["config"]) == c.model_dump()
            and strict_json(row["agents"]) == [a.model_dump()], "NATIVE_GAME_RETENTION_INPUT")
    row = db.execute("SELECT * FROM native_retention_policies WHERE campaign=? AND agent=?",
                     (c.campaign_id, a.agent_id)).fetchone()
    require(row is not None and row["ref"] == a.memory_policy and strict_json(row["config"]) == c.model_dump()
            and strict_json(row["agent_config"]) == a.model_dump(), "NATIVE_GAME_RETENTION_INPUT")
    registered = db.execute("SELECT cursor FROM outbox WHERE kind='native.retention_registered' AND "
        "json_extract(body,'$.campaign')=? AND json_extract(body,'$.agent')=? AND "
        "json_extract(body,'$.policy_ref')=?", (c.campaign_id, a.agent_id, a.memory_policy)).fetchall()
    prepared = db.execute("SELECT cursor FROM outbox WHERE kind='runtime.prepared' AND "
        "json_extract(body,'$.job_id')=?", (native.job_id,)).fetchall()
    require(len(registered) == len(prepared) == 1 and registered[0][0] < prepared[0][0],
            "NATIVE_RETENTION_TOO_LATE")
    export = inspect_native_export(db, cas, report["source_export"], simulation=True)
    require(export.job_id == native.job_id, "NATIVE_GAME_RETENTION_INPUT")
    state = NativeCheckpointState.model_validate(private_json(db, cas, report["component_ref"]))
    require(state.model_dump() == report["component"] and state.is_example is True
            and state.checkpoint_id == native.job_id + "-stopped" and state.campaign_id == c.campaign_id
            and state.agent_id == a.agent_id and state.source_epoch == native.epoch
            and state.system_digest == c.system_digest and state.profile_digest == native.profile_digest()
            and state.model_identity == native.model and state.source_export == report["source_export"]
            and state.retention_policy == a.memory_policy and state.boundary == "recovery",
            "NATIVE_GAME_RETENTION_COMPONENT")
    row = db.execute("SELECT ref FROM native_checkpoint_states WHERE checkpoint=? AND agent=?",
                     (state.checkpoint_id, a.agent_id)).fetchone()
    require(row is not None and row[0] == report["component_ref"], "NATIVE_CHECKPOINT_UNCOMMITTED")
    inventory = private_json(db, cas, export.root_artifacts)
    files = {x["path"]: x["ref"] for x in inventory["files"]}
    # This fixed conformance profile does not publish/activate learned skills.
    require(not any(p.startswith(("skills/", "active/")) for p in files), "NATIVE_GAME_RETENTION_PROFILE")
    initial = private_json(db, cas, a.initial_skills)["files"]
    require({p: r for p, r in files.items() if p.split('/')[0] in {"initial", "docs", "supplied"}} == initial,
            "NATIVE_INITIAL_CHANGED")
    require(private_json(db, cas, state.workspace) == {"schema": "strata/NativeRetainedArtifacts/1",
        "kind": "workspace", "files": files, "activates_skills": False}
        and private_json(db, cas, state.skills) == {"schema": "strata/NativeRetainedArtifacts/1",
        "kind": "skill_drafts", "files": {}, "activates_skills": False}, "NATIVE_RETENTION_CHANGED")
    check_files(cas, files)
    accounting = private_json(db, cas, export.accounting_ref)
    expected_accounts = []
    for account in Budgets.ancestors(db, native.account):
        amounts, uncertain = Budgets.totals(db, account["id"])
        expected_accounts.append({"identity": dict(account), "committed_and_reserved": amounts, "uncertain": uncertain})
    require(accounting["accounts"] == expected_accounts and accounting["ledger_cursor"] ==
            db.execute("SELECT coalesce(max(rowid),0) FROM ledger").fetchone()[0], "NATIVE_EXPORT_LEDGER")
    require(report == {"schema": "strata/NativeGameRetentionResult/1", "input_ref": report["input_ref"],
        "input_sha256": anchor, "campaign_digest": digest(c.model_dump()), "component_ref": report["component_ref"],
        "source_export": report["source_export"], "component": state.model_dump(), "model_evidence": "synthetic_provider",
        "controller_state": "DRAFT", "cost_rollback": False, "complete_checkpoint": False,
        "dispatch_authorized": False, "pack_qualified": False, "G0": "fail"}, "NATIVE_GAME_RETENTION_COMPONENT")
    result = {"preregistered": True, "component_ref": report["component_ref"], "input_sha256": anchor,
            "source_epoch": native.epoch, "retained_files": len(files), "costs_preserved": True,
            "complete_checkpoint": False}
    if plan["schema"] in {"strata/M0NativeGameSmoke/4", "strata/M0NativeGameSmoke/5"}:
        require(c.pack_lock == plan["pack"]["lock"], "NATIVE_GAME_RETENTION_INPUT")
        result["pack_lock_ref"] = c.pack_lock
        if plan["schema"] == "strata/M0NativeGameSmoke/5":
            from mcbench.pack_launch import parse_pack_binding
            from mcbench.pack_restore import baseline_record
            require(strict_json(retention.body["objects"][c.world_baseline]) == baseline_record(parse_pack_binding(plan["pack"])),
                    "NATIVE_GAME_RETENTION_INPUT")
    return result


def inspect_stopped_components(bundle, retention, server, server_plan, result):
    if not retention["preregistered"]:
        require("joint_components" not in result and "stopped_snapshot" not in server,
                "NATIVE_GAME_RETENTION_PROFILE")
        return retention
    sealed = server_plan["schema"] in {"strata/DevelopmentServer/4", "strata/DevelopmentServer/5"}
    require(sealed or server_plan["schema"] == "strata/DevelopmentServer/2", "NATIVE_GAME_RETENTION_PROFILE")
    snapshot = server["stopped_snapshot"]
    # Archived absolute paths are never used as read authority.
    stopped = verify_snapshot(bundle.path("run/server/stopped-instance/manifest.json").parent,
                              snapshot["manifest_sha256"])
    require(stopped["server_plan_digest"] == digest(server_plan), "NATIVE_GAME_RETENTION_INPUT")
    if sealed:
        lock = bundle.json("run/pack-lock.json")
        require(stopped["schema"] == "strata/StoppedVanillaSnapshot/2"
                and stopped["pack"]["lock"] == server_plan["pack"]["lock"] == retention.get("pack_lock_ref")
                and stopped["pack"]["request_id"] == server_plan["pack"]["request_id"] == lock["lock_id"]
                and stopped["pack"]["inventory_digest"] == lock["installed_root_digest"]
                and stopped["installed_inventory"] == bundle.json("run/pack-inventory.json"),
                "NATIVE_GAME_RETENTION_INPUT")
    else:
        require(stopped["schema"] == "strata/StoppedVanillaSnapshot/1", "NATIVE_GAME_RETENTION_PROFILE")
    joint = {"schema": "strata/NativeGameStoppedComponents/1", "native_component": retention["component_ref"],
        "snapshot_sha256": snapshot["manifest_sha256"], "retention_input_sha256": retention["input_sha256"],
        "complete_checkpoint": False, "dispatch_authorized": False, "G0": "fail"}
    require(bundle.json("run/joint-components.json") == result["joint_components"] == joint,
            "NATIVE_GAME_RETENTION_COMPONENT")
    return retention | {"stopped_world_captured": True, "snapshot_sha256": snapshot["manifest_sha256"],
        "state_files": sum(e["disposition"] == "state" for e in stopped["files"].values()),
        "clean_save_proven": False, "writer_custody_qualified": False}
