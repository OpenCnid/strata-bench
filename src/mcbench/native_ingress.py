"""Job-scoped native HTTP authentication, separate from upstream OAuth.

Native transport adds the header outside model arguments. The header is a
private capability, not proof against arbitrary same-user code. Its secrecy
depends on the qualified native tool/bootstrap boundary. Never journal it.
"""

import hashlib
import hmac
import re
import secrets
import time
from urllib.parse import urlsplit

from .native import NativeLaunch
from .storage import canonical, digest, require

POLICY = "native-job-http-header/1"
HEADER = "X-Strata-Ingress"


def credential():
    return secrets.token_urlsafe(32)


def credential_digest(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{43}", value), "INGRESS_CREDENTIAL")
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def provider_binding(plan):
    require(plan.ingress_policy == POLICY, "INGRESS_PROFILE")
    config = plan.config_overrides
    provider = config.get("model_provider")
    require(isinstance(provider, str) and re.fullmatch(r"[a-z0-9_]{1,64}", provider), "INGRESS_PROFILE")
    prefix = "model_providers." + provider + "."
    allowed = {"name", "base_url", "wire_api", "requires_openai_auth", "http_headers",
               "supports_websockets", "request_max_retries", "stream_max_retries",
               "stream_idle_timeout_ms"}
    require("model_providers" not in config and "model_providers." + provider not in config and
            all(key[len(prefix):] in allowed for key in config if key.startswith(prefix)),
            "INGRESS_PROFILE")
    headers = config.get(prefix + "http_headers")
    require(isinstance(headers, dict) and set(headers) == {HEADER}, "INGRESS_PROFILE")
    sha = credential_digest(headers[HEADER])
    value = config.get(prefix + "base_url")
    require(isinstance(value, str) and re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}/v1", value),
            "INGRESS_ENDPOINT")
    url = urlsplit(value)
    port = int(url.netloc.rsplit(":", 1)[1])
    require(1 <= port <= 65535, "INGRESS_ENDPOINT")
    require(url.scheme == "http" and url.hostname == "127.0.0.1" and url.port is not None and
            url.username is None and url.password is None and not url.query and not url.fragment and
            url.path == "/v1" and config.get(prefix + "wire_api") == "responses" and
            config.get(prefix + "supports_websockets") is False, "INGRESS_ENDPOINT")
    # Unsupported authentication commands/environment expansion cannot silently
    # supply another bearer or expose upstream credentials in this profile.
    require(not any(prefix + key in config for key in (
        "auth", "env_key", "experimental_bearer_token", "env_http_headers", "query_params")),
        "INGRESS_PROFILE")
    native_oauth = config.get(prefix + "requires_openai_auth")
    require(type(native_oauth) is bool, "INGRESS_PROFILE")
    return {"job": plan.job_id, "profile": plan.profile_digest(), "credential_digest": sha,
            "authority": f"127.0.0.1:{url.port}", "native_oauth": native_oauth}


class NativeIngress:
    def __init__(self, database, *, clock=time.time):
        self.db, self.clock = database, clock
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_ingress (job TEXT PRIMARY KEY, "
                       "body TEXT, fingerprint TEXT, revoked INTEGER)")
            db.execute("CREATE TABLE IF NOT EXISTS native_ingress_requests (operation TEXT PRIMARY KEY, "
                       "job TEXT, profile TEXT, request_digest TEXT, authority_digest TEXT)")

    def register(self, plan):
        body = provider_binding(plan)
        with self.db.transaction() as db:
            old = db.execute("SELECT fingerprint FROM native_ingress WHERE job=?", (plan.job_id,)).fetchone()
            require(old is None or old[0] == digest(body), "IDEMPOTENCY_CONFLICT")
            if old is None:
                db.execute("INSERT INTO native_ingress VALUES(?,?,?,0)", (
                    plan.job_id, canonical(body).decode(), digest(body)))
                self.db.event(db, "native.ingress_registered", body)

    def authenticate(self, job, headers, path):
        require(path in {"/v1/responses", "/v1/responses/compact"}, "INGRESS_ROUTE")
        plan, binding = active_binding(self.db.connection, job, now=self.clock())
        # get_all preserves duplicate fields; Header.get alone is insufficient.
        values = headers.get_all(HEADER, [])
        hosts = headers.get_all("Host", [])
        require(len(values) == 1 and len(hosts) == 1 and hosts[0] == binding["authority"], "INGRESS_DENIED")
        require(isinstance(values[0], str) and re.fullmatch(r"[A-Za-z0-9_-]{43}", values[0]), "INGRESS_DENIED")
        require(hmac.compare_digest(hashlib.sha256(values[0].encode("ascii")).hexdigest(),
                                    binding["credential_digest"]), "INGRESS_DENIED")
        auth = headers.get_all("Authorization", [])
        require(len(auth) <= 1 and (binding["native_oauth"] or not auth), "INGRESS_AUTH_MODE")
        if binding["native_oauth"]:
            require(len(auth) == 1 and auth[0].startswith("Bearer ") and
                    7 < len(auth[0]) <= 16384 and not any(c.isspace() for c in auth[0][7:]),
                    "INGRESS_AUTH_MODE")
        require(not headers.get_all("Proxy-Authorization", []) and
                not headers.get_all("Cookie", []), "INGRESS_AUTH_MODE")
        return plan.profile_digest()

    def bind_request(self, job, operation, request_digest, headers, path):
        require(isinstance(request_digest, str) and re.fullmatch(r"[a-f0-9]{64}", request_digest),
                "REQUEST_DIGEST_MISMATCH")
        with self.db.transaction() as db:
            profile = self.authenticate(job, headers, path)
            _, binding = active_binding(db, job, now=self.clock())
            values = (operation, job, profile, request_digest, digest(binding))
            old = db.execute("SELECT * FROM native_ingress_requests WHERE operation=?", (operation,)).fetchone()
            require(old is None or tuple(old) == values, "IDEMPOTENCY_CONFLICT")
            db.execute("INSERT OR IGNORE INTO native_ingress_requests VALUES(?,?,?,?,?)", values)
            if old is None:
                self.db.event(db, "native.ingress_authenticated", {"operation": operation,
                    "job": job, "profile": profile, "request_digest": request_digest,
                    "authority_digest": digest(binding)})

    def revoke(self, job):
        with self.db.transaction() as db:
            db.execute("UPDATE native_ingress SET revoked=1 WHERE job=?", (job,))
            self.db.event(db, "native.ingress_revoked", {"job": job})


def active_binding(db, job, *, now):
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='native_ingress'").fetchone(),
            "INGRESS_NOT_REGISTERED")
    row = db.execute("SELECT i.body,i.revoked,j.plan,j.state,j.started FROM native_ingress i "
                     "JOIN native_jobs j ON i.job=j.id WHERE i.job=?", (job,)).fetchone()
    require(row is not None and not row["revoked"] and row["state"] == "RUNNING", "INGRESS_REVOKED")
    plan = NativeLaunch.model_validate_json(row["plan"])
    require(row["started"] + plan.hard_timeout_s > now, "INGRESS_EXPIRED")
    binding = provider_binding(plan)
    require(canonical(binding).decode() == row["body"], "INGRESS_PROFILE_CHANGED")
    return plan, binding


def require_ingress_request(db, plan, operation, request_digest):
    _, binding = active_binding(db, plan.job_id, now=time.time())
    _request_bound(db, plan, operation, request_digest, binding)


def require_ingress_capture(db, plan, operation, request_digest):
    """Historical source authentication only; never admits or revives a job."""
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='native_ingress'").fetchone(),
            "INGRESS_NOT_REGISTERED")
    binding = provider_binding(plan)
    row = db.execute("SELECT body FROM native_ingress WHERE job=?", (plan.job_id,)).fetchone()
    require(row is not None and row[0] == canonical(binding).decode(), "INGRESS_PROFILE_CHANGED")
    _request_bound(db, plan, operation, request_digest, binding)


def _request_bound(db, plan, operation, request_digest, binding):
    row = db.execute("SELECT * FROM native_ingress_requests WHERE operation=?", (operation,)).fetchone()
    require(row is not None and row["job"] == plan.job_id and row["profile"] == plan.profile_digest()
            and row["request_digest"] == request_digest and row["authority_digest"] == digest(binding),
            "INGRESS_REQUEST_NOT_AUTHENTICATED")
