"""Live native purpose/account separation; never applied to stopped evidence.

Evaluation needs its own disposable admission path. It must not enter a campaign
or borrow a development conformance profile merely by changing the launch label.
"""

from .budgets import Budgets
from .records import BudgetLedger
from .storage import require


def require_purpose_category(purpose, category):
    allowed = {"campaign": {"training", "development"},
               "conformance": {"development"}, "development_piloting": {"development"}}
    require(purpose in allowed and category in allowed[purpose],
            "CONFORMANCE_ACCOUNT_REQUIRED" if purpose in {"conformance", "development_piloting"}
            else "NATIVE_ACCOUNT_PURPOSE")


def require_native_account(db, plan, reserve=None):
    """Join the actual leaf and aggregate identities before new live effects.

    Unclassified aggregate accounts may pool explicitly classified children;
    the native leaf cannot be unclassified. No costs, labels or holds are changed.
    """
    chain = Budgets.ancestors(db, plan.account)
    leaf = chain[0]
    require_purpose_category(plan.purpose, leaf["category"])
    require(leaf["campaign"] == plan.campaign_id and leaf["agent"] == plan.agent_id,
            "NATIVE_ACCOUNT_SCOPE")
    require(all(a["category"] in (None, leaf["category"]) and
                a["campaign"] in ("*", plan.campaign_id) for a in chain[1:]), "NATIVE_ACCOUNT_SCOPE")
    if reserve is not None:
        require(reserve.campaign_account == leaf["category"] and
                reserve.campaign_id == plan.campaign_id and reserve.agent_id == plan.agent_id,
                "NATIVE_ACCOUNT_SCOPE")
    if reserve is None or reserve.operation_id != plan.operation_id:
        # Once running, even a switch between two otherwise allowed categories
        # cannot change the identity of the job's original funded operation.
        operation = db.execute("SELECT account FROM operations WHERE id=?", (plan.operation_id,)).fetchone()
        records = db.execute("SELECT body FROM ledger WHERE campaign=? AND "
            "json_extract(body,'$.operation_id')=? AND json_extract(body,'$.posting')='reserve'",
            (plan.campaign_id, plan.operation_id)).fetchall()
        require(operation is not None and operation[0] == plan.account and len(records) == 1,
                "NATIVE_ACCOUNT_RESERVATION_REQUIRED")
        original = BudgetLedger.model_validate_json(records[0][0])
        require(original.campaign_account == leaf["category"] and original.agent_id == plan.agent_id,
                "NATIVE_ACCOUNT_SCOPE")
