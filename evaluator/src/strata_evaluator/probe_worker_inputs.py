"""Private whole-pair worker input custody; no process or provider dispatch.

This checks declared account bindings, not entitlement/session validity. Token
refresh and authenticated server identity remain the worker's separate checks.
Parent evaluation envelopes/resources stay reserved when this custody closes.
"""

from contextlib import ExitStack
from copy import deepcopy
import re

from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease, snapshot
from mcbench.native_probe_binding import read_binding
from mcbench.pack_launch import resolve_pack_launch
from mcbench.pack_worker import HeldPackWorker, _path
from mcbench.storage import digest, require
from mcbench.worker_stop import ARGUMENT

from .telemetry_auth import private_read

POLICY = "held-complete-probe-worker-inputs/1"


def account_declaration(configuration):
    """Read only the small profile declaration, never provider token files."""
    path = _path(configuration["auth_cache"]) / "account.json"
    value = strict_json(private_read(path, 8192))
    require(isinstance(value, dict) and set(value) == {"schema", "account", "profile_id"}
            and value["schema"] == "strata/MinecraftAccount/1"
            and isinstance(value["account"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value["account"])
            and value["account"] == configuration["username"], "PROBE_WORKER_ACCOUNT")
    require(isinstance(value["profile_id"], str) and re.fullmatch(r"[a-f0-9]{32}", value["profile_id"]),
            "AWAITING_OPERATOR_AUTH")
    require(value["profile_id"] == configuration["expected_player_uuid"].replace("-", ""),
            "PROBE_WORKER_ACCOUNT_MISMATCH")
    return path, digest(value)


class HeldProbeWorkerInputs:
    def __init__(self, software, principal, invocations):
        self.software, self.principal = software, principal
        self.values = deepcopy(invocations)
        self._entered, self.closed = False, False
        self._resources = None
        self._workers, self._resolved = {}, {}

    def _bindings(self):
        prep = self.software.preparation
        rows = prep.db.connection.execute(
            "SELECT arm,source_agent,ref FROM native_probe_bindings WHERE namespace=? AND pair=?",
            (prep.views.namespace, prep.pair_id)).fetchall()
        actual = {(r["arm"], r["source_agent"]): r["ref"] for r in rows}
        expected = {(arm, agent) for arm, group in self._invocations.items() for agent in group}
        require(set(actual) == expected and len(actual) == len(rows), "PROBE_COMPLETE_ROSTER")
        for (arm, agent), ref in actual.items():
            binding = read_binding(prep.db.connection, prep.cas, ref)
            invocation = self._invocations[arm][agent]
            require(binding.destination.campaign_id == invocation["campaign_id"]
                    and binding.destination.agent_id == invocation["agent_id"]
                    and invocation["epoch"] == 1, "PROBE_WORKER_SCOPE")
        return actual

    def __enter__(self):
        require(not self._entered and not self.closed, "PROBE_WORKER_INPUTS_CONSUMED")
        self._entered = True
        resources = ExitStack()
        try:
            # The existing compiler authorizes the principal and checks complete
            # roster, saved bodies, destination scopes and fresh disjoint paths.
            self._invocations = self.software.worker_invocations(self.principal, self.values)
            self._binding_refs = self._bindings()
            accounts = {}
            # Validate ALL members before creating even the first config file.
            for arm, group in self._invocations.items():
                self._resolved[arm] = {}
                for agent, invocation in group.items():
                    resolved = resolve_pack_launch(self.software.binding, "client", worker_invocation=invocation)
                    configuration = resolved["worker_configuration"]
                    require(configuration["schema"] == "strata/DevelopmentWorker/2"
                            and resolved["launch"]["arguments"][-1] == ARGUMENT,
                            "PROBE_WORKER_STOP_REQUIRED")
                    path, pin = account_declaration(configuration)
                    require(path not in accounts or accounts[path] == pin, "PROBE_WORKER_ACCOUNT_MISMATCH")
                    accounts[path] = pin
                    self._resolved[arm][agent] = resolved
            self._account_lease = resources.enter_context(FileLease(snapshot(list(accounts), [])))
            self._accounts = accounts
            self._check_accounts()
            for arm, group in self._invocations.items():
                self._workers[arm] = {}
                for agent, invocation in group.items():
                    worker = resources.enter_context(HeldPackWorker(self.software.binding, invocation))
                    self._workers[arm][agent] = worker
                    require(worker.resolved == self._resolved[arm][agent], "PROBE_WORKER_INPUTS_CHANGED")
            self._resources = resources
            self.check()
            return self
        except BaseException:
            self.closed = True
            resources.close()
            raise

    def _check_accounts(self):
        self._account_lease.recheck()
        for group in self._resolved.values():
            for resolved in group.values():
                path, pin = account_declaration(resolved["worker_configuration"])
                require(self._accounts.get(path) == pin, "PROBE_WORKER_ACCOUNT_CHANGED")

    def check(self):
        require(self._resources is not None and not self.closed, "PROBE_WORKER_INPUTS_CLOSED")
        try:
            self.software.check()
            require(self._bindings() == self._binding_refs, "PROBE_WORKER_BINDING_CHANGED")
            self._check_accounts()
            for arm, group in self._workers.items():
                for agent, worker in group.items():
                    require(not worker.processes, "PROBE_WORKER_PREMATURE_DISPATCH")
                    worker.runtime.recheck()
                    worker.config_lease.recheck()
                    require(worker.resolved == self._resolved[arm][agent], "PROBE_WORKER_INPUTS_CHANGED")
            return {"policy": POLICY, "pair_id": self.software.preparation.pair_id,
                    "invocations": deepcopy(self._invocations), "resolved": deepcopy(self._resolved),
                    "account_bindings": {str(p): pin for p, pin in self._accounts.items()},
                    "whole_roster_held": True, "worker_dispatch_authorized": False,
                    "authenticated_identity_verified": False, "live_initial_state_verified": False}
        except BaseException:
            self.close()
            raise

    def close(self):
        self.closed = True
        if self._resources is not None:
            self._resources.close()

    def __exit__(self, *_):
        self.close()
