"""Explicit cross-language integration: production Java store/HTTP, synthetic runtime only."""

import contextlib
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from mcbench.controls import Controls
from mcbench.native_settings import NativePatch, NativeSettingsClient, OutcomeUnknown
from mcbench.storage import Fault

ID = "fixture:key.mod.action:0"
ORIGINAL = "renderDistance:12\r\nkey_key.mod.action:key.keyboard.g\r\nkey_key.inventory:key.keyboard.e\r\ncustom:日本語\r\n"


@pytest.fixture
def jvm(tmp_path):
    classpath_file = os.environ.get("STRATA_SETTINGS_TEST_CLASSPATH")
    java = os.environ.get("STRATA_SETTINGS_TEST_JAVA")
    if not classpath_file or not java:
        pytest.skip("explicit pinned Java/classpath required for synthetic JVM integration")
    classpath = Path(classpath_file).read_text().strip()
    profile = tmp_path / "profile"
    private = tmp_path / "broker"
    profile.mkdir()
    private.mkdir()
    (profile / "options.txt").write_bytes(ORIGINAL.encode())
    launches = 0

    @contextlib.contextmanager
    def launch():
        nonlocal launches
        launches += 1
        connection = private / f"connection-{launches}.json"
        argfile = tmp_path / f"java-args-{launches}.txt"

        def quoted(value):
            return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'

        argfile.write_text("\n".join(map(quoted, ["-cp", classpath,
            "io.github.opencnid.strata.client.SettingsBridgeFixture", profile, private, connection])),
            encoding="utf-8")
        process = subprocess.Popen([java, "@" + str(argfile)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        client = None
        expires = time.monotonic() + 20
        try:
            while time.monotonic() < expires:
                if process.poll() is not None:
                    raise AssertionError("synthetic JVM exited: " + process.stderr.read().decode(errors="replace")[-2000:])
                if connection.exists():
                    try:
                        client = NativeSettingsClient.from_file(connection)
                        break
                    except ValueError:
                        pass  # Producer may still be writing this fresh connection file.
                time.sleep(0.02)
            assert client is not None, "live JVM did not publish connection within 20s"
            yield client, process, profile, private
        finally:
            if process.poll() is None:
                process.stdin.write(b"stop\n")
                process.stdin.flush()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()
            process.stderr.close()

    return launch


def change(snapshot):
    return NativePatch(transaction_id="native-tx-1", expected_revision=snapshot["revision"],
        expected_digest=snapshot["digest"], changes={ID: {"before": "key.keyboard.g", "after": "key.keyboard.f13"}})


def test_python_java_transaction_query_dedup_rollback_and_unsupported_gameplay(jvm, database):
    with jvm() as (client, process, profile, private):
        assert process.poll() is None
        initial = client.snapshot()
        assert initial["supported"] is False
        with pytest.raises(Fault, match="CAPABILITY_MISSING"):
            Controls(database, client).plan("avatar-1", "gameplay-tx", [ID])
        patch = change(initial)
        receipt = client.apply(patch)
        assert receipt["phase"] == "applied_pending_verification" and not receipt["committed"]
        assert client.status(patch.transaction_id) == receipt
        assert client.apply(patch) == receipt
        current = client.snapshot()
        assert current["bindings"][ID]["runtime_value"] == "key.keyboard.f13"
        assert current["bindings"][ID]["persisted_value"] == "key.keyboard.f13"
        journal = [json.loads(line)["payload"] for line in (private / "settings-journal.jsonl").read_text().splitlines()]
        assert sum(event["kind"] == "prepared" for event in journal) == 1
        assert client.rollback(patch.transaction_id)["phase"] == "rolled_back"
        assert (profile / "options.txt").read_bytes() == ORIGINAL.encode()
        assert client.snapshot()["bindings"][ID]["runtime_value"] == "key.keyboard.g"
        assert client.stop_all() == {"native_inputs_released": True}


def test_process_crash_new_session_and_pending_transaction_recovery(jvm):
    with jvm() as (client, process, profile, private):
        patch = change(client.snapshot())
        client.apply(patch)
        old_session = client.connection.session_id
        process.kill()  # Deliberate synthetic infrastructure fault, not a game process.
        process.wait(timeout=5)
    with jvm() as (client, process, profile, private):
        assert client.connection.session_id != old_session
        assert client.status(patch.transaction_id)["phase"] == "applied_pending_verification"
        assert client.apply(patch)["phase"] == "applied_pending_verification"
        assert client.rollback(patch.transaction_id)["phase"] == "rolled_back"
        assert (profile / "options.txt").read_bytes() == ORIGINAL.encode()


def test_concurrent_foreign_edit_remains_fenced_after_failed_recovery(jvm):
    with jvm() as (client, process, profile, private):
        patch = change(client.snapshot())
        client.apply(patch)
        foreign = (profile / "options.txt").read_bytes().replace(b"renderDistance:12", b"renderDistance:7")
        (profile / "options.txt").write_bytes(foreign)
        with pytest.raises(Fault, match="SETTINGS_ROLLBACK_CONFLICT"):
            client.rollback(patch.transaction_id)
        assert client.status(patch.transaction_id)["phase"] == "rollback_conflict"
        assert (profile / "options.txt").read_bytes() == foreign
        assert client.snapshot()["active_transaction"] == patch.transaction_id


def test_lost_post_response_is_queried_without_repeating_native_write(jvm, monkeypatch):
    with jvm() as (client, process, profile, private):
        patch = change(client.snapshot())
        exchange = client._exchange
        mutations = []

        def lose_response(method, path, body, timeout):
            result = exchange(method, path, body, timeout)
            if method == "POST" and json.loads(body)["operation"] == "apply":
                mutations.append(json.loads(body)["request_id"])
                raise TimeoutError("synthetic lost acknowledgement after actual HTTP acceptance")
            return result

        monkeypatch.setattr(client, "_exchange", lose_response)
        with pytest.raises(OutcomeUnknown):
            client.apply(patch)
        assert len(mutations) == 1
        expires = time.monotonic() + 5
        while True:
            try:
                status = client.status(patch.transaction_id)
                break
            except Fault as error:
                assert error.code == "SETTINGS_TRANSACTION_MISSING" and time.monotonic() < expires
        assert status["phase"] == "applied_pending_verification"
        assert len(mutations) == 1
        assert client.rollback(patch.transaction_id)["phase"] == "rolled_back"
        assert (profile / "options.txt").read_bytes() == ORIGINAL.encode()
