"""Synthetic private preflight controls; no game, sign-in or model dispatch."""

import copy
import hashlib
import json
import os
from pathlib import Path

from pydantic import ValidationError
import pytest

from mcbench.storage import Fault, digest
from mcbench.launch_integrity import FileLease, snapshot
from strata_evaluator.reference_client import ClientReferenceBinding, main, validate_client_binding
from test_craft_reference import ACTOR, pin, reference  # noqa: F401


@pytest.fixture
def registration(reference, tmp_path):  # noqa: F811
    store, setup, _, _, _ = reference
    declaration = tmp_path / "declared-setup.json"
    declaration.write_bytes(
        b'{"supplied_inputs":{"minecraft:andesite":5,"minecraft:polished_andesite":3}}'
    )
    declared = {"path": str(declaration), **pin(declaration)}
    module = tmp_path / "module.jar"
    module.write_bytes(b"synthetic module")
    module_pin = {"path": str(module), **pin(module)}
    setup.update(schema="strata/PrivateCraftReferencePlan/2", native_team_ids={"agent": ACTOR})
    setup["supporting_files"]["declared-setup"] = declared
    setup["supporting_files"]["module"] = module_pin
    launch = {
        "schema": "strata/PrivateReferenceLaunch/2",
        "instance_id": "i",
        "setup_digest": digest(setup),
        "mode": "e9e-serverstarter",
        "executable": module_pin,
        "module_file": module_pin,
        "immutable_files": [module_pin],
        "immutable_trees": [],
        "fixture_arguments": [],
        "evidence_directory": str(tmp_path / "launch"),
        "server_port": 25574,
        "max_wall_s": 600,
        "graceful_stop_s": 120,
        "participant": {
            "participant_id": "client",
            "window_s": 380,
            "report_path": str(tmp_path / "result.json"),
        },
    }
    value = {
        "schema": "strata/PrivateReferenceClientBinding/1",
        "instance_id": "i",
        "campaign_id": "synthetic",
        "epoch": 1,
        "agent_id": "agent",
        "participant_id": "client",
        "actor_uuid": ACTOR,
        "native_team_id": ACTOR,
        "endpoint_policy": "installed-cli-resolved-loopback/1",
        "server_port": 25574,
        "body_fingerprint": hashlib.sha256(f"127.0.0.1:25574\n{ACTOR}".encode()).hexdigest(),
        "server_module": module_pin,
        "fixture_declaration": declared,
        "declared_supplied_inputs": {"minecraft:andesite": 5, "minecraft:polished_andesite": 3},
        "client_wall_ms": 365000,
        "worker_wall_ms": 90000,
        "terminal_reserve_ms": 15000,
        "primitive_limit": 1000,
    }
    return store, value, setup, launch


def test_consistent_registered_inputs_do_not_consume_grant_or_certify_arriving_body(registration):
    store, value, setup, launch = registration
    report = validate_client_binding(value, setup, launch)
    assert report["registration_consistent"] and not report["actual_body_verified"]
    assert not report["guardian_qualified"] and not report["scoring_eligible"]
    assert (
        store.database.connection.execute(
            "SELECT COUNT(*) FROM craft_reference_launches"
        ).fetchone()[0]
        == 0
    )
    assert report["binding_digest"] == digest(value)


@pytest.mark.parametrize(
    "change",
    [
        "old_port_body",
        "foreign_actor",
        "team",
        "campaign",
        "epoch",
        "agent",
        "launch_port",
        "launch_module",
        "source_module",
        "fixture_pin",
        "fixture_bytes",
        "input_count",
        "client_window",
        "worker_window",
        "setup_digest",
        "legacy_setup",
        "copied_labels",
        "endpoint_policy",
        "participant",
        "sealed_module",
        "server_window",
        "declaration_type",
    ],
)
def test_stale_or_inconsistent_reference_registration_rejected_before_launch(registration, change):
    store, value, setup, launch = registration
    if change == "old_port_body":
        value["body_fingerprint"] = hashlib.sha256(f"127.0.0.1:25567\n{ACTOR}".encode()).hexdigest()
    elif change == "foreign_actor":
        value["actor_uuid"] = "22222222-2222-2222-2222-222222222222"
        value["body_fingerprint"] = hashlib.sha256(
            f"127.0.0.1:25574\n{value['actor_uuid']}".encode()
        ).hexdigest()
    elif change == "team":
        value["native_team_id"] = "22222222-2222-2222-2222-222222222222"
    elif change == "campaign":
        value["campaign_id"] = "other"
    elif change == "epoch":
        value["epoch"] = 2
    elif change == "agent":
        value["agent_id"] = "other"
    elif change == "launch_port":
        launch["server_port"] = 25575
    elif change == "launch_module":
        launch["module_file"] = copy.deepcopy(launch["module_file"])
        launch["module_file"]["sha256"] = "a" * 64
    elif change == "source_module":
        Path(value["server_module"]["path"]).write_bytes(b"changed")
    elif change == "fixture_pin":
        value["fixture_declaration"] = copy.deepcopy(value["fixture_declaration"])
        value["fixture_declaration"]["sha256"] = "a" * 64
    elif change == "fixture_bytes":
        Path(value["fixture_declaration"]["path"]).write_bytes(b"{}")
    elif change == "input_count":
        value["declared_supplied_inputs"]["minecraft:andesite"] = 6
    elif change == "client_window":
        value["client_wall_ms"] = 380000
    elif change == "worker_window":
        value["worker_wall_ms"] = 360000
    elif change == "setup_digest":
        launch["setup_digest"] = "a" * 64
    elif change == "legacy_setup":
        setup["schema"] = "strata/PrivateCraftReferencePlan/1"
        del setup["native_team_ids"]
    elif change == "copied_labels":
        value["no_new_resources"] = True
    elif change == "endpoint_policy":
        value["endpoint_policy"] = "adopt_received_identity"
    elif change == "participant":
        value["participant_id"] = "other-client"
    elif change == "sealed_module":
        setup["supporting_files"]["module"] = copy.deepcopy(setup["supporting_files"]["module"])
        setup["supporting_files"]["module"]["sha256"] = "a" * 64
        launch["setup_digest"] = digest(setup)
    elif change == "server_window":
        launch["max_wall_s"] = 379
    else:
        path = Path(value["fixture_declaration"]["path"])
        path.write_bytes(b'{"supplied_inputs":{"minecraft:andesite":true}}')
        updated = {"path": str(path), **pin(path)}
        setup["supporting_files"]["declared-setup"] = updated
        value["fixture_declaration"] = updated
        value["declared_supplied_inputs"] = {"minecraft:andesite": 1}
        launch["setup_digest"] = digest(setup)
    with pytest.raises((Fault, ValidationError)):
        validate_client_binding(value, setup, launch)
    assert (
        store.database.connection.execute(
            "SELECT COUNT(*) FROM craft_reference_launches"
        ).fetchone()[0]
        == 0
    )


def test_endpoint_body_is_independent_of_observed_response(registration):
    _, value, _, _ = registration
    parsed = ClientReferenceBinding.model_validate(value)
    assert (
        parsed.body_fingerprint != hashlib.sha256(f"127.0.0.1:25575\n{ACTOR}".encode()).hexdigest()
    )
    assert "observed_body_fingerprint" not in type(parsed).model_fields


def test_operator_cli_preserves_fresh_report_and_rejects_replacement_or_game_output(
    registration, tmp_path
):
    _, binding, setup, launch = registration
    arguments = []
    for name, value in (("binding", binding), ("setup", setup), ("launch", launch)):
        path = tmp_path / (name + ".json")
        path.write_text(json.dumps(value), encoding="utf-8")
        arguments += ["--" + name, str(path)]
    output = tmp_path / "check.json"
    assert main(arguments + ["--output", str(output)]) == 0
    before = output.read_bytes()
    with pytest.raises(Fault, match="REFERENCE_CLIENT_OUTPUT"):
        main(arguments + ["--output", str(output)])
    assert output.read_bytes() == before
    with pytest.raises(Fault, match="REFERENCE_CLIENT_OUTPUT"):
        main(arguments + ["--output", str(Path(setup["game_directory"]) / "check.json")])


@pytest.mark.skipif(os.name != "nt", reason="Windows held-file registration profile")
@pytest.mark.parametrize("changed_after_preflight", [False, True])
def test_registration_rechecks_declared_bytes_under_held_handles(
    registration, changed_after_preflight
):
    _, binding, setup, launch = registration
    validate_client_binding(binding, setup, launch)
    path = Path(binding["fixture_declaration"]["path"])
    if changed_after_preflight:
        path.write_bytes(b'{"supplied_inputs":{}}')
    with FileLease(snapshot([path, Path(binding["server_module"]["path"])], [])):
        if changed_after_preflight:
            with pytest.raises(Fault, match="CRAFT_FILE_CHANGED"):
                validate_client_binding(binding, setup, launch)
        else:
            assert validate_client_binding(binding, setup, launch)["registration_consistent"]
            with pytest.raises(PermissionError):
                path.write_bytes(b'{"changed":true}')
