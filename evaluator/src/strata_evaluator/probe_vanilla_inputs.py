"""Held sealed vanilla software plus exact registered probe state; no launch permit."""

import json
import os
from pathlib import Path

from mcbench.launch_integrity import FileLease, safe, snapshot
from mcbench.pack_launch import PackLaunchBinding, resolve_pack_launch
from mcbench.storage import digest, extended_path, require
from mcbench.vanilla_persistence import (
    MUTABLE,
    disposition,
    template_directory_layout,
    template_files,
)

POLICY = "held-pair-sealed-vanilla-inputs/1"


class VanillaProbeInputs:
    """Borrow a fresh sealed installation while both protected copies exist.

    The common ancestor used by the copier is a path-containment check only;
    only the explicit compiled files enter its native workspace. Evaluation
    manifests, client software and the provisioning store are never copied.
    """

    def __init__(self, preparation, value):
        self.preparation = preparation
        self.binding = PackLaunchBinding.model_validate(value)
        require(type(self.binding) is PackLaunchBinding, "PROBE_PACK_TEMPLATE")
        self.lease = None
        self.closed = False

    def __enter__(self):
        prep = self.preparation
        prep.check()
        pair, _, target, *_ = prep._source(prep.pair_id)
        require(self.binding.lock == pair["common"]["pack_lock"], "PROBE_PACK_MISMATCH")
        resolved = resolve_pack_launch(self.binding, "server")
        require(resolved["target"] == "vanilla", "PROBE_PACK_UNSUPPORTED")
        root = safe(Path(self.binding.instance) / "server")
        inventory_path = safe(Path(self.binding.store) / "objects" / resolved["inventory_digest"])
        inventory = json.loads(inventory_path.read_bytes())
        require(digest(inventory) == resolved["inventory_digest"], "PROBE_PACK_MISMATCH")
        template = template_files(
            inventory, {key: resolved[key] for key in ("lock", "request_id", "inventory_digest")}
        )
        software = {
            name: entry
            for name, entry in template.items()
            if disposition(name, template) == "immutable"
        }
        # This copier creates file parents, not arbitrary empty directories.
        # Refuse a wider sealed layout instead of silently dropping it.
        parents = {p.as_posix() for name in software for p in Path(name).parents if str(p) != "."}
        require(
            set(template_directory_layout(inventory)) <= parents, "PROBE_PACK_EMPTY_DIRECTORIES"
        )
        state = {}
        for name in pair["world_files"]:
            destination = name.removeprefix("external/")
            require(
                (not name.startswith("external/") or destination in MUTABLE)
                and disposition(destination, template) == "state",
                "PROBE_PACK_STATE_LAYOUT",
            )
            require(
                destination not in state and destination not in software, "PROBE_PACK_STATE_LAYOUT"
            )
            state[destination] = name
        require(MUTABLE | {"world/level.dat"} <= state.keys(), "PROBE_PACK_STATE_INCOMPLETE")
        sources, roots = {}, {}
        for arm in pair["arm_order"]:
            original = target / pair["arm_directories"][arm] / "server"
            selected = {
                name: entry | {"path": str(root / name)} for name, entry in software.items()
            }
            for destination, name in state.items():
                ref = pair["world_files"][name]
                row = prep.db.connection.execute(
                    "SELECT bytes FROM objects WHERE namespace=? AND ref=?",
                    (prep.views.namespace, ref),
                ).fetchone()
                require(row is not None, "PROBE_PRIVATE_SOURCE")
                selected[destination] = {
                    "path": str(original / name),
                    "sha256": ref[11:],
                    "bytes": row[0],
                }
            sources[arm] = selected
            roots[arm] = str(Path(os.path.commonpath([p["path"] for p in selected.values()])))
        self.sources, self.roots = sources, roots
        self.resolved = resolved
        self.record = {
            "policy": POLICY,
            "binding": self.binding.model_dump(),
            "resolved_digest": digest(resolved),
            "world_digest": pair["world_digest"],
            "state_mapping": state,
            "sources": sources,
            "source_roots": roots,
            "native_launch_authorized": False,
            "live_initial_state_verified": False,
        }
        # Include exact inventory metadata and all materialization files so a
        # changed template cannot be accepted between resolution and copying.
        self.lease = FileLease(snapshot([inventory_path], [Path(self.binding.instance)]))
        try:
            self.check()
            return self
        except BaseException:
            self.close()
            raise

    def check(self):
        require(not self.closed and self.lease is not None, "PROBE_PACK_CUSTODY_CLOSED")
        self.preparation.check()
        self.lease.recheck()
        require(resolve_pack_launch(self.binding, "server") == self.resolved, "PROBE_PACK_CHANGED")

    def validate(self, arm, plan):
        require(
            extended_path(Path(plan.source_root)) == extended_path(Path(self.roots[arm]))
            and {
                name: {**pin.model_dump(), "path": str(extended_path(Path(pin.path)))}
                for name, pin in plan.sources.items()
            }
            == {
                name: {**pin, "path": str(extended_path(Path(pin["path"])))}
                for name, pin in self.sources[arm].items()
            },
            "PROBE_WORLD_SOURCE",
        )
        launch = self.resolved["launch"]
        require(
            extended_path(Path(plan.java.path)) == extended_path(Path(launch["executable_path"]))
            and plan.java.sha256 == launch["executable"]["digest"],
            "PROBE_PACK_JAVA",
        )

    def close(self):
        self.closed = True
        if self.lease is not None:
            self.lease.close()

    def __exit__(self, *args):
        self.close()
