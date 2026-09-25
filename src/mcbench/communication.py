"""Declared team messages, durable per-sender order and bounded delivery."""

import json
import time
from datetime import datetime

from .storage import Database, Principal, canonical, digest, require


class Communication:
    def __init__(self, database: Database, clock=time.time, *, monotonic=time.monotonic):
        self.database, self.clock, self.monotonic = database, clock, monotonic
        with database.transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS messages (campaign TEXT, id TEXT, sender TEXT, "
                "seq INTEGER, body TEXT, created REAL, expires REAL, digest TEXT, "
                "PRIMARY KEY(campaign,id), UNIQUE(campaign,sender,seq))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS deliveries (campaign TEXT, message TEXT, "
                "recipient TEXT, acknowledged INTEGER DEFAULT 0, "
                "PRIMARY KEY(campaign,message,recipient))"
            )
            # Separate per-recipient cursors reveal no activity from private or
            # unrelated campaigns. Existing message bytes/sequences never change.
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            present = {"team_delivery_cursors", "team_cursor_format"} & tables
            require(
                not present or present == {"team_delivery_cursors", "team_cursor_format"},
                "TEAM_CURSOR_FORMAT",
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS team_delivery_cursors (campaign TEXT, recipient TEXT, "
                "message TEXT, cursor INTEGER NOT NULL CHECK(cursor>0), "
                "PRIMARY KEY(campaign,recipient,message), UNIQUE(campaign,recipient,cursor))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS team_cursor_format (singleton INTEGER PRIMARY KEY CHECK(singleton=1), "
                "policy TEXT NOT NULL, migration_event INTEGER NOT NULL REFERENCES outbox(cursor))"
            )
            missing = db.execute(
                "SELECT d.campaign,d.recipient,d.message FROM deliveries d "
                "JOIN messages m ON m.campaign=d.campaign AND m.id=d.message "
                "LEFT JOIN team_delivery_cursors c ON c.campaign=d.campaign AND c.recipient=d.recipient "
                "AND c.message=d.message WHERE c.message IS NULL "
                "ORDER BY m.created,m.sender,m.seq,d.campaign,d.recipient"
            ).fetchall()
            if not present:
                for row in missing:
                    self._cursor(db, row["campaign"], row["recipient"], row["message"])
                event = self.database.event(
                    db,
                    "team.cursor_migration",
                    {
                        "policy": "recipient-delivery-cursor/1",
                        "deliveries": len(missing),
                        "legacy_message_bytes_changed": False,
                    },
                )
                db.execute(
                    "INSERT INTO team_cursor_format VALUES(1,'recipient-delivery-cursor/1',?)",
                    (event,),
                )
            else:
                require(not missing, "TEAM_CURSOR_MISSING")
            format_rows = db.execute("SELECT * FROM team_cursor_format").fetchall()
            require(
                len(format_rows) == 1 and format_rows[0]["policy"] == "recipient-delivery-cursor/1",
                "TEAM_CURSOR_FORMAT",
            )
            migration = db.execute(
                "SELECT kind,body FROM outbox WHERE cursor=?", (format_rows[0]["migration_event"],)
            ).fetchone()
            require(
                migration is not None
                and migration["kind"] == "team.cursor_migration"
                and json.loads(migration["body"]).get("policy") == "recipient-delivery-cursor/1",
                "TEAM_CURSOR_FORMAT",
            )
            require(
                db.execute(
                    "SELECT 1 FROM team_delivery_cursors GROUP BY campaign,recipient "
                    "HAVING min(cursor)<>1 OR max(cursor)<>count(*) LIMIT 1"
                ).fetchone()
                is None,
                "TEAM_CURSOR_SEQUENCE",
            )
            require(
                db.execute(
                    "SELECT 1 FROM team_delivery_cursors c LEFT JOIN deliveries d ON "
                    "c.campaign=d.campaign AND c.recipient=d.recipient AND c.message=d.message WHERE d.message IS NULL LIMIT 1"
                ).fetchone()
                is None,
                "TEAM_CURSOR_ORPHAN",
            )
            require(
                db.execute(
                    "SELECT 1 FROM deliveries d LEFT JOIN messages m ON m.campaign=d.campaign AND m.id=d.message "
                    "WHERE m.id IS NULL LIMIT 1"
                ).fetchone()
                is None,
                "TEAM_DELIVERY_ORPHAN",
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS team_requests (campaign TEXT,agent TEXT,epoch INTEGER,request TEXT,"
                "fingerprint TEXT NOT NULL,PRIMARY KEY(campaign,agent,epoch,request))"
            )

    @staticmethod
    def _cursor(db, campaign, recipient, message):
        value = db.execute(
            "SELECT coalesce(max(cursor),0)+1 FROM team_delivery_cursors "
            "WHERE campaign=? AND recipient=?",
            (campaign, recipient),
        ).fetchone()[0]
        db.execute(
            "INSERT INTO team_delivery_cursors VALUES(?,?,?,?)",
            (campaign, recipient, message, value),
        )
        return value

    @staticmethod
    def roster(db, campaign, agent, principal):
        require(
            principal.role == "executor"
            and principal.namespace == f"campaign:{campaign}:agent:{agent}",
            "FORBIDDEN",
        )
        row = db.execute("SELECT config,state FROM campaigns WHERE id=?", (campaign,)).fetchone()
        require(row is not None and row["state"] == "RUNNING", "CAMPAIGN_NOT_RUNNING")
        agents = json.loads(row["config"])["agent_ids"]
        require(agent in agents, "FORBIDDEN")
        return agents

    def send(self, principal: Principal, campaign, agent, message_id, body, recipients, *, ttl=600):
        require(
            isinstance(body, str) and len(body.encode("utf-8")) <= 4096 and body, "MESSAGE_SIZE"
        )
        require(
            0 < ttl <= 600 and recipients and len(set(recipients)) == len(recipients),
            "MESSAGE_RECIPIENTS",
        )
        fingerprint = digest(
            {"sender": agent, "body": body, "recipients": sorted(recipients), "ttl": ttl}
        )
        with self.database.transaction() as db:
            return self._send(
                db, principal, campaign, agent, message_id, body, recipients, ttl, fingerprint
            )

    def _send(self, db, principal, campaign, agent, message_id, body, recipients, ttl, fingerprint):
        roster = self.roster(db, campaign, agent, principal)
        require(set(recipients) <= set(roster) - {agent}, "FORBIDDEN")
        old = db.execute(
            "SELECT * FROM messages WHERE campaign=? AND id=?", (campaign, message_id)
        ).fetchone()
        if old:
            require(old["digest"] == fingerprint, "IDEMPOTENCY_CONFLICT")
            return old["seq"]
        recent = db.execute(
            "SELECT COUNT(*) FROM messages WHERE campaign=? AND sender=? AND created>?",
            (campaign, agent, self.clock() - 60),
        ).fetchone()[0]
        require(recent < 10, "RATE_LIMITED")
        for recipient in recipients:
            queued = db.execute(
                "SELECT COUNT(*) FROM deliveries d JOIN messages m ON "
                "d.campaign=m.campaign AND d.message=m.id WHERE d.campaign=? AND recipient=? "
                "AND acknowledged=0 AND m.expires>?",
                (campaign, recipient, self.clock()),
            ).fetchone()[0]
            require(queued < 100, "QUEUE_FULL")
        seq = db.execute(
            "SELECT COALESCE(MAX(seq),0)+1 FROM messages WHERE campaign=? AND sender=?",
            (campaign, agent),
        ).fetchone()[0]
        created = self.clock()
        db.execute(
            "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)",
            (campaign, message_id, agent, seq, body, created, created + ttl, fingerprint),
        )
        db.executemany(
            "INSERT INTO deliveries(campaign,message,recipient) VALUES (?,?,?)",
            [(campaign, message_id, r) for r in recipients],
        )
        for recipient in recipients:
            self._cursor(db, campaign, recipient, message_id)
        # Byte cost is durable audit evidence; model/tool calls also retain their normal budget.
        self.database.event(
            db,
            "team.message",
            {
                "campaign": campaign,
                "sender": agent,
                "id": message_id,
                "seq": seq,
                "bytes": len(body.encode("utf-8")),
                "recipients": sorted(recipients),
            },
        )
        return seq

    def request(self, principal, value, cas, *, expected_policy_ref=None, authority_guard=None,
                native_call_event=None):
        """Trusted scoped facade; authentication is supplied by the native broker.

        Guards, ack/send effects, public receipt and private journal commit in a
        single writer transaction. This method exposes no model-chosen paths.
        """
        from .team_protocol import TeamPolicy, TeamRequest, TeamResponse, TeamSend

        value = TeamRequest.model_validate(value)
        started = self.monotonic()
        deadline = datetime.fromisoformat(value.deadline_at.replace("Z", "+00:00")).timestamp()
        budget = deadline - self.clock()
        require(0 < budget <= 5, "DEADLINE_EXCEEDED")
        with self.database.transaction() as db:
            if authority_guard is not None:
                authority_guard(db)
            roster = self.roster(db, value.campaign_id, value.agent_id, principal)
            row = db.execute("SELECT * FROM campaigns WHERE id=?", (value.campaign_id,)).fetchone()
            require(row["epoch"] == value.epoch, "STALE_EPOCH")
            now = self.clock()
            require(row["lease_until"] > now, "LEASE_EXPIRED")
            remaining = deadline - now
            require(0 < remaining <= 5, "DEADLINE_EXCEEDED")
            ref = json.loads(row["config"])["communication_policy"]
            require(expected_policy_ref is None or ref == expected_policy_ref, "TEAM_POLICY_CHANGED")
            visibility = db.execute(
                "SELECT visibility FROM objects WHERE namespace='operator' AND ref=?", (ref,)
            ).fetchone()
            require(visibility is not None and visibility[0] == "operator", "TEAM_POLICY_PRIVATE")
            policy = TeamPolicy.model_validate(
                cas.json(Principal("operator", "operator"), "operator", ref)
            )
            mode = db.execute("SELECT simulation FROM controller_profile").fetchone()
            require(mode is not None and policy.is_example is bool(mode[0]), "TEAM_POLICY_SCOPE")
            require(policy.mode == "campaign_roster", "TEAM_COMMUNICATION_DISABLED")
            operation = value.operation
            fingerprint = digest(operation.model_dump())
            identity = (value.campaign_id, value.agent_id, value.epoch, value.request_id)
            prior = db.execute(
                "SELECT fingerprint FROM team_requests WHERE campaign=? AND agent=? AND epoch=? AND request=?",
                identity,
            ).fetchone()
            require(prior is None or prior[0] == fingerprint, "IDEMPOTENCY_CONFLICT")
            if prior is None:
                db.execute("INSERT INTO team_requests VALUES(?,?,?,?,?)", (*identity, fingerprint))
            if isinstance(operation, TeamSend):
                require(set(operation.recipients) <= set(roster) - {value.agent_id}, "FORBIDDEN")
                fingerprint = digest(
                    {
                        "sender": value.agent_id,
                        "body": operation.body,
                        "recipients": sorted(operation.recipients),
                        "ttl": operation.ttl_s,
                    }
                )
                seq = self._send(
                    db,
                    principal,
                    value.campaign_id,
                    value.agent_id,
                    operation.message_id,
                    operation.body,
                    operation.recipients,
                    operation.ttl_s,
                    fingerprint,
                )
                message = db.execute(
                    "SELECT expires FROM messages WHERE campaign=? AND id=?",
                    (value.campaign_id, operation.message_id),
                ).fetchone()
                result = {
                    "kind": "sent",
                    "message_id": operation.message_id,
                    "sender_seq": seq,
                    "expires_unix_ms": int(message[0] * 1000),
                }
            else:
                # Foreign acknowledgements cannot silently masquerade as a
                # successful operation, and no ack takes effect on partial failure.
                for message in operation.acknowledge:
                    require(
                        db.execute(
                            "SELECT 1 FROM deliveries WHERE campaign=? AND recipient=? AND message=?",
                            (value.campaign_id, value.agent_id, message),
                        ).fetchone()
                        is not None,
                        "FORBIDDEN",
                    )
                for message in operation.acknowledge:
                    db.execute(
                        "UPDATE deliveries SET acknowledged=1 WHERE campaign=? AND recipient=? AND message=?",
                        (value.campaign_id, value.agent_id, message),
                    )
                messages = [
                    dict(r)
                    for r in db.execute(
                        "SELECT m.id,m.sender,m.seq sender_seq,m.body,"
                        "CAST(m.expires*1000 AS INTEGER) expires_unix_ms,c.cursor FROM deliveries d "
                        "JOIN messages m ON m.campaign=d.campaign AND m.id=d.message "
                        "JOIN team_delivery_cursors c ON c.campaign=d.campaign AND c.recipient=d.recipient AND c.message=d.message "
                        "WHERE d.campaign=? AND d.recipient=? AND d.acknowledged=0 AND m.expires>? AND c.cursor>? "
                        "ORDER BY c.cursor LIMIT ?",
                        (
                            value.campaign_id,
                            value.agent_id,
                            now,
                            operation.after,
                            operation.limit + 1,
                        ),
                    )
                ]
                more = len(messages) > operation.limit
                messages = messages[: operation.limit]
                result = {
                    "kind": "received",
                    "messages": messages,
                    "has_more": more,
                    "next_cursor": messages[-1]["cursor"] if messages else operation.after,
                }
            result = {
                "schema": "strata/TeamResponse/1",
                "request_id": value.request_id,
                "result": result,
            }
            result = TeamResponse.model_validate(result).model_dump()
            self.database.event(
                db,
                "team.request",
                {"policy_ref": ref, "request": value.model_dump(), "result_digest": digest(result),
                 **({"native_call_event": native_call_event, "result": result}
                    if native_call_event is not None else {})},
            )
            require(len(canonical(result)) <= 512 * 1024, "TEAM_RESPONSE_LIMIT")
            require(
                self.monotonic() - started < budget and self.clock() < deadline, "DEADLINE_EXCEEDED"
            )
            require(row["lease_until"] > self.clock(), "LEASE_EXPIRED")
            if authority_guard is not None:
                authority_guard(db)
            return result

    def receive(self, principal, campaign, agent, *, acknowledge=()):
        with self.database.transaction() as db:
            self.roster(db, campaign, agent, principal)
            for message in acknowledge:
                db.execute(
                    "UPDATE deliveries SET acknowledged=1 WHERE campaign=? AND message=? "
                    "AND recipient=?",
                    (campaign, message, agent),
                )
            return [
                dict(row)
                for row in db.execute(
                    "SELECT m.id,m.sender,m.seq,m.body,m.expires "
                    "FROM deliveries d JOIN messages m ON d.campaign=m.campaign AND d.message=m.id "
                    "WHERE d.campaign=? AND d.recipient=? AND acknowledged=0 AND m.expires>? "
                    "ORDER BY m.created,m.sender,m.seq LIMIT 100",
                    (campaign, agent, self.clock()),
                )
            ]
