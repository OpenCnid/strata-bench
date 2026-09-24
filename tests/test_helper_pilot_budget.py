"""Nested helper admission against synthetic retained uncertainty, no paid calls."""
import time

import pytest

from mcbench.budgets import DIMENSIONS
from mcbench.pilot_budget import decision_body, decision_job
from mcbench.storage import Fault, canonical
from native_dispatch_probe import ledger
import test_luna6_pilot_budget as previous

trial, make_plan = previous.trial, previous.make_plan
pilot_trial, corrected_trial = previous.pilot_trial, previous.corrected_trial
luna6, retained_pilot = previous.luna6, previous.retained_pilot


@pytest.fixture
def helper_pilot(retained_pilot):
    t = retained_pilot
    db = t.db.connection
    for index in range(1, 6):
        job = decision_job(f"D19.{index}")
        db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,?,NULL,NULL)",
            (job, "old", "a1", 1, "executor", None, "synthetic", "{}", "FINALIZED", time.time()))
        db.execute("INSERT INTO native_gateways VALUES(?,'CLOSED','fixture-fence')", (job,))
    t.decision = decision_body(db, "D19.6", helper=True)
    job = t.decision["job_id"]
    t.plan = t.plan.model_copy(update={"job_id": job, "account": job+":account", "operation_id": job+":envelope",
                                     "helper_limit": 1, "hard_timeout_s": 240})
    t.budgets.create_account(t.plan.account, dict.fromkeys(DIMENSIONS, None) |
        {"spend_microusd": 1000000, "model_calls": 16}, t.plan.campaign_id, "a1", t.authority, category="development")
    t.root = t.root.model_copy(update={"operation_id": t.plan.operation_id,
        "source_event_id": job+":reserve", "ledger_id": job+":ledger",
        "usage": t.root.usage.model_copy(update={"model_calls": 16, "input_tokens": 1050000*16,
                                               "output_tokens": 128000*16})})
    t.authorize()
    db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
        (job, t.plan.campaign_id, "a1", 1, "executor", None, "synthetic",
         canonical(t.plan.model_dump()).decode(), "PREPARED"))
    t.budgets.post(t.plan.account, t.root, envelope=True)
    db.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (job,))
    t.helper_envelope = "child:"+"a"*64
    def reserve(name, parent=None, helper=False):
        return ledger(t.plan, name, parent=parent or t.plan.operation_id, calls=1, spend=358500,
                      pricing=t.root.pricing_ref, inputs=1050000, outputs=128000).model_copy(
                          update={"kind": "helper" if helper else "model"})
    t.reserve = reserve
    return t


@pytest.mark.parametrize("luna6", ["D18.4"], indirect=True)
def test_one_helper_is_nested_charged_once_with_bounded_overlap(helper_pilot):
    t = helper_pilot
    first = t.reserve("first-root")
    t.budgets.post(t.plan.account, first)
    previous.prior.settle(t, first)
    child = t.reserve(t.helper_envelope, helper=True)
    t.budgets.post(t.plan.account, child, envelope=True)
    helper = t.reserve("helper-reply", t.helper_envelope, True)
    t.budgets.post(t.plan.account, helper)
    overlapping = t.reserve("concurrent-root")
    t.budgets.post(t.plan.account, overlapping)
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post(t.plan.account, t.reserve("second-concurrent-root"))
    previous.prior.settle(t, overlapping)
    previous.prior.settle(t, helper)
    last = t.reserve("last-root")
    t.budgets.post(t.plan.account, last)
    previous.prior.settle(t, last)
    assert t.db.connection.execute("SELECT requests FROM pilot_trials WHERE job=?", (t.plan.job_id,)).fetchone()[0] == 4
    assert previous.prior.uncertain_rows(t.db.connection, t.authority) == t.retained_all
    assert t.budgets.status(t.authority)["committed_and_reserved"]["spend_microusd"] == t.decision["combined_exposure_microusd"]
    # Child and root reservations are envelopes, so only four actual calls settle.
    for envelope in (child, t.root):
        receipt = envelope.model_copy(update={"posting": "settle", "metering": "reported",
            "source_event_id": envelope.source_event_id+":closed", "raw_usage_ref": t.root.pricing_ref,
            "usage": envelope.usage.model_copy(update=dict.fromkeys(envelope.usage.model_dump(), 0))})
        with t.db.transaction() as db:
            t.budgets.post_in_transaction(db, t.plan.account, receipt, close_envelope=True)
    assert t.budgets.status(t.authority)["committed_and_reserved"]["spend_microusd"] == t.decision["prior_exposure_microusd"]+4000


@pytest.mark.parametrize("luna6", ["D18.4"], indirect=True)
@pytest.mark.parametrize("case", ["second_helper", "grandchild", "extra_helper_call", "unknown_helper",
                                 "root_as_helper", "child_as_root", "larger_child", "unreserved_child"])
def test_helper_profile_cannot_expand_or_ignore_unknown(helper_pilot, case):
    t = helper_pilot
    child = t.reserve(t.helper_envelope, helper=True)
    if case == "larger_child":
        child = child.model_copy(update={"usage": child.usage.model_copy(update={"model_calls": 2})})
        with pytest.raises(Fault, match="METERING_UNKNOWN"):
            t.budgets.post(t.plan.account, child, envelope=True)
        return
    if case != "unreserved_child":
        t.budgets.post(t.plan.account, child, envelope=True)
    if case in {"extra_helper_call", "unknown_helper"}:
        request = t.reserve("child-first", t.helper_envelope, True)
        t.budgets.post(t.plan.account, request)
        if case == "unknown_helper":
            t.budgets.hold_uncertain(t.plan.account, request.operation_id, "synthetic missing receipt")
        else:
            previous.prior.settle(t, request)
    request = t.reserve("bad-child", t.helper_envelope, True)
    envelope = case in {"second_helper", "grandchild"}
    if envelope:
        request = t.reserve("child:"+"b"*64, t.plan.operation_id if case == "second_helper" else t.helper_envelope, True)
    elif case in {"root_as_helper", "unknown_helper"}:
        request = t.reserve("bad-root", helper=case == "root_as_helper")
    elif case == "child_as_root":
        request = request.model_copy(update={"kind": "model"})
    with pytest.raises(Fault, match="METERING_UNKNOWN|ENVELOPE_EXHAUSTED|FORBIDDEN"):
        t.budgets.post(t.plan.account, request, envelope=envelope)


@pytest.mark.parametrize("luna6", ["D18.4"], indirect=True)
def test_old_decisions_keep_zero_helpers_and_bounds(retained_pilot):
    t = retained_pilot
    assert decision_body(t.db.connection, "D19.1")["helper_limit"] == 0
    with pytest.raises(Fault, match="PILOT_HELPER_DECISION"):
        decision_body(t.db.connection, "D19.1", helper=True)
