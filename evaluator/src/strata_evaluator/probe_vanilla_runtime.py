"""Sequential protected server references for an already held registered pair.

This does not admit native gameplay, claim all-N body readiness, dispose of a
probe agent, settle evaluation costs or expose private provenance to gameplay.
"""

from contextlib import nullcontext
from pathlib import Path
import threading
import time
from typing import Literal

from pydantic import Field, TypeAdapter

from mcbench.contracts import Strict, Id
from mcbench.launch_integrity import FileLease, safe, snapshot
from mcbench.storage import canonical, digest, require
from mcbench.vanilla_persistence import RegisteredProbeWorld, VanillaPersistence, verify_snapshot

from .craft_reference import PrivateFile, check_file, check_tree
from .probe_vanilla_inputs import DIRECTORY_POLICY, BODY_POLICY as BODY_SOFTWARE_POLICY
from .vanilla_writer import ARGUMENTS, VanillaWriterSession, check_vanilla_settings
from .writer_preparation import WriterPreparationPlanV4, pinned_inventory

POLICY = "held-pair-protected-vanilla-reference/1"
BODY_POLICY = "held-pair-protected-vanilla-reference/2"


class ProbeVanillaLaunch(Strict):
    schema_: Literal["strata/PrivateProbeVanillaLaunch/1"] = Field(alias="schema")
    policy: Literal["held-pair-protected-vanilla-reference/1"]
    pair_id: Id
    arm: Literal["initial", "experienced"]
    helper_class: PrivateFile
    max_wall_s: int = Field(ge=30, le=600)
    max_stopped_state_bytes: int = Field(ge=1, le=1024**3)


class ProbeVanillaBodyLaunch(ProbeVanillaLaunch):
    schema_: Literal["strata/PrivateProbeVanillaLaunch/2"] = Field(alias="schema")
    policy: Literal["held-pair-protected-vanilla-reference/2"]


class ProbeVanillaSession(VanillaWriterSession):
    def __init__(self, owner, arm):
        held = owner.held
        writer = held.writers[arm]
        # start() checks the complete pair after both sessions are constructed,
        # before any dispatch. Keep local custody live here without rescanning
        # both sealed installations for each arm.
        writer.check()
        require(not writer.launched and not writer.completed, "PROBE_WORLD_ALREADY_LAUNCHED")
        writer.launched = True  # Failed preflight consumes this attempt.
        self.writer, self.plan = writer, owner.plans[arm]
        plan, software = self.plan, held.software
        require(isinstance(writer.plan, WriterPreparationPlanV4), "PROBE_PACK_DIRECTORY_POLICY")
        software.validate(arm, writer.plan)
        resolved = software.resolved
        require(
            resolved["target"] == "vanilla" and resolved["launch"]["arguments"] == ARGUMENTS,
            "VANILLA_WRITER_PROFILE",
        )
        require(
            Path(plan.helper_class.path).name == "StrataWriterLaunch.class", "WRITER_LAUNCH_HELPER"
        )
        check_file(Path(plan.helper_class.path), plan.helper_class)
        check_tree(writer.tree.path, writer.plan.sources)
        require(
            {
                p.relative_to(writer.tree.path).as_posix()
                for p in writer.tree.path.rglob("*")
                if p.is_dir()
            }
            == set(writer.plan.directories),
            "PROBE_PACK_DIRECTORIES",
        )
        check_vanilla_settings(writer.tree.path)
        pair = held.pair
        self.provenance = RegisteredProbeWorld.model_validate(
            {
                "schema": "strata/RegisteredProbeVanillaWorld/1",
                "namespace": held.preparation.views.namespace,
                "pair_id": pair["pair_id"],
                "arm": arm,
                "fixture_ref": pair["fixture_ref"],
                "pack_lock": pair["common"]["pack_lock"],
                "pair_plan_digest": digest(pair),
                "world_digest": pair["world_digest"],
                "world_files": pair["world_files"],
                "world_directories": pair["world_directories"],
            }
        )
        # The pair owns the complete installation lease through both writers'
        # lifetimes. Borrow its already hashed bytes; acquire only the new
        # helper lease. The combined launch inventory stays byte-for-byte equal
        # to a fresh helper + installation snapshot, with unchanged quotas.
        helper_inputs = snapshot([plan.helper_class.path], [])
        writer.leases.append(FileLease(helper_inputs))
        software.lease.recheck()
        trees = software.lease.inventory["trees"]
        require(len(trees) == 1 and trees[0]["path"] == str(safe(software.binding.instance)),
                "PROBE_PACK_CUSTODY_SCOPE")
        template_paths = set(trees[0]["files"])
        template_inputs = [p for p in software.lease.inventory["files"] if p["path"] in template_paths]
        require({p["path"] for p in template_inputs} == template_paths, "PROBE_PACK_CUSTODY_SCOPE")
        inputs = pinned_inventory([*template_inputs, *helper_inputs["files"]])
        inputs["trees"] = [{"path": trees[0]["path"], "files": list(trees[0]["files"])}]
        translated = resolved | {
            "launch": resolved["launch"] | {"working_directory": str(writer.tree.path)}
        }
        self.persistence = VanillaPersistence(
            writer.tree.path,
            pack=software.binding,
            resolved=translated,
            probe_world=self.provenance,
            capture_state_limit=plan.max_stopped_state_bytes,
        )
        writer.leases.append(self.persistence.lease)
        self.ready = threading.Event()
        self.evidence = Path(writer.plan.evidence_directory) / "launch"
        self.result = {
            "policy": owner.policy,
            "source_resolution": resolved,
            "probe_world": self.provenance.model_dump(by_alias=True),
            "protected_working_directory": str(writer.tree.path),
            "ready": False,
            "stop_requested": False,
            "authoritative_ticks": False,
            "probe_admission": False,
            "all_bodies_ready": False,
        }
        writer.result.update(
            capability="native-private-paired-vanilla-custody/1", vanilla=self.result
        )
        arguments = [
            "-XX:-UsePerfData",
            "-Djava.io.tmpdir=" + str(writer.workspace.path / "tmp"),
            *ARGUMENTS,
        ]
        self.result["arguments"] = arguments
        self.owner, self.inputs, self.arguments = owner, inputs, arguments
        self.started, self.native = False, None

    def start(self):
        self.owner.check()
        require(not self.started and self.native is None, "PROBE_WORLD_ALREADY_LAUNCHED")
        if not any(session.started for session in self.owner.sessions.values()):
            held = self.owner.held
            remaining = (
                min(held.preparation.deadline, *(w.deadline for w in held.writers.values()))
                - time.monotonic()
            )
            # Charge preflight time before admitting the complete sequential pair.
            require(sum(p.max_wall_s for p in self.owner.plans.values()) < remaining, "PROBE_WORLD_DEADLINE")
        self.started = True
        self.writer.body["game_launch_attempted"] = True
        self.native = self.writer._dispatch(
            self.plan, self.inputs, self.arguments, self.ready, self.evidence
        )

    def finish(self):
        result = super().finish()
        # Keep the stopped export immutable while the sibling arm still runs.
        path = Path(result["vanilla"]["snapshot"]["path"])
        self.writer.leases.append(FileLease(snapshot([], [path])))
        return result


class PairedVanillaRuntime:
    def before_writers(self, preparation, plans):
        """Server-only references have no independent worker import stage."""
        return nullcontext()

    def __init__(self, pair, values):
        require(
            isinstance(values, dict) and set(values) == set(pair["arm_order"]), "PROBE_WORLD_ROSTER"
        )
        self.plans = {arm: TypeAdapter(ProbeVanillaLaunch | ProbeVanillaBodyLaunch).validate_python(v)
                      for arm, v in values.items()}
        require(len({p.policy for p in self.plans.values()}) == 1, "PROBE_UNMATCHED_RUNTIME")
        self.policy = next(iter(self.plans.values())).policy
        self.software_policy = BODY_SOFTWARE_POLICY if self.policy == BODY_POLICY else DIRECTORY_POLICY
        require(
            all(p.pair_id == pair["pair_id"] and p.arm == arm for arm, p in self.plans.items()),
            "PROBE_WORLD_IDENTITY",
        )
        require(
            len(
                {
                    (
                        p.helper_class.sha256,
                        p.helper_class.bytes,
                        p.max_wall_s,
                        p.max_stopped_state_bytes,
                    )
                    for p in self.plans.values()
                }
            )
            == 1,
            "PROBE_UNMATCHED_RUNTIME",
        )
        self.pair_digest = digest(pair)
        self.record = {
            "policy": self.policy,
            "pair_plan_digest": self.pair_digest,
            "launches": {arm: p.model_dump(by_alias=True) for arm, p in self.plans.items()},
            "native_probe_admission": False,
            "all_bodies_ready": False,
        }
        self.storage_bound = sum(
            2 * p.max_stopped_state_bytes + 8 * 1024**2 for p in self.plans.values()
        )
        self.held, self.sessions = None, {}
        self.result = {
            "policy": self.policy,
            "servers": {},
            "events": [],
            "observations": {},
            "model_calls": 0,
            "native_probe_admission": False,
            "all_bodies_ready": False,
            "live_initial_state_verified": False,
            "probe_disposal_verified": False,
        }

    def _scope(self):
        held = self.held
        require(
            held is not None and not held.closed and digest(held.pair) == self.pair_digest,
            "PROBE_WORLD_CUSTODY_CLOSED",
        )
        require(
            held.software is not None and held.software.policy == self.software_policy,
            "PROBE_PACK_DIRECTORY_POLICY",
        )
        require(set(held.writers) == set(self.plans), "PROBE_WORLD_ROSTER")
        return held

    def check(self):
        held = self._scope()
        # Software.check includes the complete live preparation, budget,
        # resource and source check; do not repeat it immediately beforehand.
        held.software.check()
        for arm, writer in held.writers.items():
            writer.check()
            held.software.validate(arm, writer.plan)
            if not writer.launched or arm in self.sessions and not self.sessions[arm].started:
                require(not writer.completed, "PROBE_WORLD_ALREADY_LAUNCHED")
                check_tree(writer.tree.path, writer.plan.sources)
                require(
                    {
                        p.relative_to(writer.tree.path).as_posix()
                        for p in writer.tree.path.rglob("*")
                        if p.is_dir()
                    }
                    == set(writer.plan.directories),
                    "PROBE_PACK_DIRECTORIES",
                )

    def event(self, arm, phase):
        self.result["events"].append(
            {"arm": arm, "phase": phase, "monotonic_ns": time.monotonic_ns()}
        )

    def run(self, held, continuation):
        require(self.held is None and callable(continuation), "PROBE_WORLD_CONTINUATION")
        self.held = held
        # ProbeWorldCopies just performed held.check() before recording HELD.
        # Validate this coordinator's scope here; full checks below and in
        # session.start remain mandatory before any physical dispatch.
        self._scope()
        if self.policy == BODY_POLICY:
            self.result["saved_bodies"] = held.software.record["saved_bodies"]
        # Validate and hold both initial states before starting either server.
        # Slow profile validation cannot consume the sibling's finite game window.
        for arm in held.pair["arm_order"]:
            self.sessions[arm] = ProbeVanillaSession(self, arm)
            self.event(arm, "initial_state_held")
        # Server ports are sealed: run arms in registered order without changing
        # server settings. All-N avatars within an arm remain a separate gate.
        for arm in held.pair["arm_order"]:
            self.event(arm, "launch_intent")
            session = self.sessions[arm]
            # start() performs the complete check immediately before dispatch.
            session.start()
            until = min(held.preparation.deadline, session.writer.deadline, time.monotonic() + 80)
            while not session.ready.is_set():
                require(
                    session.native.observe() is None and time.monotonic() < until,
                    "SERVER_READY_TIMEOUT",
                )
                time.sleep(0.05)
            session.verify_ready()
            self.event(arm, "server_ready")
            self.check()
            observed = continuation(arm, session)
            require(
                observed is None or len(canonical(observed)) <= 1024**2,
                "PROBE_REFERENCE_OUTPUT_QUOTA",
            )
            self.result["observations"][arm] = observed
            session.stop()
            self.event(arm, "stop_requested")
            until = min(held.preparation.deadline, session.writer.deadline, time.monotonic() + 120)
            # Normal stop only reduces execution. Its scoped writer check stays
            # in stop(); validate the complete pair while the JVM drains, before
            # accepting any capture or advancing to the sibling. A failed check
            # still fences the pair and retains every reservation.
            self.check()
            while session.native.observe() is None:
                require(time.monotonic() < until, "SERVER_STOP_TIMEOUT")
                time.sleep(0.05)
            session.finish()
            self.result["servers"][arm] = session.writer.result
            self.event(arm, "stopped_export_held")
            # The next start (or final verification) revalidates the complete
            # pair. Do not repeat the same scan between these adjacent steps.
        self.verify_stopped()
        return self.result

    def verify_stopped(self):
        self.check()
        require(set(self.sessions) == set(self.plans), "PROBE_WORLD_ROSTER")
        for arm, session in self.sessions.items():
            writer = self.held.writers[arm]
            require(
                writer.completed and writer.result["status"] == "stopped" and writer.native is None,
                "PROBE_WORLD_CLOSE_UNCERTAIN",
            )
            receipt = writer.result["vanilla"]["snapshot"]
            body = verify_snapshot(safe(receipt["path"]), receipt["manifest_sha256"])
            require(
                body["schema"] == "strata/StoppedVanillaSnapshot/3"
                and body["probe_world"] == session.provenance.model_dump(by_alias=True),
                "PROBE_WORLD_IDENTITY",
            )
