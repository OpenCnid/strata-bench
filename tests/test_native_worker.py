"""Native/worker lifetime join; synthetic transport, no game claim."""

from types import SimpleNamespace

import pytest

from mcbench.native_worker import NativeWorker
from mcbench.storage import Fault


def binding(database):
    worker = NativeWorker(database, {"url": "http://127.0.0.1:1/v1/game", "token": "synthetic-token-value",
        "campaign_id": "c1", "agent_id": "a1", "epoch": 1})
    plan = SimpleNamespace(job_id="root", campaign_id="c1", agent_id="a1", epoch=1,
                           role="executor", parent_job_id=None)
    return worker, plan


def test_native_exit_stops_worker_once(database):
    worker, plan = binding(database)
    worker.bind(plan)
    calls = []

    def exchange(request):
        calls.append(request)
        assert database.connection.execute("SELECT state FROM native_worker_bindings").fetchone()[0] == "STOPPING"
        return {"schema": "strata/GameResponse/1", "request_id": request.request_id,
                "status": "ok", "result": {"status": "stopped"}}

    worker.transport = exchange
    result = worker.revoke("c1", "a1", 1)
    assert worker.revoke("c1", "a1", 1) == result
    assert len(calls) == 1 and calls[0].method == "stop_all"
    assert database.connection.execute("SELECT state FROM native_worker_bindings").fetchone()[0] == "STOPPED"


@pytest.mark.parametrize("failure", ["missing", "wrong_id", "not_stopped"])
def test_missing_stop_proof_survives_reopen_without_replay(database, failure):
    worker, plan = binding(database)
    worker.bind(plan)
    calls = []

    def exchange(request):
        calls.append(request)
        if failure == "missing":
            raise TimeoutError()
        return {"schema": "strata/GameResponse/1", "request_id": "other" if failure == "wrong_id" else request.request_id,
                "status": "ok", "result": {"status": "stopped" if failure == "wrong_id" else "pending"}}

    worker.transport = exchange
    with pytest.raises((Fault, TimeoutError)):
        worker.revoke("c1", "a1", 1)
    with pytest.raises(Fault, match="NATIVE_WORKER_STOP_UNKNOWN"):
        worker.revoke("c1", "a1", 1)
    reopened, _ = binding(database)
    with pytest.raises(Fault, match="NATIVE_WORKER_ALREADY_BOUND"):
        reopened.bind(plan)
    assert len(calls) == 1
    assert database.connection.execute("SELECT state FROM native_worker_bindings").fetchone()[0] == "STOPPING"


def test_helper_wrong_scope_cannot_bind_or_stop(database):
    worker, plan = binding(database)
    plan.role = "helper"
    with pytest.raises(Fault, match="BROKER_SCOPE"):
        worker.bind(plan)
    plan.role = "executor"
    worker.bind(plan)
    with pytest.raises(Fault, match="BROKER_SCOPE"):
        worker.revoke("c1", "a1", 2)
