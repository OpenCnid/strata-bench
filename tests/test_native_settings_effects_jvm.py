"""Python through production Java coordinator/store/lane/HTTP; synthetic body and input only."""

import contextlib
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.native_settings_effects import EffectOutcomeUnknown, EffectRequest, NativeSettingsEffectsClient

ID = "fixture:key.mod.action:0"
ORIGINAL = "renderDistance:12\r\nkey_key.mod.action:key.keyboard.g\r\nkey_key.inventory:key.keyboard.e\r\n"


@pytest.fixture
def effects_jvm(tmp_path):
    java = os.environ.get("STRATA_CLIENT_TEST_JAVA")
    classpath_path = os.environ.get("STRATA_CLIENT_TEST_CLASSPATH")
    if not java or not classpath_path:
        pytest.skip("explicit pinned Java/classpath required for synthetic settings-effects integration")
    classpath = Path(classpath_path).read_text(encoding="utf-8").strip()
    profile, settings_root, game_root = (tmp_path / name for name in ("profile", "settings", "game"))
    for path in (profile, settings_root, game_root):
        path.mkdir()
    (profile / "options.txt").write_bytes(ORIGINAL.encode())
    authority = {"schema": "strata/NativeGameAuthority/1", "campaign_id": "campaign", "agent_id": "avatar",
        "capability_digest": "c" * 64, "body_fingerprint": "b" * 64,
        "expires_unix_ms": int(time.time() * 1000) + 120000, "primitive_limit": 1000}
    (game_root / "game-authority.json").write_text(json.dumps(authority), encoding="utf-8")
    launches = 0

    @contextlib.contextmanager
    def launch(*, repair_owner=False, commit_owner=False, restart_owner=False, capability_digest=None, scope=None, options_text=None):
        nonlocal launches
        launches += 1
        if capability_digest is not None or scope is not None or options_text is not None:
            assert launches == 1, "changing authority on a used fixture is forbidden"
            override = {"capability_digest": capability_digest} if capability_digest is not None else {}
            if scope is not None:
                override |= {"campaign_id": scope[0], "agent_id": scope[1]}
            (game_root / "game-authority.json").write_text(json.dumps(authority | override), encoding="utf-8")
            if options_text is not None:
                (profile / "options.txt").write_bytes(options_text.encode())
        descriptor = tmp_path / f"connection-{launches}.json"
        argfile = tmp_path / f"args-{launches}.txt"
        args = ["-cp", classpath, "io.github.opencnid.strata.client.SettingsEffectsBridgeFixture",
                profile, settings_root, game_root, descriptor]
        if repair_owner:
            args.insert(0, "-Dstrata.settingsRepairOwner=true")
        if commit_owner:
            args.insert(0, "-Dstrata.settingsCommitOwner=true")
        if restart_owner:
            args.insert(0, "-Dstrata.settingsRestartOwner=true")
        argfile.write_text("\n".join('"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'
                                   for value in args), encoding="utf-8")
        process = subprocess.Popen([java, "@" + str(argfile)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            expires = time.monotonic() + 20
            while not descriptor.exists() and process.poll() is None and time.monotonic() < expires:
                time.sleep(0.02)
            assert process.poll() is None, process.stderr.read().decode(errors="replace")[-2000:]
            assert descriptor.exists(), "synthetic JVM did not publish descriptor"
            client = NativeSettingsEffectsClient.from_file(descriptor, game_fingerprint="a" * 64,
                                                           settings_fingerprint="d" * 64)
            yield client, process, profile, game_root
        finally:
            if process.poll() is None:
                # A guardian may concurrently terminate this fixture; still wait
                # for actual exit even when its input pipe has already closed.
                with contextlib.suppress(OSError):
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


def apply(client):
    before = client.call("settings_snapshot", {})
    patch = {"transaction_id": "tx", "expected_revision": before["revision"], "expected_digest": before["digest"],
             "changes": {ID: {"before": "key.keyboard.g", "after": "key.keyboard.f13"}}}
    receipt = client.call("settings_apply", patch)
    assert receipt["phase"] == "applied_pending_verification" and receipt["committed"] is False
    return client.call("settings_snapshot", {})


def effect(snapshot, *, hold=50, ticks=2):
    return EffectRequest(id="effect", transaction_id="tx", expected_revision=snapshot["revision"],
        expected_digest=snapshot["digest"], plan_digest="e" * 64, binding_id=ID, context="IN_GAME",
        stage="before_restart", hold_ms=hold, settle_ticks=ticks)


def terminal(client, request):
    expires = time.monotonic() + 5
    while True:
        result = client.call("settings_effect_status", {"id": request.id}, expected_effect=request)
        if result["state"] != "running":
            return result
        assert time.monotonic() < expires, "synthetic input run did not terminate"
        time.sleep(0.02)


def test_production_python_java_apply_observe_status_duplicate_and_rollback(effects_jvm):
    with effects_jvm() as (client, process, profile, game_root):
        request = effect(apply(client))
        first = client.call("settings_effect_start", request.model_dump(mode="json"))
        assert first["state"] in {"running", "observed"}
        result = terminal(client, request)
        assert result["state"] == "observed" and result["verified"] is False and result["committed"] is False
        assert result["observations"][0]["value"]["settings_fingerprint"] == "d" * 64
        length = (game_root / "game-actions.jsonl").stat().st_size
        assert client.call("settings_effect_start", request.model_dump(mode="json")) == result
        assert (game_root / "game-actions.jsonl").stat().st_size == length
        assert client.call("settings_rollback", {"transaction_id": "tx"})["phase"] == "rolled_back"
        assert (profile / "options.txt").read_bytes() == ORIGINAL.encode()
        assert NativeGameClient(client.connection).call("lane_status", {})["fenced"] is True
        assert process.poll() is None


def test_baseline_before_patch_and_after_rollback_never_invents_a_transaction(effects_jvm):
    with effects_jvm() as (client, process, profile, game_root):
        for phase in ("original", "restored"):
            snapshot = client.call("settings_snapshot", {})
            request = effect(snapshot).model_copy(update={"id": phase, "transaction_id": None, "stage": "baseline",
                "context": "IN_GAME" if phase == "original" else "GUI"})
            client.call("settings_effect_start", request.model_dump(mode="json"))
            assert terminal(client, request)["state"] == "observed"
            assert client.call("settings_snapshot", {}) == snapshot
            assert (profile / "options.txt").read_bytes() == ORIGINAL.encode()
            if phase == "original":
                pending = apply(client)
                refused = effect(pending).model_copy(update={"id": "pending-baseline", "transaction_id": None, "stage": "baseline"})
                with pytest.raises(EffectOutcomeUnknown):
                    client.call("settings_effect_start", refused.model_dump(mode="json"))
                client.call("settings_rollback", {"transaction_id": "tx"})


def test_lost_start_reply_queries_same_effect_without_replaying(effects_jvm, monkeypatch):
    with effects_jvm() as (client, process, profile, game_root):
        request = effect(apply(client))
        original = client._transport._exchange

        def lost(method, path, body, timeout):
            response = original(method, path, body, timeout)
            if method == "POST":
                raise TimeoutError("synthetic lost reply")
            return response

        with monkeypatch.context() as scoped:
            scoped.setattr(client._transport, "_exchange", lost)
            with pytest.raises(EffectOutcomeUnknown):
                client.call("settings_effect_start", request.model_dump(mode="json"))
        assert terminal(client, request)["state"] == "observed"
        events = [json.loads(line)["payload"] for line in (game_root / "game-actions.jsonl").read_text().splitlines()]
        assert sum(event["kind"] == "reconfiguration_begin" and event["id"] == request.id for event in events) == 1
        client.call("settings_rollback", {"transaction_id": "tx"})


def test_process_death_fences_old_input_and_recovers_owned_values_without_refund(effects_jvm):
    with effects_jvm() as (client, process, profile, game_root):
        request = effect(apply(client), hold=2000, ticks=200)
        client.call("settings_effect_start", request.model_dump(mode="json"))
        consumed = NativeGameClient(client.connection).call("lane_status", {})["attempted_primitive_events"]
        (game_root / "fixture-freeze").write_text("freeze", encoding="utf-8")
        expires = time.monotonic() + 5
        while not (game_root / "fixture-frozen").exists():
            assert process.poll() is None and time.monotonic() < expires
            time.sleep(0.01)
        process.kill()
        process.wait(timeout=5)
        (game_root / "fixture-freeze").unlink()
        (game_root / "fixture-frozen").unlink()
    with effects_jvm() as (client, process, profile, game_root):
        game = NativeGameClient(client.connection)
        status = game.call("lane_status", {})
        assert status["fenced"] and status["attempted_primitive_events"] >= consumed
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_effect_start", request.model_dump(mode="json"))
        assert client.call("settings_rollback", {"transaction_id": "tx"})["phase"] == "rolled_back"
        assert (profile / "options.txt").read_bytes() == ORIGINAL.encode()
        assert game.call("lane_status", {})["attempted_primitive_events"] > consumed


@pytest.mark.parametrize("action,button,modifier,predicate", [
    ("attack", "left", "SHIFT", "attack_swing"), ("use", "right", "NONE", "item_use_hold")])
def test_native_mouse_binding_roundtrip_is_charged_released_and_observed(effects_jvm, action, button, modifier, predicate):
    from mcbench.native_effect_evidence import evaluate_effect
    suffix = "" if modifier == "NONE" else ":" + modifier
    options = ORIGINAL + "key_key." + action + ":key.mouse." + button + suffix + "\r\n"
    with effects_jvm(options_text=options) as (client, process, profile, game_root):
        head = apply(client)
        request = effect(head, hold=100).model_copy(update={"binding_id": "minecraft:key." + action + ":0"})
        client.call("settings_effect_start", request.model_dump())
        raw = terminal(client, request)
        assert raw["schema"] == "strata/NativeSettingsEffects/4" and raw["state"] == "observed"
        receipt = next(o["value"] for o in raw["observations"] if o["phase"] == "input_release")
        assert receipt["schema"] == "strata/NativeInputRelease/2" and receipt["device"] == "mouse"
        assert receipt["key"] == (0 if button == "left" else 1) and receipt["modifier"] == modifier
        expected = {"schema": "strata/NativeEffectExpectation/2", "request": request.model_dump(),
            "settings_fingerprint": client.settings_fingerprint, "predicate": predicate,
            "initial_screen": "none", "final_screen": "none", "required_openings": [], "forbidden_openings": [],
            "min_horizontal_distance": 0.0, "max_horizontal_distance": .25}
        assert evaluate_effect(expected, raw)["status"] == "pass"
        health = NativeGameClient(client.connection).call("lane_status", {})
        assert health["fenced"] is True and health["attempted_primitive_events"] > 0
        journal = (game_root / "game-actions.jsonl").read_text()
        assert "NativeInputRelease/2" in journal
        assert client.call("settings_rollback", {"transaction_id": "tx"})["phase"] == "rolled_back"
        assert (profile / "options.txt").read_bytes() == options.encode()
        assert process.poll() is None
