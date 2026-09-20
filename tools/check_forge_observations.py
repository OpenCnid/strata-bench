"""Explicit operator-only, read-only checks against a running authentic client.

Does not launch/join, arm an action lane, dispatch inference or qualify a campaign.
Connection credentials are never included in the private result bundle.
"""

import argparse
import hashlib
import http.client
import json
import time
from pathlib import Path
from uuid import uuid4

from mcbench.native_game import NativeGameClient
from mcbench.storage import Fault, canonical, reject_links, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--phase", choices=("disconnected", "world", "transport"), required=True)
    args = parser.parse_args()
    root = args.evidence
    require(root.is_absolute(), "UNSAFE_PATH")
    reject_links(root)
    require(not root.is_relative_to(Path(__file__).resolve().parents[1]), "FORBIDDEN")
    root.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (root / "checker-source.py").write_bytes(source)
    client = NativeGameClient.from_file(args.connection)
    report = {
        "schema": "strata/NativeObservationCheck/1",
        "phase": args.phase,
        "started_unix_ms": time.time_ns() // 1_000_000,
        "native_fingerprint": client.connection.fingerprint,
        "checker_sha256": hashlib.sha256(source).hexdigest(),
        "campaign_admission": False,
        "gate_result": "not_run",
        "inference_dispatched": False,
        "mutations_dispatched": False,
        "checks": [],
        "calls": [],
    }

    def check(name, condition):
        report["checks"].append({"name": name, "pass": bool(condition)})
        require(condition, "CONFORMANCE_ASSERTION_FAILED")

    def call(operation, arguments, expected_error=None):
        started = time.monotonic_ns()
        record = {"operation": operation, "arguments": arguments}
        report["calls"].append(record)
        try:
            result = client.call(operation, arguments)
            record["result"] = result
        except Fault as error:
            record["error_code"] = error.code
            if expected_error is None:
                raise
            check(f"{operation}:{expected_error}", error.code == expected_error)
            return None
        finally:
            record["round_trip_ms"] = (time.monotonic_ns() - started) / 1_000_000
        check(f"{operation}:success_expected", expected_error is None)
        return result

    def snapshot_bounds(snapshot):
        state = snapshot["state"]
        check("native_snapshot_below_64KiB", len(canonical(snapshot)) <= 65536)
        check("spatial_page_bounds", len(state["nearby_blocks"]) <= 128
              and len(state["nearby_entities"]) <= 128)
        check("no_active_action", state["active_request_id"] is None)
        check("connected", state["connected"])
        check("inventory_46_slots", len(state["inventory"]) == 46)

    def transport():
        connection = client.connection
        cases = [
            ("missing_auth", 401, "SETTINGS_UNAUTHORIZED"),
            ("wrong_auth", 401, "SETTINGS_UNAUTHORIZED"),
            ("browser_origin", 403, "SETTINGS_FORBIDDEN"),
            ("foreign_host", 403, "SETTINGS_FORBIDDEN"),
            ("wrong_session", 400, "GAME_SESSION_MISMATCH"),
            ("expired_deadline", 400, "GAME_DEADLINE_INVALID"),
            ("wrong_schema", 400, "SCHEMA_UNSUPPORTED"),
        ]
        for name, expected_status, expected_code in cases:
            payload = {"schema": "strata/NativeGameRequest/1", "request_id": str(uuid4()),
                       "session_id": connection.session_id,
                       "deadline_unix_ms": time.time_ns() // 1_000_000 + 5000,
                       "operation": "capabilities", "args": {}}
            headers = {"Content-Type": "application/json",
                       "Authorization": "Bearer " + connection.bearer_token.get_secret_value()}
            if name == "missing_auth":
                del headers["Authorization"]
            elif name == "wrong_auth":
                headers["Authorization"] = "Bearer " + "0" * 64
            elif name == "browser_origin":
                headers["Origin"] = "https://example.invalid"
            elif name == "foreign_host":
                headers["Host"] = "example.invalid"
            elif name == "wrong_session":
                payload["session_id"] = str(uuid4())
            elif name == "expired_deadline":
                payload["deadline_unix_ms"] = time.time_ns() // 1_000_000 - 1000
            elif name == "wrong_schema":
                payload["schema"] = "strata/NativeSettingsRequest/1"
            started = time.monotonic_ns()
            channel = http.client.HTTPConnection(connection.host, connection.port, timeout=5)
            try:
                channel.request("POST", "/v1/game", body=canonical(payload), headers=headers)
                response = channel.getresponse()
                raw = response.read(65537)
                require(len(raw) <= 65536, "RESPONSE_TOO_LARGE")
                value = json.loads(raw)
                record = {"case": name, "http_status": response.status,
                          "error_code": value.get("error_code"),
                          "round_trip_ms": (time.monotonic_ns() - started) / 1_000_000}
                report["calls"].append(record)
                check(name, response.status == expected_status
                      and value.get("error_code") == expected_code)
            finally:
                channel.close()

    def world():
        bound = call("observe_bound", {"cursor": None})
        identity = call("identity", {})
        check("atomic_body_identity", identity["body_fingerprint"] == bound["body_fingerprint"]
              and identity["connection_generation"] == bound["connection_generation"])
        first = bound["snapshot"]
        page = first
        page_ids, block_positions, entity_ids = set(), set(), set()
        core_fields = set(first["state"]) - {
            "nearby_blocks", "nearby_entities", "truncated", "next_cursor"}
        while True:
            snapshot_bounds(page)
            check("page_identity_unique", page["snapshot_id"] not in page_ids)
            page_ids.add(page["snapshot_id"])
            check("scene_page_ceiling", len(page_ids) <= 128)
            check("frozen_scene_identity", all(page[key] == first[key] for key in (
                "state_revision", "source_clock_id", "captured_elapsed_ms")))
            check("frozen_scene_core", all(page["state"][key] == first["state"][key]
                  for key in core_fields))
            check("page_age_not_refreshed", page["age_ms"] >= first["age_ms"])
            for block in page["state"]["nearby_blocks"]:
                position = canonical(block["position"])
                check("unique_observed_block", position not in block_positions)
                block_positions.add(position)
            for entity in page["state"]["nearby_entities"]:
                check("unique_observed_entity", entity["id"] not in entity_ids)
                entity_ids.add(entity["id"])
            cursor = page["state"]["next_cursor"]
            if cursor is None:
                break
            check("cursor_not_repeated", cursor not in page_ids)
            page = call("observe", {"cursor": cursor})
        repeated = call("observe", {"cursor": first["snapshot_id"]})
        check("repeat_frozen_snapshot", all(repeated[key] == first[key]
              for key in first if key != "age_ms"))
        check("repeat_age_advances", repeated["age_ms"] >= first["age_ms"])
        call("observe", {"cursor": str(uuid4())}, "STALE_OBSERVATION")
        report["scene"] = {"pages": len(page_ids), "blocks": len(block_positions),
                           "entities": len(entity_ids)}
        # A fresh capture is distinct from reading a frozen page. State may change
        # naturally; this check does not require an idle world or equal revisions.
        fresh = call("observe_bound", {"cursor": None})
        snapshot_bounds(fresh["snapshot"])
        check("fresh_same_body_generation", all(fresh[key] == bound[key]
              for key in ("body_fingerprint", "connection_generation")))
        check("fresh_snapshot_identity", fresh["snapshot"]["snapshot_id"]
              != first["snapshot_id"])

    try:
        capabilities = call("capabilities", {})
        check("read_only_authority", capabilities["actions"] == [])
        call("lane_status", {}, "CAPABILITY_MISSING")
        if args.phase == "disconnected":
            call("identity", {}, "GAME_NOT_CONNECTED")
            call("observe", {"cursor": None}, "GAME_NOT_CONNECTED")
            call("observe_bound", {"cursor": None}, "GAME_NOT_CONNECTED")
        elif args.phase == "world":
            world()
        else:
            transport()
        report["result"] = "pass"
    except (OSError, ValueError) as error:
        report["result"] = "fail"
        report["error_code"] = error.code if isinstance(error, Fault) else "CHECK_FAILED"
    finally:
        report["finished_unix_ms"] = time.time_ns() // 1_000_000
        (root / "result.json").write_bytes(canonical(report) + b"\n")
        print(json.dumps({"result": report.get("result", "fail"), "phase": args.phase,
                          "checks": len(report["checks"]),
                          "error_code": report.get("error_code"),
                          "gate_result": "not_run"}))
    return 0 if report.get("result") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
