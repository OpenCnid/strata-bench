"""Explicit /5 integration fixture: owned game worker, synthetic roster/provider.

The caller owns worker/server lifecycle and the controller heartbeat. This
fixture never qualifies the runtime, certifies game capacity, or spends money.
"""

import hashlib
import json
from pathlib import Path

from mcbench.storage import canonical, require
from native_broker_canaries import inspect_tool_outputs
from native_game_probe import GameProbe
from native_runtime_boundary import RuntimeBoundaryCanaries, inspect_boundary_outputs
from native_team_channel_probe import ACTORS, TeamChannelProbe, TeamChannelStore


class CampaignBoundaryProbe(TeamChannelProbe):
    def __init__(self, store, mode, descriptor, lease_id, output):
        require(type(store) is TeamChannelStore, "CAMPAIGN_BOUNDARY_STORE")
        super().__init__(store, mode)
        self.game = GameProbe(descriptor, lease_id)
        require(self.game.scope == {k: self.scope[k] for k in ("campaign_id", "agent_id", "epoch")},
                "CAMPAIGN_BOUNDARY_GAME_SCOPE")
        self.output = Path(output).absolute()
        require(self.output.is_dir(), "CAMPAIGN_BOUNDARY_OUTPUT")
        self.boundary = RuntimeBoundaryCanaries(self.output, profile_name=self.job_id + "-profile",
                                               deferred_tools=True, patch_disabled=True)
        self.boundary_phases = dict.fromkeys(ACTORS, 0)
        self.direct = {kind: [] for kind in ("shell", "patch", "patch_function")}
        self.entered = False

    def __enter__(self):
        require(not self.entered, "CAMPAIGN_BOUNDARY_REARM")
        self.entered = True
        try:
            self.store.healthy()
        except BaseException:
            self.boundary.close()
            raise
        return self

    def __exit__(self, *_):
        self.boundary.close()

    def next(self, actor, step, operation):
        require(actor in ACTORS and type(step) is int and 1 <= step <= 10,
                "CAMPAIGN_BOUNDARY_SEQUENCE")
        phase = self.boundary_phases[actor]
        if phase == 0:
            self.boundary_phases[actor] = 1
            return [self.call(actor, "boundary", operation, code=self.boundary.code(agent=actor))]
        if phase == 1:
            self.boundary_phases[actor] = 2
            items = []
            for kind, name, custom in (("shell", "exec_command", False), ("patch", "apply_patch", True),
                                       ("patch_function", "apply_patch", False)):
                key = "campaign-direct-" + kind + "-" + operation
                require(key not in self.calls, "PAIR_DUPLICATE_CALL")
                self.calls[key] = {"actor": actor, "phase": "direct"}
                self.direct[kind].append(key)
                patch = "*** Begin Patch\n*** Update File: " + self.boundary.protected.as_posix() + (
                    "\n@@\n-absent context\n+changed\n*** End Patch")
                args = {"cmd": self.boundary.command(), "login": False} if kind == "shell" else {"input": patch}
                items.append({"id": "tool-" + key, "call_id": key, "namespace": "functions", "name": name,
                    "type": "custom_tool_call" if custom else "function_call",
                    **({"input": patch} if custom else {"arguments": json.dumps(args)})})
            return items
        # Parent protocol keeps its own four-wait bound; our two added phases
        # do not consume or widen that bound.
        return super().next(actor, step - 2, operation)

    def report(self):
        result = super().report()
        outputs = [{"call_id": key, "native_agent": self.calls[key]["actor"], "output": value}
                   for key, value in self.outputs.items()]
        observed = inspect_boundary_outputs(outputs)
        checks = observed["checks"] | inspect_tool_outputs(outputs, self.direct["shell"],
            deferred_tools=True, patch_disabled=True, patch_direct_calls=self.direct["patch"],
            patch_function_calls=self.direct["patch_function"], team_enabled=True)
        requests = canonical(self.requests)
        boundary = self.boundary
        def unchanged(path, expected):
            return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected
        checks.update({
            "candidate_all_boundary_phases": set(self.boundary_phases.values()) == {2},
            "candidate_owned_canaries_absent": all(value.encode() not in requests for value in boundary.secrets.values()),
            "candidate_credentials_absent": all(value not in requests for value in (
                self.game.descriptor["token"].encode(), b"STRATA_SYNTHETIC_OAUTH_ACCESS", b"STRATA_SYNTHETIC_OAUTH_REFRESH")),
            "candidate_fake_credential_target_exists": boundary.credential_path.is_file() and
                b"STRATA_SYNTHETIC_OAUTH_ACCESS" in boundary.credential_path.read_bytes(),
            "candidate_file_unchanged": unchanged(boundary.protected, boundary.original),
            "candidate_module_unchanged": unchanged(boundary.module, boundary.module_digest),
            "candidate_binary_unchanged": unchanged(boundary.binary_target, boundary.binary_digest),
            "candidate_no_patch_targets": all(not p.exists() for p in boundary.absent_targets),
            "candidate_listener_control": boundary.controls == ["/owned-control"],
            "candidate_no_private_network": boundary.unauthorized == [],
        })
        result["checks"].update(checks)
        result.update({"scope_kind": "campaign_catalog_game_integration_candidate",
            "provider": "scripted", "controller_readiness": "synthetic", "runtime_qualified": False,
            "simultaneous_body_capacity_qualified": False, "boundary": observed,
            "direct_calls": self.direct})
        return result
