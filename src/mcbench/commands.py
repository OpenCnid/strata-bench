"""Operator command facades over the durable services. Never mounted for agents."""

import json
from pathlib import Path
from typing import Annotated

import typer

from .controller import Controller
from .authorization import Authorizations, ExecutionAuthorization, parse_authorization
from .records import AgentConfig, CampaignConfig
from .storage import CAS, Database, Fault, require

campaign_app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
journal_app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
authorization_app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)


def emit(value):
    typer.echo(json.dumps(value, indent=2))


@authorization_app.command("install")
def authorize(file: Annotated[Path, typer.Option()], store: Annotated[Path, typer.Option()]):
    """Persist an already approved aggregate allowance. Does not start a model or game."""
    database = Database(store / "controller.sqlite")
    try:
        policy = parse_authorization(file.read_text(encoding="utf-8"))
        service = Authorizations(database)
        service.install(policy)
        emit(service.status(policy.authorization_id))
    finally:
        database.close()


@authorization_app.command("migration-snapshot")
def authorization_snapshot(store: Annotated[Path, typer.Option()]):
    """Get the required accounting fingerprint before explicit legacy migration."""
    require((store / "controller.sqlite").is_file(), "STORE_MISSING")
    database = Database(store / "controller.sqlite")
    try:
        emit({"snapshot_digest": Authorizations(database).snapshot()})
    finally:
        database.close()


@authorization_app.command("migrate")
def migrate_authorization(file: Annotated[Path, typer.Option()],
                          evidence: Annotated[Path, typer.Option()],
                          snapshot_digest: Annotated[str, typer.Option()],
                          legacy_amount_semantics: Annotated[str, typer.Option()],
                          store: Annotated[Path, typer.Option()]):
    """Preserve the existing allowance/receipts/holds and install D11's estimate basis."""
    require((store / "controller.sqlite").is_file(), "STORE_MISSING")
    database = Database(store / "controller.sqlite")
    try:
        from .storage import Principal
        policy = ExecutionAuthorization.model_validate_json(file.read_text(encoding="utf-8"))
        cas = CAS(database, store / "objects")
        ref = cas.put(Principal("operator", "operator"), "operator", "operator",
                      evidence.read_bytes())
        service = Authorizations(database)
        service.migrate(policy, snapshot_digest=snapshot_digest, evidence_ref=ref,
                        legacy_amount_semantics=legacy_amount_semantics, cas=cas)
        emit(service.status(policy.authorization_id))
    finally:
        database.close()


@authorization_app.command("status")
def authorization_status(authorization_id: str, store: Annotated[Path, typer.Option()]):
    require((store / "controller.sqlite").is_file(), "STORE_MISSING")
    database = Database(store / "controller.sqlite")
    try:
        emit(Authorizations(database).status(authorization_id))
    finally:
        database.close()


@campaign_app.command("validate")
def validate(config: Annotated[Path, typer.Option()], agents: Annotated[Path, typer.Option()]):
    """Validate roster, identities, schedules and account uniqueness without starting work."""
    campaign = CampaignConfig.model_validate_json(config.read_text(encoding="utf-8"))
    roster = [AgentConfig.model_validate(a) for a in json.loads(agents.read_text(encoding="utf-8"))]
    require(len(roster) == campaign.n and {a.agent_id for a in roster} == set(campaign.agent_ids),
            "ROSTER_MISMATCH")
    require(all(a.system_digest == campaign.system_digest for a in roster), "SYSTEM_MISMATCH")
    require(len({a.account_ref for a in roster}) == campaign.n, "ACCOUNT_CONFLICT")
    emit({"status": "valid", "admitted": False, "n": campaign.n,
          "requires": ["sealed_artifacts", "integration_evidence", "capacity", "isolation", "budgets"]})


@campaign_app.command("create")
def create(config: Annotated[Path, typer.Option()], agents: Annotated[Path, typer.Option()],
           store: Annotated[Path, typer.Option()], simulation: bool = False):
    """Persist a DRAFT only. Simulation stores can never become live stores."""
    database = Database(store / "controller.sqlite")
    try:
        controller = Controller(database, simulation=simulation, cas=CAS(database, store / "objects"))
        campaign = CampaignConfig.model_validate_json(config.read_text(encoding="utf-8"))
        roster = [AgentConfig.model_validate(a) for a in json.loads(agents.read_text(encoding="utf-8"))]
        controller.create(campaign, roster)
        emit(controller.status(campaign.campaign_id))
    finally:
        database.close()


@campaign_app.command("status")
def status(campaign_id: str, store: Annotated[Path, typer.Option()]):
    """Read durable campaign status; never renew a lease or trigger a process."""
    require((store / "controller.sqlite").is_file(), "STORE_MISSING")
    database = Database(store / "controller.sqlite")
    try:
        row = Controller.row(database.connection, campaign_id)
        emit({k: row[k] for k in ("id", "state", "revision", "epoch", "lease_until")})
    finally:
        database.close()


@campaign_app.command("preflight")
def preflight(config: Annotated[Path, typer.Option()], agents: Annotated[Path, typer.Option()],
              store: Annotated[Path, typer.Option()]):
    """Resolve admission prerequisites privately. Does not dispatch game/model jobs."""
    database = Database(store / "controller.sqlite")
    try:
        controller = Controller(database, cas=CAS(database, store / "objects"))
        campaign = CampaignConfig.model_validate_json(config.read_text(encoding="utf-8"))
        roster = [AgentConfig.model_validate(a) for a in json.loads(agents.read_text(encoding="utf-8"))]
        try:
            controller.validate_admission(campaign.model_dump(), [a.model_dump() for a in roster])
        except Fault as error:
            emit({"status": "blocked", "code": error.code, "started": False})
            raise typer.Exit(2) from None
        emit({"status": "prerequisites_resolved", "admitted": False})
    finally:
        database.close()


@journal_app.command("export")
def export(store: Annotated[Path, typer.Option()], destination: Annotated[Path, typer.Option()]):
    """Rebuild the private JSONL journal from the durable transactional outbox."""
    require((store / "controller.sqlite").is_file(), "STORE_MISSING")
    database = Database(store / "controller.sqlite")
    try:
        database.export_journal(destination)
        emit({"status": "exported", "visibility": "operator"})
    finally:
        database.close()
