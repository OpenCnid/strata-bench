"""Synthetic combined captures; no game, credentials, model or inference spend."""

import copy
from contextlib import closing
import hashlib
import sqlite3
import zipfile

import pytest

from mcbench.native_game_measurements import TIMING_KINDS, bind_clock_overlay, inspect_measurements, inspect_timing
from mcbench.storage import Fault, canonical, digest
from mcbench.vanilla_clock import inspect_vanilla_clock
from mcbench.vanilla_persistence import VanillaPersistence
from mcbench.worker_health import inspect_worker_health
from test_vanilla_clock import SCOPE, UUID, records as clock_records, write as write_clock
from test_vanilla_persistence import (installed, sealed_installation, stopped, write_generated_save)
from test_worker_health import connection, records as health_records

# Imported fixtures deliberately exercise the real snapshot producer/reader.
assert installed and sealed_installation


def write(path, value):
    path.write_bytes(canonical(value))


@pytest.fixture
def capture(tmp_path, sealed_installation, installed):
    output = tmp_path / "run"
    (output / "server").mkdir(parents=True)
    (output / "worker").mkdir()
    root, binding, resolved, _ = sealed_installation
    resolved["launch"]["arguments"] = ["-jar", "server.jar", "nogui"]
    write(output / "server/pack-launch.json", resolved)
    module = output / "vanilla-clock-agent.jar"
    with zipfile.ZipFile(module, "w") as jar:
        jar.writestr("strata-clock-callbacks.jar", b"synthetic callbacks")
    module_sha = hashlib.sha256(module.read_bytes()).hexdigest()
    config = {k: SCOPE[k] for k in ("campaign_id", "agent_id", "epoch")} | {"server_kind": "vanilla"}
    clock = SCOPE | {"agent_path": str(module), "agent_sha256": module_sha}
    files = [{"path": "C:/held/backends/mineflayer/dist/src/worker_health.js"}]
    base = {"schema": "strata/DevelopmentServer/5", "target": "vanilla", "pack": binding.model_dump(),
            "evidence": str(output / "server")}
    plan = bind_clock_overlay(base, clock, config, SCOPE["run_id"], files)
    write(output / "worker-runtime.json", {"inventory": {"files": files}})
    write(output / "worker-config.json", config)
    (output / "pilot-timing.jsonl").write_bytes(b"".join(canonical({"seq": seq, "kind": kind,
        "mono_ns": seq * 1_000_000_000, "unix": 1700000000 + seq}) + b"\n"
        for seq, kind in enumerate(TIMING_KINDS, 1)))
    write(output / "server/plan.json", plan)
    clock_config = "".join(f"{k}={v}\n" for k, v in (SCOPE | {"output": str(output / "server/vanilla-clock.jsonl")}).items())
    (output / "server/vanilla-clock.config").write_bytes(clock_config.encode())
    (output / "server/vanilla-clock-callbacks.jar").write_bytes(b"synthetic callbacks")
    launch = {"schema": "strata/VanillaClockLaunch/1", "base_launch_digest": digest(resolved["launch"]),
        "agent_sha256": module_sha, "callbacks_sha256": hashlib.sha256(b"synthetic callbacks").hexdigest(),
        "configuration_sha256": hashlib.sha256(clock_config.encode()).hexdigest(), **SCOPE,
        "arguments": [f"-javaagent:{module}={output / 'server/vanilla-clock.config'}", *resolved["launch"]["arguments"]],
        "original_pack_profile_unchanged_claim": False, "campaign_admission": False}
    launch["composite_launch_digest"] = digest(launch)
    write(output / "server/clock-launch.json", launch)
    records = clock_records()
    records[0]["module_sha256"] = module_sha
    write_clock(output / "server/vanilla-clock.jsonl", records)
    clock_report = inspect_vanilla_clock(output / "server/vanilla-clock.jsonl", scope=SCOPE,
                                        module_sha256=module_sha, pid=12)
    with closing(VanillaPersistence(root, pack=binding, resolved=resolved)) as persistence:
        write_generated_save(root, installed)
        (root / "world/playerdata").mkdir()
        (root / f"world/playerdata/{UUID}.dat").write_bytes(b"synthetic player")
        snapshot = persistence.capture(output / "server/stopped-instance", stopped(), plan_digest=digest(plan))
    owned = {"job": stopped().job.accounting(), "held": stopped().job.member_status()}
    server = {"status": "stopped_unqualified", "plan_digest": digest(plan), "ready": True,
        "stop_sent": True, "forced_stop": False, "exit_code": 0, "stopped_snapshot": snapshot,
        "vanilla_clock": clock_report | {"launch_binding": launch,
            "owned_jvm": {"pid": 12, "executable": resolved["launch"]["executable_path"]}, "owned_processes": owned}}
    write(output / "server/result.json", server)
    with connection(health_records()) as db:
        health = inspect_worker_health(db, **{k: config[k] for k in ("campaign_id", "agent_id", "epoch")}, required=True)
        target = sqlite3.connect(output / "worker/actions.sqlite")
        db.commit()
        db.backup(target)
        target.close()
    db.close()
    return output, plan, config, server, health


def inspect(capture):
    output, plan, config, server, health = capture
    with sqlite3.connect(output / "worker/actions.sqlite") as db:
        return inspect_measurements(output, plan, config, server, health, SCOPE["run_id"], db)


def test_recomputes_and_joins_one_body_without_adding_overlapping_intervals(capture):
    report = inspect(capture)
    assert report["saved_player_uuid"] == UUID
    assert report["clock"]["avatar_tick_events"] == {UUID: 2}
    assert report["worker_health"]["cpu_user_us"] == 175
    assert report["intervals_are_not_additive"] and report["active_wall_s"] is None
    assert not report["capacity_qualified"] and not report["complete_checkpoint"]
    timing = report["timing"]
    assert sum(s["elapsed_ns"] for s in timing["segments"]) == timing["wrapper_ns"]
    assert timing["native_harness_including_thinking_ns"] == 1_000_000_000


def test_runtime_manifest_uses_held_bundle_limit_without_enlarging_other_inputs(capture):
    import json
    from mcbench.native_game_measurements import read_json
    output = capture[0]
    path = output / "worker-runtime.json"
    runtime = json.loads(path.read_bytes())
    runtime["source_inventory_fixture_padding"] = "x" * (8 * 1024**2)
    write(path, runtime)
    assert inspect(capture)["saved_player_uuid"] == UUID
    with pytest.raises(Fault, match="NATIVE_MEASUREMENT_INPUT"):
        read_json(path)
    runtime["source_inventory_fixture_padding"] *= 2
    write(path, runtime)
    with pytest.raises(Fault, match="NATIVE_MEASUREMENT_INPUT"):
        inspect(capture)


@pytest.mark.parametrize("case", ["scope", "job", "health_module", "hash", "epoch", "extra", "unsealed"])
def test_overlay_refuses_incomplete_or_foreign_profile(capture, case):
    _, plan, config, _, _ = capture
    base, clock = copy.deepcopy(plan["base"]), copy.deepcopy(plan["clock"])
    files = [{"path": "C:/held/dist/src/worker_health.js"}]
    if case == "scope":
        clock["agent_id"] = "foreign"
    elif case == "job":
        clock["run_id"] = "old-job"
    elif case == "health_module":
        files = []
    elif case == "hash":
        clock["agent_sha256"] = "bad"
    elif case == "epoch":
        clock["epoch"] = True
    elif case == "extra":
        clock["extra"] = True
    else:
        base["schema"] = "strata/DevelopmentServer/2"
    with pytest.raises(Fault):
        bind_clock_overlay(base, clock, config, SCOPE["run_id"], files)


@pytest.mark.parametrize("case", ["health", "clock_summary", "clock_bytes", "module", "callbacks", "config",
                                  "forced", "snapshot_plan", "roster", "owned", "argument", "missing_health"])
def test_join_rejects_tampering_and_missing_streams(capture, case):
    output, plan, config, server, health = capture
    if case == "health":
        health["cpu_user_us"] += 1
    elif case == "clock_summary":
        server["vanilla_clock"]["completed_server_ticks"] += 1
    elif case == "clock_bytes":
        path = output / "server/vanilla-clock.jsonl"
        path.write_bytes(path.read_bytes()[:-1])
    elif case == "module":
        (output / "vanilla-clock-agent.jar").write_bytes(b"wrong")
    elif case == "callbacks":
        (output / "server/vanilla-clock-callbacks.jar").write_bytes(b"wrong")
    elif case == "config":
        (output / "server/vanilla-clock.config").write_bytes(b"foreign")
    elif case == "forced":
        server["forced_stop"] = True
    elif case == "snapshot_plan":
        plan["base"]["evidence"] += "foreign"
        write(output / "server/plan.json", plan)
        server["plan_digest"] = digest(plan)
    elif case == "roster":
        rows = clock_records()
        rows[0]["module_sha256"] = plan["clock"]["agent_sha256"]
        for row in rows[-2:]:
            row["avatar_tick_events"] = {"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": next(iter(row["avatar_tick_events"].values()))}
        write_clock(output / "server/vanilla-clock.jsonl", rows)
        server["vanilla_clock"].update(inspect_vanilla_clock(output / "server/vanilla-clock.jsonl",
            scope=SCOPE, module_sha256=plan["clock"]["agent_sha256"], pid=12))
    elif case == "owned":
        server["vanilla_clock"]["owned_processes"]["job"]["terminated_processes"] = 1
    elif case == "argument":
        launch = server["vanilla_clock"]["launch_binding"]
        launch["arguments"][0] = "-javaagent:foreign.jar"
        launch["composite_launch_digest"] = digest({k: v for k, v in launch.items() if k != "composite_launch_digest"})
        write(output / "server/clock-launch.json", launch)
    else:
        with sqlite3.connect(output / "worker/actions.sqlite") as db:
            db.execute("DELETE FROM events")
    write(output / "server/result.json", server)
    with pytest.raises(Fault):
        inspect(capture)


@pytest.mark.parametrize("changed", [False, True])
def test_sealed_reader_reconstructs_without_writing_or_accepting_changed_report(capture, changed):
    from strata_evaluator.evidence_bundle import EvidenceBundle
    from strata_evaluator.native_game_measurements import inspect_native_measurements
    from test_native_game_evidence import seal

    output, server_plan, config, server, health = capture
    report = inspect(capture)
    intent = {"model_provider": "native_oauth", "isolation_qualified": False,
        "plan": {"schema": "strata/M0NativePilot/2", "clock": server_plan["clock"],
            "pack": server_plan["base"]["pack"], "worker_invocation": config,
            "worker_runtime": {"sha256": hashlib.sha256((output / "worker-runtime.json").read_bytes()).hexdigest()},
            "pilot": {"job_id": SCOPE["run_id"]}}}
    write(output / "intent.json", intent)
    write(output / "server-plan.json", server_plan)
    if changed:
        report["saved_player_uuid"] = "foreign"
    write(output / "result.json", {"server_result": server, "worker_health": health,
        "status": "pass", "native_worker_journal_join": True, "measurements": report})
    bundle = EvidenceBundle(output.parent, seal(output.parent))
    if changed:
        with pytest.raises(Fault, match="NATIVE_MEASUREMENT_CHANGED"):
            inspect_native_measurements(bundle)
    else:
        result = inspect_native_measurements(bundle)
        assert result["measurements"] == report and result["model_costs_reconciled"] is False
    bundle.verify()


@pytest.mark.parametrize("case", ["missing", "partial", "reordered", "boolean", "reverse", "exposure", "unix_jump"])
def test_timing_uses_monotonic_order_and_retains_full_exposure(capture, case):
    import json
    output, _, _, server, health = capture
    path = output / "pilot-timing.jsonl"
    events = [json.loads(line) for line in path.read_bytes().splitlines()]
    if case == "missing":
        events.pop()
    elif case == "reordered":
        events[4]["kind"] = "native_finished"
    elif case == "boolean":
        events[0]["seq"] = True
    elif case == "reverse":
        events[6]["mono_ns"] = events[5]["mono_ns"] - 1
    elif case == "exposure":
        health["elapsed_ns"] = 100_000_000_000
    elif case == "unix_jump":
        events[5]["unix"] -= 1000
    raw = b"".join(canonical(e) + b"\n" for e in events)
    path.write_bytes(raw[:-1] if case == "partial" else raw)
    if case == "unix_jump":
        assert inspect_timing(path, server["vanilla_clock"], health)["native_harness_including_thinking_ns"] == 1_000_000_000
    else:
        with pytest.raises(Fault):
            inspect_timing(path, server["vanilla_clock"], health)


def test_adjacent_timing_marks_can_share_one_clock_quantum(capture):
    import json
    output, _, _, server, health = capture
    path = output / "pilot-timing.jsonl"
    events = [json.loads(line) for line in path.read_bytes().splitlines()]
    for current, preceding in ((4, 3), (8, 7)):
        events[current]["mono_ns"] = events[preceding]["mono_ns"]
    path.write_bytes(b"".join(canonical(e) + b"\n" for e in events))
    report = inspect_timing(path, server["vanilla_clock"], health)
    assert report["events"] == events
    assert sum(s["elapsed_ns"] == 0 for s in report["segments"]) == 2
    assert sum(s["elapsed_ns"] for s in report["segments"]) == report["wrapper_ns"]
    assert report["native_harness_including_thinking_ns"] == events[5]["mono_ns"] - events[4]["mono_ns"]


@pytest.fixture
def completed_cost_bundle(capture, monkeypatch):
    """Synthetic cost boundary; real clock/snapshot/health readers run normally."""
    from types import SimpleNamespace
    from strata_evaluator import native_game_measurements as reader
    from strata_evaluator.evidence_bundle import EvidenceBundle
    from test_native_game_evidence import seal

    output, plan, config, server, health = capture
    with sqlite3.connect(output.parent / "controller.sqlite") as db:
        db.execute("CREATE TABLE synthetic_boundary (value TEXT)")
    (output / "native").mkdir()
    write(output / "intent.json", {"model_provider": "native_oauth", "isolation_qualified": False,
        "plan": {"schema": "strata/M0NativePilot/2", "clock": plan["clock"], "pack": plan["base"]["pack"],
            "worker_invocation": config, "worker_runtime": {"sha256": hashlib.sha256(
                (output / "worker-runtime.json").read_bytes()).hexdigest()}, "pilot": {"job_id": SCOPE["run_id"]}}})
    write(output / "server-plan.json", plan)
    result = {"server_result": server, "worker_health": health, "status": "fail",
              "native_worker_journal_join": False, "measurements": inspect(capture)}
    native = SimpleNamespace(**config, job_id=SCOPE["run_id"], profile_digest=lambda: "synthetic-profile")
    valuation = {"raw_usage_ref": "synthetic-receipt"}
    source = {"returncode": 0, "attempts": [{"valuation": valuation}],
              "broker_calls": [{"elapsed_ns": 123}]}
    recorded = {"is_example": False, "model_evidence": "actual_native_oauth", "job_id": native.job_id,
        "profile_digest": native.profile_digest(), "attempts": ["synthetic"], "valuations": [valuation],
        "checks": {"native_completed": True, "walk_observed": False}}

    def source_reader(_db, _cas, job, *, simulation):
        assert job == native.job_id and simulation is False
        return native, source, None

    def cost_reader(_db, _cas, selected, actual_source, *, simulation):
        assert selected is native and actual_source is source and simulation is False
        return {"real_model_requests": 1, "synthetic_test_boundary": True}

    monkeypatch.setattr(reader, "inspect_native_source", source_reader)
    monkeypatch.setattr(reader, "model_usage", cost_reader)

    def bundle():
        write(output / "result.json", result)
        write(output / "native/result.json", recorded)
        return EvidenceBundle(output.parent, seal(output.parent))

    return bundle, result, recorded, native, source


def test_completed_costs_keep_failed_gameplay_and_strict_success_reader(completed_cost_bundle):
    from strata_evaluator.native_game_measurements import inspect_completed_pilot_costs, inspect_instrumented_pilot
    build, result, recorded, _, _ = completed_cost_bundle
    bundle = build()
    report = inspect_completed_pilot_costs(bundle)
    assert report["schema"] == "strata/CompletedNativePilotCosts/1"
    assert report["model_costs_reconciled"] and report["tool_execution"]["sum_call_ns"] == 123
    assert report["outcome"] == {"run_status": "fail", "native_checks": recorded["checks"],
        "worker_action_join_recorded": False, "run_result_digest": digest(result),
        "native_result_digest": digest(recorded)}
    assert not report["gameplay_success_qualified"] and not report["action_effects_reconciled"]
    assert not report["complete_G0_qualification"] and report["G0"] == "fail"
    with pytest.raises(Fault, match="NATIVE_MEASUREMENT_STOP"):
        inspect_instrumented_pilot(bundle)
    bundle.verify()


@pytest.mark.parametrize("case", ["returncode", "scope", "native_check", "nonboolean_check", "valuations",
                                  "attempts", "duration", "boolean_duration", "unknown_usage", "status", "join"])
def test_completed_costs_do_not_waive_uncertainty_or_invalid_bindings(completed_cost_bundle, monkeypatch, case):
    from strata_evaluator import native_game_measurements as reader
    build, result, recorded, native, source = completed_cost_bundle
    if case == "returncode":
        source["returncode"] = 1
    elif case == "scope":
        native.agent_id = "foreign"
    elif case == "native_check":
        recorded["checks"]["native_completed"] = False
    elif case == "nonboolean_check":
        recorded["checks"]["walk_observed"] = 0
    elif case == "valuations":
        recorded["valuations"] = []
    elif case == "attempts":
        recorded["attempts"] = []
    elif case in {"duration", "boolean_duration"}:
        source["broker_calls"][0]["elapsed_ns"] = -1 if case == "duration" else True
    elif case == "unknown_usage":
        def unknown(*args, **kwargs):
            raise Fault("METERING_UNKNOWN")
        monkeypatch.setattr(reader, "model_usage", unknown)
    elif case == "status":
        result["status"] = "unknown"
    else:
        result["native_worker_journal_join"] = 0
    with pytest.raises(Fault):
        reader.inspect_completed_pilot_costs(build())


def test_successful_wrapper_still_requires_every_gameplay_check(completed_cost_bundle):
    from strata_evaluator.native_game_measurements import inspect_instrumented_pilot
    build, result, _, _, _ = completed_cost_bundle
    result.update(status="pass", native_worker_journal_join=True)
    with pytest.raises(Fault, match="NATIVE_MEASUREMENT_COSTS"):
        inspect_instrumented_pilot(build())


def test_successful_wrapper_preserves_its_schema_and_cost_join(completed_cost_bundle):
    from strata_evaluator.native_game_measurements import inspect_completed_pilot_costs, inspect_instrumented_pilot
    build, result, recorded, _, _ = completed_cost_bundle
    result.update(status="pass", native_worker_journal_join=True)
    recorded["checks"]["walk_observed"] = True
    bundle = build()
    strict = inspect_instrumented_pilot(bundle)
    costs = inspect_completed_pilot_costs(bundle)
    assert strict["schema"] == "strata/InstrumentedNativePilotEvidence/1"
    assert strict["model_costs_reconciled"] and strict["model"] == costs["model"]
    assert strict["measurements"] == costs["measurements"]
    assert costs["outcome"]["run_status"] == "pass"
    assert not costs["gameplay_success_qualified"]  # Costs alone never certify behavior.


def test_pilot_source_capture_uses_declared_held_worker_bytes_and_keeps_credentials_out(tmp_path):
    import json
    from mcbench.native_game_measurements import archive_pilot_sources
    repository, worker, output = (tmp_path / name for name in ("repository", "worker", "output"))
    output.mkdir()
    python_name, js_name = "src/mcbench/fixture.py", "backends/mineflayer/dist/src/fixture.js"
    pins = {}
    for root, name, raw in ((repository, python_name, b"python fixture"), (worker, js_name, b"held worker fixture")):
        target = root / name
        target.parent.mkdir(parents=True)
        target.write_bytes(raw)
        pins[name] = hashlib.sha256(raw).hexdigest()
    decoy = repository / js_name
    decoy.parent.mkdir(parents=True)
    decoy.write_bytes(b"unheld checkout version")
    (worker / "auth.json").write_bytes(b"synthetic secret must not be copied")
    archive_pilot_sources(output, pins, repository, worker)
    assert json.loads((output / "source-pins.json").read_bytes()) == pins
    assert (output / "source" / js_name).read_bytes() == b"held worker fixture"
    assert not (output / "source/auth.json").exists()
    with pytest.raises(FileExistsError):
        archive_pilot_sources(output, pins, repository, worker)


@pytest.mark.parametrize("case", ["hash", "traversal", "unlisted"])
def test_failed_pilot_source_capture_never_publishes_a_complete_manifest(tmp_path, case):
    from mcbench.native_game_measurements import archive_pilot_sources
    output = tmp_path / "out"
    output.mkdir()
    source = tmp_path / "tools/fixture.py"
    source.parent.mkdir()
    source.write_bytes(b"fixture")
    name = {"hash": "tools/fixture.py", "traversal": "tools/../secret", "unlisted": "auth.json"}[case]
    with pytest.raises(Fault):
        archive_pilot_sources(output, {name: "0" * 64}, tmp_path, tmp_path)
    assert not (output / "source-pins.json").exists()


def test_reconciliation_cli_cannot_replace_its_evidence(tmp_path):
    from strata_evaluator.native_game_measurements import main
    with pytest.raises(Fault, match="EVIDENCE_READ_ONLY"):
        main(["--bundle", str(tmp_path), "--seal", "a" * 64, "--output", str(tmp_path / "seal.json")])
