"""Read-only preservation checks for explicit two-epoch development recovery."""

from collections import Counter
import math
import re

from mcbench.budgets import Budgets
from mcbench.contracts import Observation
from mcbench.inference_transport import strict_json
from mcbench.native import NativeLaunch
from mcbench.native_export import OPERATOR, private_json
from mcbench.storage import digest, require

from .saved_blocks import NbtReader, field, unpack_chunk


def rows(db, table, order="rowid"):
    require(re.fullmatch(r"[a-z_]+", table) and re.fullmatch(r"[a-z_,]+", order), "RECOVERY_TABLE_INVALID")
    return [tuple(r) for r in db.execute(f'SELECT * FROM "{table}" ORDER BY {order}')]


def native_history(db, previous, native, source):
    """Old rows stay byte-identical; new rows cannot hide a third run or refund."""
    old_schema = set(tuple(r) for r in previous.execute("SELECT type,name,sql FROM sqlite_master"))
    new_schema = set(tuple(r) for r in db.execute("SELECT type,name,sql FROM sqlite_master"))
    added = {("table", "native_recovery_projections", "CREATE TABLE native_recovery_projections "
        "(runtime TEXT, thread TEXT, component TEXT, PRIMARY KEY(runtime,thread))"),
        ("index", "sqlite_autoindex_native_recovery_projections_1", None)}
    require(old_schema <= new_schema and new_schema - old_schema <= added, "RECOVERY_NATIVE_SCHEMA")
    tables = [r[0] for r in previous.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    retained = 0
    for table in tables:
        before, after = rows(previous, table), rows(db, table)
        require(not Counter(before) - Counter(after), "RECOVERY_NATIVE_HISTORY_CHANGED")
        retained += len(before)
    for table in ("accounts", "campaigns", "native_retention_policies", "execution_authorizations"):
        require(rows(previous, table) == rows(db, table), "RECOVERY_AUTHORITY_CHANGED")
    before = [tuple(r) for r in previous.execute("SELECT rowid,* FROM ledger ORDER BY rowid")]
    after = [tuple(r) for r in db.execute("SELECT rowid,* FROM ledger ORDER BY rowid")]
    require(after[:len(before)] == before, "RECOVERY_LEDGER_CHANGED")
    old_jobs = {r[0] for r in previous.execute("SELECT id FROM native_jobs")}
    require(native.job_id not in old_jobs and {r[0] for r in db.execute("SELECT id FROM native_jobs")}
            == old_jobs | {native.job_id}, "RECOVERY_NATIVE_SCOPE")
    old_ops = {r[0] for r in previous.execute("SELECT id FROM operations")}
    new_ops = {r["id"] for r in source["operations"]}
    require(not old_ops & new_ops and {r[0] for r in db.execute("SELECT id FROM operations")} == old_ops | new_ops
            and {r["cursor"] for r in source["ledger"]} == {r[0] for r in after[len(before):]},
            "RECOVERY_LEDGER_CHANGED")
    return {"native_tables": len(tables), "native_rows": retained, "ledger_rows": len(before)}


def worker_history(db, previous, epoch):
    require(set(tuple(r) for r in db.execute("SELECT type,name,sql FROM sqlite_master"))
            == set(tuple(r) for r in previous.execute("SELECT type,name,sql FROM sqlite_master")),
            "RECOVERY_WORKER_SCHEMA")
    epochs = [r[0] for r in previous.execute("SELECT epoch FROM epochs ORDER BY epoch")]
    require(epochs and epoch == max(epochs) + 1
            and [r[0] for r in db.execute("SELECT epoch FROM epochs ORDER BY epoch")] == epochs + [epoch],
            "RECOVERY_WORKER_EPOCH")
    before, after = rows(previous, "events", "cursor"), rows(db, "events", "cursor")
    require(after[:len(before)] == before and [r[0] for r in after] == list(range(1, len(after) + 1)),
            "RECOVERY_WORKER_HISTORY_CHANGED")
    old_actions = rows(previous, "actions", "epoch,seq")
    current = list(db.execute("SELECT * FROM actions WHERE epoch!=? ORDER BY epoch,seq", (epoch,)))
    require([tuple(r) for r in current] == old_actions, "RECOVERY_WORKER_HISTORY_CHANGED")
    old_counter_rows, counter_rows = rows(previous, "counters"), rows(db, "counters")
    old_counters, counters = dict(old_counter_rows), dict(counter_rows)
    require(len(old_counters) == len(old_counter_rows) and len(counters) == len(counter_rows)
            and all(counters.get(k) == v for k, v in old_counters.items() if k not in {"primitive_events", "public_signal"})
            and set(counters) <= set(old_counters) | {f"{epoch}:action", f"{epoch}:ack", f"{epoch}:observation", "public_signal"},
            "RECOVERY_WORKER_COUNTERS")
    signals = [strict_json(r[2])["cursor"] for r in after if r[1] == "public_signal"]
    require(all(type(v) is int for v in signals) and signals == list(range(1, len(signals) + 1))
            and counters.get("public_signal", 0) == len(signals),
            "RECOVERY_WORKER_COUNTERS")
    return {"worker_events": len(before), "worker_actions": len(old_actions),
            "opening_primitive_events": old_counters["primitive_events"]}


def cumulative_usage(db, previous, native, model, prior_model):
    require(model["unit"] == prior_model["unit"], "RECOVERY_MIXED_UNITS")
    before, was_uncertain = Budgets.totals(previous, native.account)
    after, uncertain = Budgets.totals(db, native.account)
    mapped = {"input_tokens": "input_tokens", "output_tokens": "output_tokens",
              "model_calls": "model_calls", "spend_microusd": "amount"}
    require(not was_uncertain and not uncertain and set(before) == set(after)
            and all(before[k] == prior_model["totals"][v] for k, v in mapped.items())
            and all(after[k] == before[k] + (model["totals"][mapped[k]] if k in mapped else 0) for k in before),
            "RECOVERY_COSTS_CHANGED")
    return {key: prior_model["totals"][key] + model["totals"][key] for key in model["totals"]}


def parent_evidence(plan, bundle):
    from .evidence_bundle import EvidenceBundle
    from .native_game_evidence import bootstrap_inventory, inspect_native_game
    require(plan.epoch == plan.previous.epoch + 1 and plan.job_id != plan.previous.job_id
            and plan.campaign_id == plan.previous.campaign_id and plan.agent_id == plan.previous.agent_id,
            "RECOVERY_NATIVE_SCOPE")
    previous = EvidenceBundle(plan.previous.bundle, plan.previous.seal_sha256, inventory_extension=bootstrap_inventory)
    require(not previous.root.is_relative_to(bundle.root) and not bundle.root.is_relative_to(previous.root),
            "RECOVERY_SOURCE_ALIAS")
    current, old = bundle.json("run/intent.json")["plan"], previous.json("run/intent.json")["plan"]
    profiles = {"strata/M0NativeGameRecovery/2": "strata/M0NativeGameSmoke/3",
                "strata/M0NativeGameRecovery/3": "strata/M0NativeGameSmoke/5"}
    require(current["schema"] in profiles and old["schema"] == profiles[current["schema"]], "RECOVERY_PROFILE")
    reference = current["recovery_source"]
    require(set(reference) == ({"bundle", "seal_sha256"} if current["schema"].endswith('/3') else
            {"bundle", "seal_sha256", "template_directory"}) and reference["seal_sha256"] == plan.previous.seal_sha256,
            "RECOVERY_SOURCE_CHANGED")
    require(current["worker_runtime"] == old["worker_runtime"], "RECOVERY_RUNTIME_CHANGED")
    for name, entry in previous.files.items():
        if name.startswith("run/native/objects/"):
            require(bundle.files.get(name) == entry, "RECOVERY_NATIVE_OBJECT_CHANGED")
    return previous, inspect_native_game(plan.previous)


def source_record(bundle, previous, plan, worker, prior_retention):
    from .native_game_evidence import windows
    source = bundle.json("run/intent.json")["plan"]["recovery_source"]
    expected = {"source": source, "component": prior_retention["component_ref"],
        "original_outer_result": previous.json("run/result.json")["status"],
        "world_snapshot": prior_retention["snapshot_sha256"], "epoch": plan.epoch,
        "worker_rows_preserved": worker.execute("SELECT COUNT(*) FROM actions").fetchone()[0],
        "full_checkpoint": False, "G0": "fail"}
    require(bundle.json("run/recovery-source.json") == expected, "RECOVERY_SOURCE_CHANGED")
    require({name for name in bundle.files if name.startswith("run/worker/grant-")} ==
            {f"run/worker/grant-{plan.epoch}.json"}, "RECOVERY_CREDENTIAL_REUSED")
    if bundle.json("run/intent.json")["plan"]["schema"] == "strata/M0NativeGameRecovery/3":
        journal = "run/worker/actions.sqlite"
        restored = bundle.json("run/result.json")["sealed_worker_receipt"]["journal_restoration"]
        reference = restored["source"]
        require(windows(reference["path"]) == windows(source["bundle"]) / journal,
                "RECOVERY_SOURCE_CHANGED")
        sidecars = {suffix: {"bytes": previous.files[journal + suffix].bytes,
                             "sha256": previous.files[journal + suffix].sha256}
                    for suffix in ("-wal", "-shm", "-journal") if journal + suffix in previous.files}
        require(restored == {"schema": "strata/WorkerJournalRestoration/1", "source": {
            "path": reference["path"], "sha256": previous.files[journal].sha256,
            "campaign_id": plan.previous.campaign_id, "agent_id": plan.previous.agent_id, "epoch": plan.previous.epoch},
            "retained": {"epochs": [r[0] for r in worker.execute("SELECT epoch FROM epochs ORDER BY epoch")],
                "action_rows": expected["worker_rows_preserved"],
                "event_rows": worker.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                "primitive_events": worker.execute("SELECT value FROM counters WHERE name='primitive_events'").fetchone()[0]},
            "old_grant_restored": False, "source_sidecars": sidecars, "sidecars_copied": False,
            "held_until_launch_handoff": True, "writer_custody_qualified": False}, "RECOVERY_JOURNAL_HANDOFF")


def player_matches(player, state):
    positions, rotations = field(player, "Pos", 9), field(player, "Rotation", 9)
    require(positions[0] == 6 and len(positions[1]) == 3 and rotations[0] == 5
            and len(rotations[1]) == 2, "GAME_RECOVERY_PLAYER")
    position, rotation = ([t.value for t in value[1]] for value in (positions, rotations))
    require(all(math.isfinite(v) for v in position + rotation), "GAME_RECOVERY_PLAYER")
    items = field(player, "Inventory", 9)
    require(items[0] == 10 or items[0] == 0 and not items[1], "GAME_RECOVERY_PLAYER")
    inventory = {}
    for item in items[1]:
        slot = field(item.value, "Slot", 1)
        # Player NBT uses a different namespace from protocol window slots.
        # In particular NBT 36 must not alias hotbar slot 0 after conversion.
        require(0 <= slot <= 35 or 100 <= slot <= 103 or slot == -106, "GAME_RECOVERY_PLAYER")
        slot = slot + 36 if 0 <= slot <= 8 else 45 if slot == -106 else 108 - slot if 100 <= slot <= 103 else slot
        require(5 <= slot <= 45 and slot not in inventory, "GAME_RECOVERY_PLAYER")
        item_id, count = field(item.value, "id", 8), field(item.value, "Count", 1)
        require(re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", item_id) is not None
                and item_id != "minecraft:air" and 1 <= count <= 127, "GAME_RECOVERY_PLAYER")
        inventory[slot] = (item_id, count)
    observed, seen = {}, set()
    for item in state["inventory"]:
        slot, count = item["slot"], item["count"]
        require(type(slot) is int and 0 <= slot <= 45 and slot not in seen
                and type(count) is int and 0 <= count <= 127, "GAME_RECOVERY_PLAYER")
        seen.add(slot)
        if count:
            require(5 <= slot <= 45, "GAME_RECOVERY_PLAYER")
            observed[slot] = (item["item_id"], count)
    yaw = (180 - math.degrees(state["yaw"]) + 180) % 360 - 180
    return (state["connected"] and state["dimension"] == field(player, "Dimension", 8)
        and state["health"] == field(player, "Health", 5) and state["food"] == field(player, "foodLevel", 3)
        and inventory == observed and abs((rotation[0] - yaw + 180) % 360 - 180) <= .01
        and abs(rotation[1] + math.degrees(state["pitch"])) <= .01
        and all(abs(position[i] - state["position"][axis]) <= .01 for i, axis in enumerate(("x", "y", "z"))))


def restored_state(bundle, previous, plan, db, cas, native, source, retention, prior_retention):
    """Join restored player, native component, clean helper and original policy."""
    prior_native = NativeLaunch.model_validate_json(db.execute("SELECT plan FROM native_jobs WHERE id=?",
                                                              (plan.previous.job_id,)).fetchone()[0])
    require(native.resume_component_ref == prior_retention["component_ref"] and native.account == prior_native.account
            and all(getattr(native, k) == getattr(prior_native, k) for k in
                    ("model", "binary_digest", "binary_version", "dovetail_commit", "helper_limit")),
            "RECOVERY_NATIVE_SCOPE")
    require(bundle.read("run/retention-input.json") == previous.read("run/retention-input.json")
            and bundle.read("run/player-before.dat") == previous.read("run/player-after.dat"), "RECOVERY_SOURCE_CHANGED")
    player = NbtReader(unpack_chunk(previous.read("run/player-after.dat"), 1)).root()
    initial = bundle.json("run/initial-observation.json")
    require(initial["status"] == "ok", "RECOVERY_PLAYER_CHANGED")
    observation = Observation.model_validate(initial["result"])
    require(not observation.is_example and observation.mode == "structured" and observation.state is not None
            and all(getattr(observation, k) == getattr(plan, k) for k in ("campaign_id", "agent_id", "epoch"))
            and player_matches(player, observation.state.model_dump()) and observation.last_action_seq is None
            and observation.state.active_request_id is None, "RECOVERY_PLAYER_CHANGED")
    old_grant = previous.json(f"run/worker/grant-{plan.previous.epoch}.json")
    grant = bundle.json(f"run/worker/grant-{plan.epoch}.json")
    require(grant["token"] != old_grant["token"] and grant["epoch"] == old_grant["epoch"] + 1
            and bundle.json("run/worker-config.json")["lease_id"] != previous.json("run/worker-config.json")["lease_id"],
            "RECOVERY_CREDENTIAL_REUSED")
    start = bundle.json("run/recovery-start.json")
    expected_negative = {}
    for name, code in (("old_token", "FORBIDDEN"), ("old_epoch", "STALE_EPOCH")):
        value = start["negative_requests"][name]
        require(value == {"schema": "strata/GameResponse/1", "status": "error", "error": {
            "code": code, "message": code, "retryable": False, "retry_after_ms": None,
            "request_id": None if name == "old_token" else "recovery-denied-" + name,
            "expected_epoch": plan.epoch, "details_ref": None}},
                "RECOVERY_STALE_ACCEPTED")
        expected_negative[name] = value
    require(start == {"own_saved_state_matches": True, "no_action_replayed": True,
        "negative_requests": expected_negative, "original_outer_result": previous.json("run/result.json")["status"],
        "full_checkpoint": False}, "RECOVERY_SOURCE_CHANGED")
    prior_component = private_json(db, cas, prior_retention["component_ref"])
    component = private_json(db, cas, retention["component_ref"])
    old_files = private_json(db, cas, prior_component["workspace"])["files"]
    files = private_json(db, cas, component["workspace"])["files"]
    old_note, new_note = old_files["notes/root.md"], files["notes/root.md"]
    require(old_note != new_note and cas.read(OPERATOR, "operator", old_note) == b"STRATA_OWN_ARTIFACT"
            and cas.read(OPERATOR, "operator", new_note) == b"STRATA_RESTORED_AND_CONTINUED"
            and {k: v for k, v in files.items() if k != "notes/root.md"}
            == {k: v for k, v in old_files.items() if k != "notes/root.md"}, "RECOVERY_ARTIFACT_CHANGED")
    depths = {p["participant"]["thread"]: p["participant"]["depth"] for p in source["participants"]}
    reads = [(depths[strict_json(c["body"])["thread"]], c) for c in source["broker_calls"]
             if strict_json(c["body"])["tool"] == "artifact_read"
             and strict_json(c["body"])["arguments_digest"] == digest({"path": "notes/root.md"})]
    expected_read = digest({"path": "notes/root.md", "ref": old_note, "text": "STRATA_OWN_ARTIFACT"})
    require(any(depth == 0 and c["state"] == "RETURNED" and c["result_digest"] == expected_read for depth, c in reads)
            and any(depth == 1 and c["state"] == "REJECTED" and c["fault"] == "BROKER_FORBIDDEN" for depth, c in reads)
            and all(depth == 0 or c["state"] == "REJECTED" and c["fault"] == "BROKER_FORBIDDEN" for depth, c in reads),
            "RECOVERY_ARTIFACT_ACCESS")
    require(source["retained_projection"]["binding"]["component"] == prior_retention["component_ref"],
            "RECOVERY_NATIVE_SCOPE")
    return {"source_component": prior_retention["component_ref"], "saved_player_restored": True,
            "old_credentials_rejected": True, "root_artifact_continued": True, "helper_root_history_denied": True,
            "complete_checkpoint": False, "runtime_isolation_qualified": False}
