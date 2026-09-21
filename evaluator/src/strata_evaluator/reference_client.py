"""Operator reference-client registration, not observed identity or admission proof."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, TypeAdapter, model_validator

from mcbench.contracts import Digest, Id, Name, Positive, Strict
from mcbench.inference_transport import strict_json
from mcbench.storage import digest, require

from .craft_reference import (
    CraftReferencePlanV2,
    PrivateFile,
    check_file,
    parse_plan,
    private_path,
    write_new,
)
from .reference_launch import ReferenceLaunchPlanV2, parse_launch_plan
from .setup_facts import UUID
from .telemetry_auth import private_read


class ClientReferenceBinding(Strict):
    schema_: Literal["strata/PrivateReferenceClientBinding/1"] = Field(alias="schema")
    instance_id: Id
    campaign_id: Id
    epoch: Positive
    agent_id: Id
    participant_id: Id
    actor_uuid: UUID
    native_team_id: UUID
    # The selected installed-CLI launch resolves a numeric loopback TCP endpoint.
    # Menu metadata, hostnames, IPv6 and a different launch method need their own
    # predeclared binding; do not normalize or adopt an arriving identity.
    endpoint_policy: Literal["installed-cli-resolved-loopback/1"]
    server_port: int = Field(ge=1024, le=65535)
    body_fingerprint: Digest
    server_module: PrivateFile
    fixture_declaration: PrivateFile
    declared_supplied_inputs: dict[Name, Positive] = Field(max_length=128)
    client_wall_ms: int = Field(ge=1, le=420000)
    worker_wall_ms: int = Field(ge=1, le=420000)
    terminal_reserve_ms: int = Field(ge=5000, le=60000)
    primitive_limit: int = Field(ge=2, le=1000000)

    @model_validator(mode="after")
    def planned_identity(self):
        # Exact NativeGameRuntime.bodyFingerprint / GameBodyEndpoint policy for
        # this explicit numeric endpoint, independently of received observations.
        expected = hashlib.sha256(
            f"127.0.0.1:{self.server_port}\n{self.actor_uuid}".encode()
        ).hexdigest()
        require(self.body_fingerprint == expected, "REFERENCE_CLIENT_BODY")
        require(
            self.worker_wall_ms + self.terminal_reserve_ms < self.client_wall_ms,
            "REFERENCE_CLIENT_EXPOSURE",
        )
        return self


def same_pin(first, second):
    return (
        Path(first.path).resolve() == Path(second.path).resolve()
        and first.sha256 == second.sha256
        and first.bytes == second.bytes
    )


def validate_client_binding(value, setup_value, launch_value):
    """Verify registration against sealed inputs before consuming a launch grant.

    The driver must still compare the actual native identity, enforce the bounded
    process lifetime, and preserve a failed guardian. This function grants neither
    native action authority nor permission to reuse a consumed instance.
    """
    binding = ClientReferenceBinding.model_validate(value)
    setup, launch = parse_plan(setup_value), parse_launch_plan(launch_value)
    require(
        isinstance(setup, CraftReferencePlanV2) and isinstance(launch, ReferenceLaunchPlanV2),
        "REFERENCE_CLIENT_PROFILE",
    )
    require(
        launch.mode == "e9e-serverstarter"
        and launch.instance_id == setup.instance_id
        and launch.setup_digest == digest(setup.model_dump(by_alias=True)),
        "REFERENCE_CLIENT_SETUP",
    )
    require(
        (binding.instance_id, binding.campaign_id, binding.epoch)
        == (setup.instance_id, setup.campaign_id, setup.epoch),
        "REFERENCE_CLIENT_SCOPE",
    )
    require(
        setup.roster.get(binding.agent_id) == binding.actor_uuid
        and setup.native_team_ids.get(binding.agent_id) == binding.native_team_id,
        "REFERENCE_CLIENT_ROSTER",
    )
    require(
        binding.participant_id == launch.participant.participant_id, "REFERENCE_CLIENT_PARTICIPANT"
    )
    module = setup.supporting_files.get("module")
    require(
        binding.server_port == launch.server_port
        and same_pin(binding.server_module, launch.module_file)
        and module is not None
        and same_pin(binding.server_module, module),
        "REFERENCE_CLIENT_SERVER",
    )
    require(
        binding.client_wall_ms + binding.terminal_reserve_ms <= launch.participant.window_s * 1000
        and launch.participant.window_s <= launch.max_wall_s,
        "REFERENCE_CLIENT_EXPOSURE",
    )
    declaration = setup.supporting_files.get("declared-setup")
    require(
        declaration is not None and same_pin(binding.fixture_declaration, declaration),
        "REFERENCE_CLIENT_FIXTURE",
    )
    require(binding.fixture_declaration.bytes <= 1024**2, "REFERENCE_CLIENT_FIXTURE_QUOTA")
    for pin in (binding.server_module, binding.fixture_declaration):
        check_file(private_path(pin.path), pin)
    declared = strict_json(private_read(binding.fixture_declaration.path, 1024**2))
    require(isinstance(declared, dict), "REFERENCE_CLIENT_FIXTURE")
    supplied = TypeAdapter(dict[Name, Positive]).validate_python(
        declared.get("supplied_inputs"), strict=True
    )
    require(supplied == binding.declared_supplied_inputs, "REFERENCE_CLIENT_FIXTURE")
    return {
        "schema": "strata/PrivateReferenceClientBindingCheck/1",
        "binding_digest": digest(binding.model_dump(by_alias=True)),
        "setup_digest": launch.setup_digest,
        "launch_plan_digest": digest(launch.model_dump(by_alias=True)),
        "registration_consistent": True,
        "expected_body_fingerprint": binding.body_fingerprint,
        "actual_body_verified": False,
        "guardian_qualified": False,
        "scoring_eligible": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("binding", "setup", "launch", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args(argv)
    binding, setup, launch = [
        strict_json(private_read(path, 8 * 1024**2))
        for path in (args.binding, args.setup, args.launch)
    ]
    output = private_path(args.output)
    game = private_path(parse_plan(setup).game_directory)
    require(not output.exists() and not output.is_relative_to(game), "REFERENCE_CLIENT_OUTPUT")
    report = validate_client_binding(binding, setup, launch)
    write_new(output, report)
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
