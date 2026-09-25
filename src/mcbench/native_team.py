"""Private binding for the optional native campaign-team capability."""

import json
import time

from .native_broker_policy import TEAM_POLICY
from .storage import Principal, digest, require
from .team_protocol import TeamPolicy, TeamRequest, TeamResponse, TeamSend


def require_team_plan(db, cas, plan, *, now=None):
    """Read-only preflight/admission check, never a grant or policy creation."""
    require(plan.broker_policy == TEAM_POLICY and plan.team_policy_ref is not None,
            "TEAM_PROFILE_REQUIRED")
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    require({"campaigns", "controller_profile", "native_profile"} <= tables,
            "TEAM_CONTROLLER_REQUIRED")
    row = db.execute("SELECT * FROM campaigns WHERE id=?", (plan.campaign_id,)).fetchone()
    require(row is not None and row["state"] == "RUNNING", "CAMPAIGN_NOT_RUNNING")
    config = json.loads(row["config"])
    require(plan.agent_id in config["agent_ids"] and row["epoch"] == plan.epoch,
            "TEAM_CAMPAIGN_SCOPE")
    require(row["lease_until"] > (time.time() if now is None else now), "LEASE_EXPIRED")
    require(config["communication_policy"] == plan.team_policy_ref, "TEAM_POLICY_CHANGED")
    visibility = db.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?",
                            (plan.team_policy_ref,)).fetchone()
    require(visibility is not None and visibility[0] == "operator", "TEAM_POLICY_PRIVATE")
    policy = TeamPolicy.model_validate(cas.json(Principal("operator", "operator"),
                                               "operator", plan.team_policy_ref))
    controller = db.execute("SELECT simulation FROM controller_profile").fetchone()
    native = db.execute("SELECT simulation FROM native_profile").fetchone()
    require(controller is not None and native is not None and controller[0] == native[0]
            and policy.is_example is bool(controller[0]), "TEAM_POLICY_SCOPE")
    require(policy.mode == "campaign_roster", "TEAM_COMMUNICATION_DISABLED")
    return policy


def inspect_team_calls(db, plan, calls):
    """Read-only stopped evidence join; never migrates or repairs missing data.

    The immutable receipt is bound into the private export. Mutable queue/ack
    state is validated only as delivery identity, not copied into an old export
    or restored as a campaign checkpoint.
    """
    require(plan.broker_policy == TEAM_POLICY and plan.team_policy_ref is not None,
            "TEAM_PROFILE_REQUIRED")
    receipts = []
    for call in calls:
        source = json.loads(call["body"])
        if source["tool"] != "team":
            continue
        arguments = source.get("team_arguments")
        require(isinstance(arguments, dict) and set(arguments) == {"request"}
                and digest(arguments) == source["arguments_digest"], "TEAM_CALL_EVIDENCE")
        request = TeamRequest.model_validate(arguments["request"])
        rows = db.execute("SELECT cursor,body FROM outbox WHERE kind='team.request' "
            "AND json_extract(body,'$.native_call_event')=? ORDER BY cursor", (call["cursor"],)).fetchall()
        require(len(rows) <= 1 and (call["state"] != "RETURNED" or len(rows) == 1),
                "TEAM_RECEIPT_MISSING")
        if not rows:
            continue  # An authenticated rejected helper/scope request has no effects.
        record = dict(rows[0])
        body = json.loads(record["body"])
        grant_row = db.execute("SELECT body FROM broker_grants WHERE runtime=? AND thread=?",
                               (plan.job_id, source["thread"])).fetchone()
        require(grant_row is not None, "TEAM_CALL_EVIDENCE")
        from .broker import BrokerGrant
        grant = BrokerGrant.model_validate_json(grant_row[0])
        require(grant.role == "executor" and (request.campaign_id, request.agent_id, request.epoch)
                == (plan.campaign_id, plan.agent_id, plan.epoch)
                and body.get("policy_ref") == plan.team_policy_ref
                and body.get("request") == request.model_dump()
                and record["cursor"] > call["cursor"], "TEAM_CALL_EVIDENCE")
        response = TeamResponse.model_validate(body.get("result"))
        require(response.request_id == request.request_id
                and digest(response.model_dump()) == body.get("result_digest")
                and (call["state"] != "RETURNED" or call["result_digest"] == body["result_digest"]),
                "TEAM_RECEIPT_MISMATCH")
        operation = request.operation
        journal = db.execute("SELECT fingerprint FROM team_requests WHERE campaign=? AND agent=? AND epoch=? AND request=?",
            (plan.campaign_id, plan.agent_id, plan.epoch, request.request_id)).fetchone()
        require(journal is not None and journal[0] == digest(operation.model_dump()), "TEAM_REQUEST_MISSING")
        if isinstance(operation, TeamSend):
            require(response.result.kind == "sent", "TEAM_RECEIPT_MISMATCH")
            message = db.execute("SELECT * FROM messages WHERE campaign=? AND id=?",
                                  (plan.campaign_id, operation.message_id)).fetchone()
            require(message is not None, "TEAM_MESSAGE_MISSING")
            recipients = sorted(r[0] for r in db.execute("SELECT recipient FROM deliveries WHERE campaign=? AND message=?",
                (plan.campaign_id, operation.message_id)))
            require(message["sender"] == plan.agent_id and message["body"] == operation.body
                    and recipients == sorted(operation.recipients)
                    and message["digest"] == digest({"sender": plan.agent_id, "body": operation.body,
                        "recipients": recipients, "ttl": operation.ttl_s})
                    and message["expires"] == message["created"] + operation.ttl_s
                    and response.result.message_id == operation.message_id
                    and response.result.sender_seq == message["seq"]
                    and response.result.expires_unix_ms == int(message["expires"] * 1000),
                    "TEAM_MESSAGE_MISMATCH")
        else:
            require(response.result.kind == "received", "TEAM_RECEIPT_MISMATCH")
            require(len(response.result.messages) <= operation.limit, "TEAM_RECEIPT_MISMATCH")
            cursors = [m.cursor for m in response.result.messages]
            require(cursors == sorted(set(cursors)) and all(c > operation.after for c in cursors)
                    and response.result.next_cursor == (cursors[-1] if cursors else operation.after),
                    "TEAM_RECEIPT_MISMATCH")
            for item in response.result.messages:
                message = db.execute("SELECT m.id,m.sender,m.seq sender_seq,m.body,"
                    "CAST(m.expires*1000 AS INTEGER) expires_unix_ms,c.cursor FROM messages m "
                    "JOIN deliveries d ON d.campaign=m.campaign AND d.message=m.id "
                    "JOIN team_delivery_cursors c ON c.campaign=d.campaign AND c.message=d.message AND c.recipient=d.recipient "
                    "WHERE m.campaign=? AND m.id=? AND d.recipient=?",
                    (plan.campaign_id, item.id, plan.agent_id)).fetchone()
                require(message is not None and dict(message) == item.model_dump(), "TEAM_MESSAGE_MISMATCH")
            for message in operation.acknowledge:
                require(db.execute("SELECT 1 FROM deliveries WHERE campaign=? AND message=? AND recipient=? AND acknowledged=1",
                    (plan.campaign_id, message, plan.agent_id)).fetchone() is not None, "TEAM_ACK_MISSING")
        receipts.append(record)
    return receipts
