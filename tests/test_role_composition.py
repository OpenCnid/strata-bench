"""Synthetic paired composition; expert/game behavior requires actual evidence."""

import hashlib

import pytest

from mcbench import role_composition as c
from mcbench.provisioning import PackProvider
from mcbench.storage import Fault


@pytest.fixture
def prepared(tmp_path, monkeypatch, database, cas):
    service = PackProvider(database, cas, simulation=True)
    service.resolve_candidate("pack", "e9e")
    proof = service._put("pack", {"scope": "synthetic operator evidence"})
    with database.transaction() as db:
        db.execute("UPDATE provisioning SET state='ACQUIRED',receipt=? WHERE id='pack'", (proof,))
    roles = []
    for role in ("client", "server"):
        source = tmp_path / (role + ".txt")
        raw = (role + " synthetic payload").encode()
        source.write_bytes(raw)
        roles.append({"role": role, "directories": ["empty"], "files": [{"source": str(source), "entry": {
            "role": role, "path": "config/fixture.txt", "digest": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "origin": "synthetic origin", "license_ref": proof, "layer": "resolved",
            "project_id": None, "file_id": None}}]})
    plan = {"schema": "strata/E9ERoleComposition/1", "request_id": "pack", "acquisition_receipt": proof,
            "source_reports": [proof], "component_notices": proof, "exclusions": proof, "roles": roles}
    monkeypatch.setattr(c, "inspect_e9e_mode", lambda *a, **k: {"file_result": "pass", "scope": "synthetic setup fixture"})
    return service, plan, tmp_path / "output"


def test_independent_roles_keep_notices_and_state_unpromoted(prepared):
    service, plan, output = prepared
    result = service.prepare_e9e_roles("pack", plan, output)
    assert result["initial_roles_only"] and not result["effective_configuration_qualified"]
    assert service._row("pack")["state"] == "ACQUIRED"
    for role in result["roles"]:
        assert (output / role["role"] / "empty").is_dir()
        assert role["files"][0]["license_ref"] == plan["component_notices"]
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        service.prepare_e9e_roles("pack", plan, output)


@pytest.mark.parametrize("fault", ["second_source", "duplicate", "file_parent", "receipt", "namespace", "role", "world"])
def test_both_roles_preflight_before_output(prepared, fault):
    service, plan, output = prepared
    item = plan["roles"][1]["files"][0]
    if fault == "second_source":
        item["entry"]["digest"] = "0" * 64
    elif fault == "duplicate":
        plan["roles"][1]["files"].append(dict(item))
    elif fault == "file_parent":
        plan["roles"][1]["directories"].append("config/fixture.txt/child")
    elif fault == "receipt":
        plan["acquisition_receipt"] = "cas:sha256:" + "0" * 64
    elif fault == "namespace":
        item["entry"]["license_ref"] = service._put("other", {"foreign": True})
    elif fault == "role":
        item["entry"]["role"] = "client"
    else:
        item["entry"]["path"] = "world/playerdata/player.dat"
    with pytest.raises(Fault):
        service.prepare_e9e_roles("pack", plan, output)
    assert not output.exists()


def test_failed_initial_expert_setup_retains_partial_output(prepared, monkeypatch):
    service, plan, output = prepared
    monkeypatch.setattr(c, "inspect_e9e_mode", lambda *a, **k: {"file_result": "fail"})
    with pytest.raises(Fault, match="INITIAL_EXPERT_SETUP_MISMATCH"):
        service.prepare_e9e_roles("pack", plan, output)
    assert output.exists() and service._row("pack")["state"] == "ACQUIRED"
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        service.prepare_e9e_roles("pack", plan, output)


def test_source_changed_after_preflight_retains_unpromoted_partial_roles(prepared, monkeypatch):
    from pathlib import Path
    service, plan, output = prepared
    def inspect(root, **kwargs):
        # Client finished; change a server source after both plans passed preflight.
        Path(plan["roles"][1]["files"][0]["source"]).write_bytes(b"changed during paired copy")
        return {"file_result": "pass"}
    monkeypatch.setattr(c, "inspect_e9e_mode", inspect)
    with pytest.raises(Fault, match="SOURCE_CHANGED"):
        service.prepare_e9e_roles("pack", plan, output)
    assert (output / "client/config/fixture.txt").exists()
    assert service._row("pack")["state"] == "ACQUIRED"
