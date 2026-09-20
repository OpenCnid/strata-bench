"""Declared team messages, durable per-sender order and bounded delivery."""

import json
import time

from .storage import Database, Principal, digest, require


class Communication:
    def __init__(self, database: Database, clock=time.time):
        self.database, self.clock = database, clock
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS messages (campaign TEXT, id TEXT, sender TEXT, "
                       "seq INTEGER, body TEXT, created REAL, expires REAL, digest TEXT, "
                       "PRIMARY KEY(campaign,id), UNIQUE(campaign,sender,seq))")
            db.execute("CREATE TABLE IF NOT EXISTS deliveries (campaign TEXT, message TEXT, "
                       "recipient TEXT, acknowledged INTEGER DEFAULT 0, "
                       "PRIMARY KEY(campaign,message,recipient))")

    @staticmethod
    def roster(db, campaign, agent, principal):
        require(principal.role == "executor" and
                principal.namespace == f"campaign:{campaign}:agent:{agent}", "FORBIDDEN")
        row = db.execute("SELECT config,state FROM campaigns WHERE id=?", (campaign,)).fetchone()
        require(row is not None and row["state"] == "RUNNING", "CAMPAIGN_NOT_RUNNING")
        agents = json.loads(row["config"])["agent_ids"]
        require(agent in agents, "FORBIDDEN")
        return agents

    def send(self, principal: Principal, campaign, agent, message_id, body, recipients, *, ttl=600):
        require(isinstance(body, str) and len(body.encode("utf-8")) <= 4096 and body,
                "MESSAGE_SIZE")
        require(0 < ttl <= 600 and recipients and len(set(recipients)) == len(recipients),
                "MESSAGE_RECIPIENTS")
        fingerprint = digest({"sender": agent, "body": body, "recipients": sorted(recipients),
                              "ttl": ttl})
        with self.database.transaction() as db:
            roster = self.roster(db, campaign, agent, principal)
            require(set(recipients) <= set(roster) - {agent}, "FORBIDDEN")
            old = db.execute("SELECT * FROM messages WHERE campaign=? AND id=?",
                             (campaign, message_id)).fetchone()
            if old:
                require(old["digest"] == fingerprint, "IDEMPOTENCY_CONFLICT")
                return old["seq"]
            recent = db.execute("SELECT COUNT(*) FROM messages WHERE campaign=? AND sender=? "
                                "AND created>?", (campaign, agent, self.clock() - 60)).fetchone()[0]
            require(recent < 10, "RATE_LIMITED")
            for recipient in recipients:
                queued = db.execute("SELECT COUNT(*) FROM deliveries d JOIN messages m ON "
                    "d.campaign=m.campaign AND d.message=m.id WHERE d.campaign=? AND recipient=? "
                    "AND acknowledged=0 AND m.expires>?", (campaign, recipient, self.clock())).fetchone()[0]
                require(queued < 100, "QUEUE_FULL")
            seq = db.execute("SELECT COALESCE(MAX(seq),0)+1 FROM messages WHERE campaign=? AND sender=?",
                             (campaign, agent)).fetchone()[0]
            db.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)", (campaign, message_id, agent,
                       seq, body, self.clock(), self.clock() + ttl, fingerprint))
            db.executemany("INSERT INTO deliveries(campaign,message,recipient) VALUES (?,?,?)",
                           [(campaign, message_id, r) for r in recipients])
            # Byte cost is durable audit evidence; model/tool calls also retain their normal budget.
            self.database.event(db, "team.message", {"campaign": campaign, "sender": agent,
                "id": message_id, "seq": seq, "bytes": len(body.encode("utf-8")),
                "recipients": sorted(recipients)})
            return seq

    def receive(self, principal, campaign, agent, *, acknowledge=()):
        with self.database.transaction() as db:
            self.roster(db, campaign, agent, principal)
            for message in acknowledge:
                db.execute("UPDATE deliveries SET acknowledged=1 WHERE campaign=? AND message=? "
                           "AND recipient=?", (campaign, message, agent))
            return [dict(row) for row in db.execute("SELECT m.id,m.sender,m.seq,m.body,m.expires "
                "FROM deliveries d JOIN messages m ON d.campaign=m.campaign AND d.message=m.id "
                "WHERE d.campaign=? AND d.recipient=? AND acknowledged=0 AND m.expires>? "
                "ORDER BY m.created,m.sender,m.seq LIMIT 100", (campaign, agent, self.clock()))]
