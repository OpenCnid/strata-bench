import json

from typer.testing import CliRunner

from mcbench.cli import app
from strata_evaluator.cli import main as report_main

runner = CliRunner()


def test_campaign_commands_create_status_journal_preflight(tmp_path, configs):
    config, agents = configs(2)
    config_file, agent_file = tmp_path / "config.json", tmp_path / "agents.json"
    config_file.write_text(config.model_dump_json(), encoding="utf-8")
    agent_file.write_text(json.dumps([a.model_dump() for a in agents]), encoding="utf-8")
    args = ["--config", str(config_file), "--agents", str(agent_file)]
    result = runner.invoke(app, ["campaign", "validate", *args])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["n"] == 2
    store = tmp_path / "private"
    result = runner.invoke(app, ["campaign", "create", *args, "--store", str(store)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["state"] == "DRAFT"
    result = runner.invoke(app, ["campaign", "status", "c1", "--store", str(store)])
    assert result.exit_code == 0, result.output
    destination = tmp_path / "journal.jsonl"
    result = runner.invoke(app, ["journal", "export", "--store", str(store),
                                 "--destination", str(destination)])
    assert result.exit_code == 0, result.output
    assert json.loads(destination.read_text())["kind"] == "campaign.created"
    result = runner.invoke(app, ["campaign", "preflight", *args, "--store", str(store)])
    assert result.exit_code == 2, result.output
    assert json.loads(result.output)["started"] is False


def test_private_report_replay_and_safe_publication(example, tmp_path):
    plan = {"assignments": {"private-lineage": {"craft": ["private-pair"]}},
            "family_weights": {"craft": 1}, "protocol_id": "ep1", "checkpoint_id": "cp1",
            "seed": 42, "replicates": 10000, "synthetic": True}
    plan_file, results_file = tmp_path / "plan.json", tmp_path / "results.jsonl"
    plan_file.write_text(json.dumps(plan), encoding="utf-8")
    records = [example("EvaluationResult") | {"arm": arm, "lineage_id": "private-lineage",
        "pair_id": "private-pair", "result_id": arm, "outcome": "success", "success": True,
        "event_observed": True, "censor_reason": None, "validity_flags": []}
        for arm in ("experienced", "initial")]
    results_file.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    private, public = tmp_path / "private.json", tmp_path / "public.json"
    args = ["--plan", str(plan_file), "--results", str(results_file), "--output", str(private),
            "--publication-output", str(public)]
    report_main(args)
    first = private.read_bytes()
    report_main(args)
    assert first == private.read_bytes()
    text = public.read_text()
    assert "private-lineage" not in text and "private-pair" not in text and "cas:sha256:" not in text
    assert json.loads(text)["report"]["synthetic"] is True
