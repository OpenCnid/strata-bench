import json

import pytest

from mcbench.communication import Communication
from mcbench.controller import READINESS, Controller
from mcbench.storage import Database, Fault, Principal, safe_relative

REF = "cas:sha256:" + "a" * 64
CAPACITY = {"bodies": 4, "memory_mib": 16000, "disk_bytes": 100000000, "model_slots": 4}


def setup_campaign(controller, configs, *, n=2, campaign="c1", admission="queue"):
    config, agents = configs(n, campaign, admission)
    controller.create(config, agents)
    epoch = controller.claim(campaign, "owner", 0)
    for state in ("PROVISIONING", "VALIDATING"):
        controller.transition(campaign, "owner", epoch, controller.status(campaign)["revision"],
                              state, "synthetic-test")
    return config, epoch


def start(controller, config, epoch):
    resources = CAPACITY | {"bodies": config.n, "model_slots": config.n, "memory_mib": 1000}
    controller.certify("w", "fingerprint", CAPACITY, REF, simulation=True)
    state = controller.admit(config.campaign_id, "owner", epoch,
                             controller.status(config.campaign_id)["revision"], "w", "fingerprint",
                             resources)
    if state == "STARTING":
        controller.ready(config.campaign_id, "owner", epoch,
                         controller.status(config.campaign_id)["revision"],
                         {a: dict.fromkeys(READINESS, REF) for a in config.agent_ids})
    return state


def test_cas_acl_quota_corruption_and_journal(cas, database, operator, tmp_path):
    private = cas.put(operator, "private", "evaluator", b"private-canary")
    public = cas.put(operator, "campaign:c1:agent:a1", "agent", b"public-canary")
    agent = Principal("campaign:c1:agent:a1", "executor")
    assert cas.read(agent, agent.namespace, public) == b"public-canary"
    for namespace, ref in (("private", private), (agent.namespace, private)):
        with pytest.raises(Fault, match="FORBIDDEN"):
            cas.read(agent, namespace, ref)
    with pytest.raises(Fault, match="FORBIDDEN"):
        cas.put(Principal(agent.namespace, "helper"), agent.namespace, "agent", b"mutation")
    with pytest.raises(Fault, match="QUOTA"):
        cas.put(agent, agent.namespace, "agent", b"x" * 100, quota_bytes=50)
    assert len(list(cas.root.iterdir())) == 2
    with pytest.raises(Fault, match="POLICY_CONFLICT"):
        cas.put(operator, "private", "agent", b"private-canary")
    journal = tmp_path / "journal.jsonl"
    journal.write_bytes(b'{"partial')
    database.export_journal(journal)
    first = journal.read_bytes()
    database.export_journal(journal)
    assert journal.read_bytes() == first
    assert len([json.loads(line) for line in first.splitlines()]) == 2
    (cas.root / public[11:]).write_bytes(b"corrupt")
    with pytest.raises(Fault, match="CORRUPT"):
        cas.read(agent, agent.namespace, public)


@pytest.mark.parametrize("path", ["../x", "x/../y", "/absolute", "C:/foo", "file:stream",
    "x\\y", "x//y", "./x", "CON", "sub/nul.txt", "x.", "x ", "x\x00y", "x*y"])
def test_unsafe_paths(path):
    with pytest.raises(Fault, match="UNSAFE_PATH"):
        safe_relative(path)


def test_atomic_whole_team_admission_and_expired_cleanup(database, configs):
    now = [100.0]
    c = Controller(database, simulation=True, clock=lambda: now[0])
    config, epoch = setup_campaign(c, configs, n=4)
    assert start(c, config, epoch) == "STARTING"
    assert c.status("c1")["state"] == "RUNNING"
    second, second_epoch = setup_campaign(c, configs, n=2, campaign="c2")
    assert start(c, second, second_epoch) == "QUEUED"
    assert database.connection.execute("SELECT COUNT(*) FROM account_leases").fetchone()[0] == 4
    now[0] += 130
    # Expiry never frees still-running bodies for another team.
    c.claim("c2", "owner", c.status("c2")["revision"])
    assert start(c, second, c.status("c2")["epoch"]) == "QUEUED"
    epoch = c.claim("c1", "owner", c.status("c1")["revision"])
    with pytest.raises(Fault, match="CLEANUP"):
        c.transition("c1", "owner", epoch, c.status("c1")["revision"], "ABORTED", "timeout")
    c.transition("c1", "owner", epoch, c.status("c1")["revision"], "ABORTED", "timeout",
                 cleanup_ref=REF)
    assert start(c, second, c.status("c2")["epoch"]) == "STARTING"


def test_large_team_queues_without_allocating_any_bodies(database, configs):
    controller = Controller(database, simulation=True)
    config, epoch = setup_campaign(controller, configs, n=10000)
    assert start(controller, config, epoch) == "QUEUED"
    assert database.connection.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] == 0
    assert database.connection.execute("SELECT COUNT(*) FROM account_leases").fetchone()[0] == 0


def test_partial_readiness_revisions_scopes_helpers_and_epoch(database, configs):
    now = [100.0]
    c = Controller(database, simulation=True, clock=lambda: now[0])
    config, epoch = setup_campaign(c, configs)
    c.certify("w", "fp", CAPACITY, REF, simulation=True)
    with pytest.raises(Fault, match="PARTIAL_TEAM"):
        c.admit("c1", "owner", epoch, c.status("c1")["revision"], "w", "fp", CAPACITY | {"bodies": 1})
    c.admit("c1", "owner", epoch, c.status("c1")["revision"], "w", "fp", CAPACITY | {"bodies": 2})
    with pytest.raises(Fault, match="TEAM_NOT_READY"):
        c.ready("c1", "owner", epoch, c.status("c1")["revision"], {"a1": dict.fromkeys(READINESS, REF)})
    c.ready("c1", "owner", epoch, c.status("c1")["revision"],
            {a: dict.fromkeys(READINESS, REF) for a in config.agent_ids})
    with pytest.raises(Fault, match="FORBIDDEN"):
        c.grant("c1", "owner", epoch, "a1", "campaign:c1:agent:a1", ["act"], role="helper")
    token = c.grant("c1", "owner", epoch, "a1", "campaign:c1:agent:a1", ["observe"], quota=1)
    with pytest.raises(Fault, match="FORBIDDEN"):
        c.authorize(token, "c1", "a2", epoch, "observe", 101)
    assert c.authorize(token, "c1", "a1", epoch, "observe", 101).namespace == "campaign:c1:agent:a1"
    with pytest.raises(Fault, match="QUOTA"):
        c.authorize(token, "c1", "a1", epoch, "observe", 101)
    now[0] += 7
    new_epoch = c.claim("c1", "new-owner", c.status("c1")["revision"])
    assert new_epoch > epoch
    with pytest.raises(Fault, match="FORBIDDEN"):
        c.authorize(token, "c1", "a1", epoch, "observe", now[0] + 1)


def test_production_cannot_use_simulation_or_unresolved_evidence(database, configs, tmp_path):
    c = Controller(database)
    with pytest.raises(Fault, match="PROFILE_MISMATCH"):
        Controller(database, simulation=True)
    with pytest.raises(Fault, match="EVIDENCE_STORE_REQUIRED"):
        c.certify("w", "fp", CAPACITY, REF, simulation=False)
    with pytest.raises(Fault, match="EVIDENCE_STORE_REQUIRED"):
        config, agents = configs()
        c.validate_admission(config.model_dump(), [a.model_dump() for a in agents])
    path = tmp_path / "future.sqlite"
    db = Database(path)
    db.connection.execute("PRAGMA user_version=100")
    db.close()
    with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
        Database(path)


def test_team_order_rate_dedup_ttl_cross_team(database, configs):
    now = [100.0]
    controller = Controller(database, simulation=True, clock=lambda: now[0])
    config, epoch = setup_campaign(controller, configs)
    start(controller, config, epoch)
    messages = Communication(database, clock=lambda: now[0])
    a1, a2 = [Principal(f"campaign:c1:agent:{a}", "executor") for a in ("a1", "a2")]
    assert messages.send(a1, "c1", "a1", "m1", "hello", ["a2"], ttl=10) == 1
    assert messages.send(a1, "c1", "a1", "m1", "hello", ["a2"], ttl=10) == 1
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        messages.send(a1, "c1", "a1", "m1", "changed", ["a2"])
    with pytest.raises(Fault, match="FORBIDDEN"):
        messages.send(a1, "c1", "a1", "bad", "private", ["other-team"])
    for i in range(2, 11):
        assert messages.send(a1, "c1", "a1", f"m{i}", "hi", ["a2"], ttl=10) == i
    with pytest.raises(Fault, match="RATE_LIMITED"):
        messages.send(a1, "c1", "a1", "too-many", "hi", ["a2"])
    assert [r["seq"] for r in messages.receive(a2, "c1", "a2")] == list(range(1, 11))
    assert len(messages.receive(a2, "c1", "a2", acknowledge=["m1"])) == 9
    now[0] += 11
    assert messages.receive(a2, "c1", "a2") == []
