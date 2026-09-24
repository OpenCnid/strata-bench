"""Signed synthetic controls for the private D14 producer/scorer/report path."""

import json
from contextlib import closing

import pytest

from mcbench.storage import Database, Fault, canonical
from strata_evaluator.craft_reference import CraftReferenceStore
from strata_evaluator.development_milestone import build_report, main
from test_craft_reference import reference, seal  # noqa: F401
from test_setup_facts import native  # noqa: F401
from test_setup_history import history, histories, require_history  # noqa: F401


def prepare(fixture):
    require_history(fixture[1])
    seal(fixture)
    return fixture[0].database, fixture[4]


def counts(db):
    return tuple(db.connection.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] for table in
                 ("outbox", "game_events", "predicate_state", "scored_transaction_receipts",
                  "development_milestone_reports"))


def test_signed_craft_reaches_only_development_report_and_replays_once(history):  # noqa: F811
    db, spool = prepare(history)
    report = build_report(db, "i", spool)
    assert report["development_predicate_complete"] and report["development_output"] == 1
    assert report["evidence_kind"] == "synthetic" and report["scope_decision"] == "D14"
    assert all(report[k] is False for k in ("scoring_eligible", "scoring_authority_qualified",
        "setup_mechanics_qualified", "isolation_qualified", "scientific_claim", "campaign_admission"))
    assert report["G0"] == "fail" and report["visibility"] == "evaluator"
    begin = next(e for e in history[2] if e["kind"] == "craft_begin")
    event = report["derived_events"][0]
    assert all(event[k] == begin[k] for k in ("recorded_at", "seq", "server_event_seq", "server_tick",
                                             "server_boot_id", "actor_ids", "evidence_refs"))
    assert event["payload"]["consumed"] == {"minecraft:andesite": 5, "minecraft:polished_andesite": 3}
    assert json.loads(db.connection.execute("SELECT body FROM craft_reference_imports").fetchone()[0])[
        "scoring_eligible"] is False
    assert db.connection.execute("SELECT instance FROM predicate_state").fetchone()[0].startswith("m0dev-")
    prior = counts(db)
    with closing(Database(db.path)) as restarted:
        assert build_report(restarted, "i", spool) == report
        assert counts(restarted) == prior
    assert all(r[0].startswith("private.") for r in db.connection.execute("SELECT kind FROM outbox"))


@pytest.mark.parametrize("control", ["reverted-mode", "wrong-team", "wrong-mode", "operator",
                                    "outside-window", "insufficient-consumption", "wrong-output"])
def test_negative_controls_cannot_award_development_credit(history, control):  # noqa: F811
    _, plan, events, _, _ = history
    if control == "reverted-mode":
        for event in histories(events)[1:]:
            event["payload"]["attempts"]["world_mode"] = 2
    elif control == "wrong-team":
        plan["native_team_ids"]["agent"] = "44444444-4444-4444-4444-444444444444"
    elif control in {"wrong-mode", "operator"}:
        for event in events:
            if event["kind"] == "setup_snapshot" and event["payload"].get("actor"):
                if control == "operator":
                    event["payload"]["actor"]["is_operator"] = True
                else:
                    event["payload"]["pack"].update(mode="normal", is_expert=False, is_normal=True)
    elif control == "outside-window":
        plan["cutoff_server_tick"] = 19
    elif control == "insufficient-consumption":
        plan["predicate"]["ingredients"]["minecraft:andesite"] = 6
    else:
        plan["predicate"]["item_id"] = "minecraft:diamond"
    db, spool = prepare(history)
    report = build_report(db, "i", spool)
    assert not report["development_predicate_complete"] and report["development_output"] == 0
    assert report["rejected_resource_witnesses"] and report["derived_events"] == []
    assert db.connection.execute("SELECT COUNT(*) FROM predicate_state").fetchone()[0] == 0
    assert build_report(db, "i", spool) == report


def test_legacy_point_only_plan_cannot_be_used_as_history_qualification(native):  # noqa: F811
    seal(native)
    with pytest.raises(Fault, match="DEVELOPMENT_HISTORY_REQUIRED"):
        build_report(native[0].database, "i", native[4])


def test_changed_import_or_mac_cannot_replace_verified_source(history):  # noqa: F811
    db, spool = prepare(history)
    result = build_report(db, "i", spool)
    previous = counts(db)
    spool.write_bytes(spool.read_bytes().replace(b'"mac":"', b'"mac":"0', 1))
    with pytest.raises(Fault, match="TELEMETRY_AUTH_MAC"):
        build_report(db, "i", spool)
    assert counts(db) == previous
    assert json.loads(db.connection.execute("SELECT body FROM development_milestone_reports").fetchone()[0]) == result


def test_forged_stored_candidate_cannot_replace_source_checks(history):  # noqa: F811
    db, spool = prepare(history)
    report = history[0].inspect("i", spool)
    report["accepted_resource_witnesses"][0]["count"] = 100
    with db.transaction() as tx:
        tx.execute("UPDATE craft_reference_imports SET body=?", (canonical(report).decode(),))
    with pytest.raises(Fault, match="CRAFT_IMPORT_CONFLICT"):
        build_report(db, "i", spool)


def test_wire_changed_between_import_and_header_read_is_rejected(history, monkeypatch):  # noqa: F811
    db, spool = prepare(history)
    original = CraftReferenceStore.inspect
    def changed(self, instance, path):
        result = original(self, instance, path)
        path.write_bytes(path.read_bytes() + b"\n")
        return result
    monkeypatch.setattr(CraftReferenceStore, "inspect", changed)
    with pytest.raises((Fault, ValueError)):
        build_report(db, "i", spool)


def test_cli_report_cannot_enter_game_or_authority_directories(history, tmp_path, capsys):  # noqa: F811
    db, spool = prepare(history)
    args = ["--database", str(db.path), "--instance", "i", "--spool", str(spool), "--output"]
    for output in (history[1]["game_directory"] + "/score.json", str(history[3] / "score.json")):
        with pytest.raises(Fault, match="CRAFT_PRIVATE_PATH"):
            main(args + [output])
    output = tmp_path / "private-report.json"
    main(args + [str(output)])
    envelope = json.loads(output.read_bytes())
    assert envelope["report"]["development_predicate_complete"]
    stdout = json.loads(capsys.readouterr().out)
    assert set(stdout) == {"status", "visibility", "digest", "scoring_authority_qualified"}
    previous = output.read_bytes()
    with pytest.raises(Fault, match="CRAFT_REPORT_EXISTS"):
        main(args + [str(output)])
    assert output.read_bytes() == previous


def test_failed_report_write_can_retry_without_double_credit(history, tmp_path, monkeypatch):  # noqa: F811
    import strata_evaluator.development_milestone as module
    db, spool = prepare(history)
    output = tmp_path / "private-report.json"
    args = ["--database", str(db.path), "--instance", "i", "--spool", str(spool), "--output", str(output)]
    original = module.write_new
    def fail(*_):
        raise OSError("synthetic report disk failure")
    monkeypatch.setattr(module, "write_new", fail)
    with pytest.raises(OSError, match="synthetic report disk failure"):
        main(args)
    assert not output.exists()
    previous = counts(db)
    monkeypatch.setattr(module, "write_new", original)
    main(args)
    assert counts(db) == previous
    assert json.loads(output.read_bytes())["report"]["development_output"] == 1


def test_conflicting_durable_report_is_retained_and_rejected(history):  # noqa: F811
    db, spool = prepare(history)
    build_report(db, "i", spool)
    with db.transaction() as tx:
        tx.execute("UPDATE development_milestone_reports SET body='{}'")
    previous = counts(db)
    with pytest.raises(Fault, match="DEVELOPMENT_REPORT_CONFLICT"):
        build_report(db, "i", spool)
    assert counts(db) == previous
    assert db.connection.execute("SELECT body FROM development_milestone_reports").fetchone()[0] == "{}"
