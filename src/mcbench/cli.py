"""Read-only operator commands. No implicit game installation or inference dispatch."""

import json
from pathlib import Path

import typer

from mcbench.conformance import AcquisitionInputs, preflight
from mcbench.commands import authorization_app, campaign_app, journal_app
from mcbench.records import RECORDS
from mcbench.packaging import package_gameplay
from mcbench.pack_commands import pack_app
from mcbench.runtime import ExecUsageReader, inspect_codex

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
conformance = typer.Typer(no_args_is_help=True)
app.add_typer(conformance, name="conformance")
app.add_typer(campaign_app, name="campaign")
app.add_typer(journal_app, name="journal")
app.add_typer(pack_app, name="pack")
app.add_typer(authorization_app, name="authorization")


def output(value):
    typer.echo(json.dumps(value, indent=2))


@app.command()
def doctor():
    """Fingerprint Codex and report unverified host prerequisites; uses no inference."""
    output(inspect_codex())
    raise typer.Exit(2)


@app.command()
def validate(record: Path):
    """Validate any canonical record. Does not admit examples or a campaign."""
    data = json.loads(record.read_text(encoding="utf-8"))
    model = RECORDS.get(data.get("schema"))
    if model is None:
        output({"status": "error", "code": "SCHEMA_UNSUPPORTED"})
        raise typer.Exit(4)
    model.model_validate(data)
    output({"status": "valid", "admitted": False, "is_example": data.get("is_example")})


@conformance.command("preflight")
def conformance_preflight(target: str = "e9e", artifacts: Path | None = None):
    """Report the complete compact-suite checklist and typed missing prerequisites."""
    inputs = (
        AcquisitionInputs.model_validate_json(artifacts.read_text(encoding="utf-8"))
        if artifacts
        else None
    )
    output(preflight(target, inputs))
    raise typer.Exit(2)


@app.command("inspect-events")
def inspect_events(events: Path):
    """Inspect a captured exec JSONL file privately; never claims all-call accounting."""
    reader = ExecUsageReader()
    with events.open(encoding="utf-8") as stream:
        for cursor, line in enumerate(stream, 1):
            if len(line.encode("utf-8")) > 1024 * 1024:
                raise ValueError("CAPACITY_EXCEEDED")
            reader.ingest(cursor, line)
    output(reader.report())


@app.command("package-gameplay")
def package_client(repository: Path, destination: Path):
    """Package the allowlisted scoped client/skill only, after compiling the Node client."""
    output(package_gameplay(repository, destination))
