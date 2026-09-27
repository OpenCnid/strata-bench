"""Private probe bootstrap and scoped broker projection, without launch authority."""

from pathlib import Path

from .launch_integrity import read_manifest, safe, safe_many, snapshot
from .native_export import OPERATOR
from .native_probe_binding import artifact_inputs, require_binding_scope
from .storage import (
    Principal,
    canonical,
    digest,
    extended_path,
    reject_links,
    require,
    safe_relative,
)

POLICY = "prepared-probe-bootstrap-and-role-projection/1"
IMMUTABLE = {"initial", "docs", "supplied", "active"}


def validate_probe_bootstrap(db, cas, plan):
    """Join approved workspace bytes to the pinned complete bootstrap tree.

    This checks inventory; the supervisor must still own the actual bootstrap
    leases and matched world/runtime custody throughout execution.
    """
    body = require_binding_scope(db, cas, plan)
    files = dict(body.broker_files["executor"])
    files.update(
        {
            ".agents/skills/" + name + "/" + path: ref
            for name, skill in body.catalog.items()
            for path, ref in skill.files.items()
        }
    )
    require(0 < len(files) <= 2048, "PROBE_ARTIFACT_QUOTA")
    expected_dirs = set()
    for name in files:
        expected_dirs.update(str(p) for p in safe_relative(name).parents if str(p) != ".")
    target = extended_path(Path(plan.workspace))
    current = snapshot([], [target])
    actual = {
        Path(e["path"]).relative_to(safe(target)).as_posix(): "cas:sha256:" + e["sha256"]
        for e in current["files"]
    }
    require(actual == files, "PROBE_ARTIFACT_VIEW_CHANGED")
    directories = set()
    for path in target.rglob("*"):
        reject_links(path)
        if path.is_dir():
            directories.add(path.relative_to(target).as_posix())
            require(len(directories) <= 8192, "PROBE_ARTIFACT_QUOTA")
    require(directories == expected_dirs, "PROBE_ARTIFACT_VIEW_CHANGED")
    require(
        plan.bootstrap_manifest is not None and plan.bootstrap_digest is not None,
        "PROBE_BOOTSTRAP_REQUIRED",
    )
    manifest = read_manifest(plan.bootstrap_manifest, plan.bootstrap_digest)
    entries = manifest["inventory"]["files"]
    pinned = {
        str(path): entry
        for path, entry in zip(safe_many(e["path"] for e in entries), entries, strict=True)
    }
    require(len(pinned) == len(entries), "PROBE_ARTIFACT_UNPINNED")
    trees = [t for t in manifest["inventory"]["trees"] if safe(t["path"]) == safe(target)]
    require(
        len(trees) == 1
        and set(trees[0]["files"]) == set(current["trees"][0]["files"])
        and len(trees[0]["files"]) == len(current["trees"][0]["files"])
        and all(pinned.get(e["path"]) == e for e in current["files"]),
        "PROBE_ARTIFACT_UNPINNED",
    )
    return body


def project_probe_artifacts(database, cas, plan, grant, broker):
    """Project approved content once, after authenticated root/helper enrollment.

    Private bindings, provenance, pair metadata and catalogs are never broker
    files. A repeated admission must not overwrite later local adaptation.
    """
    require(
        grant.runtime_id == plan.job_id == broker.runtime_id
        and grant.profile_digest == plan.profile_digest() == broker.profile_digest
        and all(
            getattr(grant, k) == getattr(plan, k)
            for k in ("campaign_id", "agent_id", "epoch", "model")
        ),
        "PROBE_PROJECTION_SCOPE",
    )
    require(
        broker._grant(database.connection, grant.thread_id)[0] == grant, "PROBE_PROJECTION_SCOPE"
    )
    validate_probe_bootstrap(database.connection, cas, plan)
    files = artifact_inputs(database.connection, cas, plan, grant.role)
    require(0 < len(files) <= 1024, "ARTIFACT_QUOTA")
    for path, ref in files.items():
        broker._path(path)
        raw = cas.read(OPERATOR, "operator", ref, max_bytes=256 * 1024)
        raw.decode("utf-8")
        require(
            cas.put(
                Principal(grant.namespace, "executor"),
                grant.namespace,
                "agent",
                raw,
                media_type="text/plain",
            )
            == ref,
            "CORRUPT_EVIDENCE",
        )
    marker = (
        plan.job_id,
        grant.thread_id,
        plan.probe_binding_ref,
        grant.namespace,
        grant.role,
        digest(files),
    )
    with database.transaction() as db:
        require(broker._grant(db, grant.thread_id)[0] == grant, "PROBE_PROJECTION_SCOPE")
        validate_probe_bootstrap(db, cas, plan)
        require(artifact_inputs(db, cas, plan, grant.role) == files, "PROBE_PROJECTION_SCOPE")
        db.execute(
            "CREATE TABLE IF NOT EXISTS native_probe_projections (runtime TEXT,thread TEXT,"
            "binding_ref TEXT,namespace TEXT UNIQUE,role TEXT,files_digest TEXT,PRIMARY KEY(runtime,thread))"
        )
        old = db.execute(
            "SELECT * FROM native_probe_projections WHERE runtime=? AND thread=?", marker[:2]
        ).fetchone()
        existing = {
            r["path"]: (r["ref"], r["immutable"])
            for r in db.execute("SELECT * FROM broker_files WHERE namespace=?", (grant.namespace,))
        }
        if old:
            require(
                tuple(old) == marker
                and all(
                    existing.get(p) == (ref, 1)
                    for p, ref in files.items()
                    if p.split("/")[0] in IMMUTABLE
                ),
                "PROBE_PROJECTION_CHANGED",
            )
            return  # Keep root notes and newly written probe-local artifacts.
        require(not existing, "PROBE_PROJECTION_NAMESPACE_NOT_FRESH")
        for path, ref in files.items():
            db.execute(
                "INSERT INTO broker_files VALUES(?,?,?,?)",
                (grant.namespace, path, ref, int(path.split("/")[0] in IMMUTABLE)),
            )
        db.execute("INSERT INTO native_probe_projections VALUES(?,?,?,?,?,?)", marker)
        database.event(
            db,
            "native.probe_artifacts_projected",
            {
                "policy": POLICY,
                "runtime": plan.job_id,
                "thread": grant.thread_id,
                "role": grant.role,
                "binding_ref": plan.probe_binding_ref,
                "files_digest": digest(files),
                "inventory": canonical(files).decode(),
            },
        )
