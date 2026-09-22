"""Private operator pack commands. Acquisition remains an explicit official workflow."""

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

import typer

from .provisioning import (
    LaunchProfile, PackProvider, ProvisioningEvidence, RoleInventoryInput, parse_acquisition,
)
from .storage import CAS, Database, Fault, require
from .pack_modes import inspect_e9e_mode

pack_app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
Store = Annotated[Path, typer.Option()]
Request = Annotated[str, typer.Option("--request")]


@contextmanager
def provider(store, simulation):
    database = Database(store / "controller.sqlite")
    try:
        yield PackProvider(database, CAS(database, store / "objects"), simulation=simulation)
    except Fault as error:
        typer.echo(json.dumps({"status": "blocked", "code": error.code, "started": False}))
        raise typer.Exit(2) from None
    finally:
        database.close()


def emit(value):
    typer.echo(json.dumps(value, indent=2))


@pack_app.command("inspect-npm-runtime")
def inspect_npm_runtime(root: Path, cache: Path, generated_shims: Path):
    """Compare installed dependencies with retained tarballs and reviewed npm shim output.

    Cache names the sha512 content directory, not a registry or npm configuration.
    Emits private evidence only; never downloads, runs scripts or seals a pack.
    """
    from .npm_runtime import verify_installed_packages
    try:
        emit(verify_installed_packages(root, cache, generated_shims))
    except Fault as error:
        emit({"status": "blocked", "code": error.code, "started": False})
        raise typer.Exit(2) from None


@pack_app.command("inspect-expert-mode")
def inspect_expert_mode(root: Path, role: str = "server", effective: bool = False,
                        world: str | None = None):
    """Read exact E9E setup/effective files. Does not start a game or pass T02."""
    try:
        result = inspect_e9e_mode(root, role, effective=effective, world=world)
    except Fault as error:
        emit({"status": "blocked", "code": error.code, "started": False})
        raise typer.Exit(2) from None
    emit(result)
    if result["file_result"] != "pass":
        raise typer.Exit(2)


@pack_app.command("resolve")
def resolve(target: str, request: Request, store: Store, simulation: bool = False):
    """Resolve the exact pinned target without downloading or installing anything."""
    with provider(store, simulation) as service:
        emit(service.resolve_candidate(request, target).model_dump())


@pack_app.command("acquire")
def acquire(request: Request, store: Store, simulation: bool = False):
    """Persist the official acquisition request and display required operator work."""
    with provider(store, simulation) as service:
        emit(service.request_acquisition(request))


@pack_app.command("import")
def import_receipt(receipt: Annotated[Path, typer.Option()], store: Store, simulation: bool = False):
    """Import exact official distributions and a provenance receipt into private storage."""
    with provider(store, simulation) as service:
        from .inference_transport import strict_json
        parsed = parse_acquisition(strict_json(receipt.read_bytes()))
        emit({"receipt": service.import_acquisition_receipt(parsed)})


@pack_app.command("evidence")
def import_evidence(request: Request, file: Annotated[Path, typer.Option()], store: Store,
                    simulation: bool = False, preserve_source_bytes: bool = False):
    """Import operator-authored JSON evidence; does not certify its truth or any gate."""
    with provider(store, simulation) as service:
        service._row(request, active=True)
        from .inference_transport import strict_json
        require(file.stat().st_size <= 64 * 1024**2, "ARTIFACT_QUOTA")
        raw = file.read_bytes()
        value = strict_json(raw)
        ref = (service.cas.put(service.principal, service.namespace(request), "operator", raw,
                               quota_bytes=service.quota, max_object_bytes=64 * 1024**2)
               if preserve_source_bytes else service._put(request, value))
        emit({"ref": ref, "authority": "operator_attestation"})


@pack_app.command("verify")
def verify(request: Request, inventory: Annotated[Path, typer.Option()], store: Store,
           simulation: bool = False):
    """Check every installed file, source provenance and immutable imported bytes."""
    with provider(store, simulation) as service:
        roles = [RoleInventoryInput.model_validate(r)
                 for r in json.loads(inventory.read_text(encoding="utf-8"))]
        emit({"inventory": service.verify_inventory(request, roles)})


@pack_app.command("prepare-vanilla-server")
def prepare_vanilla_server(root: Path, destination: Path, request: Request, store: Store,
                           simulation: bool = False):
    """Verify acquired/installed server payloads and prepare a new private software copy."""
    with provider(store, simulation) as service:
        emit(service.prepare_vanilla_server(request, root, destination))


@pack_app.command("prepare-vanilla-client")
def prepare_vanilla_client(assets: Path, destination: Path, request: Request, store: Store,
                           library_root: Annotated[list[Path], typer.Option("--library-root")],
                           simulation: bool = False):
    """Prepare the acquired Windows client with exact cached libraries/assets."""
    with provider(store, simulation) as service:
        emit(service.prepare_vanilla_client(request, assets, library_root, destination))


@pack_app.command("prepare-vanilla-worker")
def prepare_vanilla_worker(repository: Path, node: Path, python_root: Path, destination: Path,
                           npm_evidence: Annotated[str, typer.Option()], request: Request, store: Store):
    """Copy a private worker/stdlib helper runtime from existing reviewed software.

    Requires retained npm evidence in the original request. No auth or game launch.
    """
    from .worker_bundle import prepare_worker_bundle
    with provider(store, False) as service:
        require(".." not in destination.parts and ".." not in store.parts, "WORKER_BUNDLE_PATH")
        row = service._row(request, active=True)
        require(row["target"] == "vanilla" and row["state"] in {"VERIFIED", "SEALED"}, "UNVERIFIED_PACK")
        require(not destination.absolute().is_relative_to(store.absolute())
                and not store.absolute().is_relative_to(destination.absolute()), "UNSAFE_PATH")
        emit(prepare_worker_bundle(repository, node, python_root, destination,
             service._json(request, npm_evidence), npm_evidence))


@pack_app.command("seal")
def seal(request: Request, launch: Annotated[Path, typer.Option()],
         evidence: Annotated[Path, typer.Option()], store: Store, simulation: bool = False):
    """Freeze a verified template; keeps conformance and campaign admission separate."""
    with provider(store, simulation) as service:
        profile = LaunchProfile.model_validate_json(launch.read_text(encoding="utf-8"))
        proof = ProvisioningEvidence.model_validate_json(evidence.read_text(encoding="utf-8"))
        emit({"lock": service.seal_template(request, profile, proof)})


@pack_app.command("materialize")
def materialize(destination: Path, request: Request, store: Store, simulation: bool = False):
    """Copy sealed bytes into a NEW instance. Never starts scripts, Java or a client."""
    with provider(store, simulation) as service:
        emit(service.materialize(request, destination))


@pack_app.command("status")
def status(request: Request, store: Store, simulation: bool = False):
    """Read the durable request state without acquisition retries."""
    with provider(store, simulation) as service:
        emit(service.status(request))
