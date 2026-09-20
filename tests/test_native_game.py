"""Synthetic payload and transport faults; actual Minecraft remains untested."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from mcbench.native_game import RECIPE_QUERY_POLICY, GameConnection, GameOutcomeUnknown, GameResponse, NativeGameClient, main
from mcbench.contracts import RpcRequest
from mcbench.storage import Fault


def test_native_block_target_policy_agrees_with_compiled_broker_and_rejects_old_identity():
    from pydantic import ValidationError
    from mcbench.native_game import GameCapabilities
    module = (Path(__file__).resolve().parents[1] / "backends/mineflayer/dist/src/native_game.js").as_uri()
    script = f"import {{nativeCapabilities}} from {json.dumps(module)}; console.log(JSON.stringify(nativeCapabilities(true)));"
    result = subprocess.run([shutil.which("node"), "--input-type=module", "-e", script],
                            capture_output=True, text=True, timeout=10, check=True)
    value = json.loads(result.stdout)
    caps = GameCapabilities.model_validate(value)
    assert caps.block_target_policy == "observed-outline-centers64-local16/1"
    for patch in ({"native_action_policy": "durable-intent-client-thread-nineteen-actions/1"},
                  {"block_target_policy": "unqualified"}):
        with pytest.raises(ValidationError):
            GameCapabilities.model_validate(value | patch)
    value.pop("block_target_policy")
    with pytest.raises(ValidationError):
        GameCapabilities.model_validate(value)


def connection():
    return GameConnection.model_validate({"schema": "strata/NativeGameConnection/1",
        "host": "127.0.0.1", "port": 12345, "session_id": "session-1", "bearer_token": "b" * 64,
        "fingerprint": "a" * 64, "operator_development_only": True})


def snapshot():
    return {"schema": "strata/NativeGameSnapshot/1", "snapshot_id": "snapshot-1",
        "state_revision": 3, "source_clock_id": "clock-1", "captured_elapsed_ms": 1000, "age_ms": 50,
        "state": {"dimension": "minecraft:overworld", "position": {"x": -1.25, "y": 65.0, "z": 2.5},
            "yaw": 1.2, "pitch": -0.5, "health": 20.0, "food": 20.0, "inventory": [], "window": None,
            "nearby_blocks": [], "nearby_entities": [], "active_request_id": None,
            "connected": True, "truncated": False, "next_cursor": None}}


@pytest.mark.parametrize("fault", [None, "energy", "fluid", "tag", "kind", "layout", "type", "negative", "boolean"])
def test_current_machine_display_is_strict_and_bounded(monkeypatch, fault):
    client = NativeGameClient(connection())
    value = snapshot()
    machine = {"policy": "thermal-current-gui-energy-fluid-base-slots/1", "kind": "thermal:machine_crucible",
               "energy": {"stored": 100, "capacity": 1000},
               "tanks": [{"capacity_mb": 4000, "contents": {"fluid_id": "minecraft:lava", "amount_mb": 250}}]}
    window = {"id": 7, "revision": 10, "type": "thermal:machine_crucible", "slots": [],
              "cursor_item": None, "machine": machine}
    value["state"]["window"] = window
    if fault == "energy":
        machine["energy"]["stored"] = 1001
    elif fault == "fluid":
        machine["tanks"][0]["contents"]["amount_mb"] = 4001
    elif fault == "tag":
        machine["tanks"][0]["contents"]["nbt"] = "private-canary"
    elif fault == "kind":
        machine["kind"] = "unknown:machine"
    elif fault == "layout":
        machine["tanks"] = []
    elif fault == "type":
        window["type"] = "minecraft:chest"
    elif fault == "negative":
        machine["energy"]["stored"] = -1
    elif fault == "boolean":
        machine["energy"]["stored"] = True

    monkeypatch.setattr(client._transport, "_exchange",
                        lambda method, path, body, timeout: response(json.loads(body), result=value))
    if fault:
        with pytest.raises(Fault, match="GAME_OBSERVATION_UNAVAILABLE"):
            client.observe()
    else:
        result = client.observe()
        assert result["state"]["window"]["machine"] == machine
        machine["tanks"][0]["contents"] = None
        assert client.observe()["state"]["window"]["machine"]["tanks"][0]["contents"] is None


def response(request, **changes):
    return GameResponse.model_validate({"schema": "strata/NativeGameResponse/1",
        "request_id": request["request_id"], "session_id": "session-1", "status": "completed",
        "result": snapshot(), "error_code": None} | changes)


def test_observation_is_strict_typed_and_native_clock_is_not_restamped(monkeypatch):
    client = NativeGameClient(connection())
    methods = []
    request = None

    def exchange(method, path, body, timeout):
        nonlocal request
        methods.append(method)
        if method == "POST":
            assert path == "/v1/game"
            request = json.loads(body)
            assert request["schema"] == "strata/NativeGameRequest/1"
            assert request["args"] == {"cursor": None}
            return response(request, status="accepted", result=None)
        assert path.endswith(request["request_id"])
        return response(request)

    monkeypatch.setattr(client._transport, "_exchange", exchange)
    result = client.observe()
    assert methods == ["POST", "GET"]
    assert result["captured_elapsed_ms"] == 1000 and result["age_ms"] == 50
    assert "captured_mono_ms" not in result
    assert result["state"]["position"]["x"] == -1.25


def test_bound_observation_preserves_atomic_identity_and_rejects_hidden_fields(monkeypatch):
    client = NativeGameClient(connection())
    value = {"schema": "strata/NativeBoundSnapshot/1", "snapshot": snapshot(),
             "body_fingerprint": "a" * 64, "connection_generation": 7}

    def exchange(method, path, body, timeout):
        request = json.loads(body)
        assert request["operation"] == "observe_bound" and request["args"] == {"cursor": None}
        return response(request, result=value)

    monkeypatch.setattr(client._transport, "_exchange", exchange)
    result = client.call("observe_bound", {"cursor": None})
    assert result["connection_generation"] == 7
    assert result["snapshot"]["captured_elapsed_ms"] == 1000
    value["snapshot"]["state"]["private_score"] = 1
    with pytest.raises(Fault, match="GAME_OBSERVATION_UNAVAILABLE"):
        client.call("observe_bound", {"cursor": None})


@pytest.mark.parametrize("fault", [None, "hidden", "unsupported_fields", "cursor", "ingredients", "result", "duplicates", "boolean"])
def test_recipe_projection_is_bounded_and_private_fields_are_rejected(monkeypatch, fault):
    client = NativeGameClient(connection())
    recipe = {"recipe_id": "test:expert", "supported": True, "serializer": "minecraft:crafting_shaped",
              "width": 1, "height": 1, "ingredients": [["test:actual_ingredient"]],
              "result": {"item_id": "test:actual_output", "count": 2}}
    value = {"schema": "strata/NativeRecipeList/1", "body_fingerprint": "a" * 64, "connection_generation": 1,
             "revision": 4, "recipes": [recipe], "next_cursor": None}
    if fault == "hidden":
        recipe["evaluator_score"] = 1
    elif fault == "unsupported_fields":
        recipe["supported"] = False
    elif fault == "cursor":
        value["next_cursor"] = 9
    elif fault == "ingredients":
        recipe["ingredients"] = [[]]
    elif fault == "result":
        recipe["result"]["count"] = 65
    elif fault == "duplicates":
        value["recipes"].append(recipe.copy())
    elif fault == "boolean":
        recipe["supported"] = 1
    calls = []

    def exchange(method, path, body, timeout):
        calls.append(method)
        request = json.loads(body)
        assert request["operation"] == "recipes" and request["args"] == {"after": 0}
        return response(request, result=value)

    monkeypatch.setattr(client._transport, "_exchange", exchange)
    if fault:
        with pytest.raises(Fault):
            client.call("recipes", {"after": 0})
    else:
        assert client.call("recipes", {"after": 0}) == value
    assert calls == ["POST"]
    for after in [-1, 10001, True, "0"]:
        with pytest.raises(Fault, match="GAME_ARGUMENTS_INVALID"):
            client.call("recipes", {"after": after})
    assert calls == ["POST"]


def test_loaded_native_authority_is_typed_and_read_only(monkeypatch):
    client = NativeGameClient(connection())
    value = {"schema": "strata/NativeGameAuthority/1", "campaign_id": "campaign", "agent_id": "avatar",
             "capability_digest": "c" * 64, "body_fingerprint": "a" * 64,
             "expires_unix_ms": 2000000000000, "primitive_limit": 100}

    def exchange(method, path, body, timeout):
        request = json.loads(body)
        assert request["operation"] == "authority" and request["args"] == {}
        return response(request, result=value)

    monkeypatch.setattr(client._transport, "_exchange", exchange)
    assert client.call("authority", {}) == value
    value["private_key"] = "canary"
    with pytest.raises(Fault, match="GAME_OBSERVATION_UNAVAILABLE"):
        client.call("authority", {})


@pytest.mark.parametrize("fault", [None, "echo", "policy", "generation", "hidden", "authority", "cursor", "boolean"])
def test_focused_recipe_query_is_strict_and_discovery_only(monkeypatch, fault):
    client = NativeGameClient(connection())
    query = {"source": "jei", "category": "minecraft:crafting", "item_id": "fixture:output", "role": "output", "after": 0}
    recipe = {"recipe_id": "fixture:expert", "supported": False, "craft_authority": "discovery_only"}
    value = {"schema": "strata/NativeRecipeQuery/1", "body_fingerprint": "a" * 64, "connection_generation": 1,
             "revision": 1, "query": query.copy(), "source_generation": 1, "policy": RECIPE_QUERY_POLICY,
             "recipes": [recipe], "next_cursor": None}
    if fault == "echo":
        value["query"]["role"] = "input"
    elif fault == "policy":
        value["policy"] = "global-recipes"
    elif fault == "generation":
        value["source_generation"] = -1
    elif fault == "hidden":
        recipe["hidden_solution"] = "canary"
    elif fault == "authority":
        recipe["craft_authority"] = "arbitrary"
    elif fault == "cursor":
        value["next_cursor"] = 2
    elif fault == "boolean":
        recipe["supported"] = 0
    calls = []

    def exchange(method, path, body, timeout):
        calls.append(method)
        request = json.loads(body)
        assert request["operation"] == "recipe_query" and request["args"] == query
        return response(request, result=value)

    monkeypatch.setattr(client._transport, "_exchange", exchange)
    if fault:
        with pytest.raises(Fault):
            client.call("recipe_query", query)
    else:
        assert client.call("recipe_query", query) == value
    assert calls == ["POST"]
    for patch in [{"source": "server"}, {"category": "minecraft:smelting"}, {"role": "all"},
                  {"item_id": "*"}, {"after": -1}, {"after": 513}, {"after": True}, {"include_hidden": True}]:
        with pytest.raises(ValueError):
            client.call("recipe_query", query | patch)
    assert calls == ["POST"]
    rpc = {"schema": "strata/GameRequest/1", "request_id": "query", "campaign_id": "campaign", "agent_id": "avatar",
           "epoch": 1, "deadline_at": "2026-09-19T00:00:00Z", "method": "recipes.query", "recipe_query": query,
           "action": None, "target_request_id": None, "after": None}
    assert RpcRequest.model_validate(rpc).recipe_query.item_id == "fixture:output"
    for patch in [{"method": "observe"}, {"recipe_query": None}, {"after": 0}]:
        with pytest.raises(ValueError):
            RpcRequest.model_validate(rpc | patch)


@pytest.mark.parametrize("case", ["hidden", "nbt", "cursor", "session", "truncated", "timeout"])
def test_private_or_malformed_responses_fail_without_replay(monkeypatch, case):
    client = NativeGameClient(connection())
    calls = []

    def exchange(method, path, body, timeout):
        calls.append(method)
        if case == "timeout":
            raise TimeoutError("private credential")
        value = response(json.loads(body))
        if case == "hidden":
            value.result["state"]["private_score"] = 1
        elif case == "nbt":
            value.result["state"]["inventory"] = [{"slot": 0, "item_id": "pack:box", "count": 1,
                "component_summary": {"BlockEntityTag": {"Items": ["hidden"]}}}]
        elif case == "cursor":
            value.result["state"]["next_cursor"] = "forged"
        elif case == "session":
            value.session_id = "other-session"
        elif case == "truncated":
            value.result["state"]["nearby_entities"] = [{"id": "1", "type": "pig"}] * 129
        return value

    monkeypatch.setattr(client._transport, "_exchange", exchange)
    with pytest.raises(Fault):
        client.observe()
    assert calls == ["POST"]


def test_unsupported_actions_and_coordinate_queries_never_reach_transport(monkeypatch):
    client = NativeGameClient(connection())
    monkeypatch.setattr(client._transport, "_exchange", lambda *_: pytest.fail("unexpected network"))
    with pytest.raises(Fault, match="CAPABILITY_MISSING"):
        client.call("raw_packet", {"kind": "look_at"})
    with pytest.raises(Fault, match="GAME_ARGUMENTS_INVALID"):
        client.call("observe", {"cursor": None, "x": 500})


def test_connection_file_rejects_settings_schema_and_never_prints_credentials(tmp_path, capsys):
    value = connection().model_dump(mode="json", by_alias=True)
    value["bearer_token"] = "private-credential-that-must-stay-secret"
    path = tmp_path / "connection.json"
    path.write_text(json.dumps(value))
    assert main(["--connection", str(path), "observe"]) == 1
    output = capsys.readouterr().out
    assert "private-credential" not in output and "GAME_CONNECTION_INVALID" in output
    value["schema"] = "strata/NativeSettingsConnection/1"
    value["bearer_token"] = "b" * 64
    path.write_text(json.dumps(value))
    with pytest.raises(Fault, match="GAME_CONNECTION_INVALID"):
        NativeGameClient.from_file(path)


@pytest.mark.parametrize("case", ["timeout", "session", "receipt"])
def test_ambiguous_mutation_never_reposts_and_retains_action_identity(monkeypatch, case):
    from test_native_game_jvm import action_batch
    client = NativeGameClient(connection())
    batch = action_batch(snapshot(), 1, "action-id")
    calls = []

    def exchange(method, path, body, timeout):
        calls.append(method)
        if case == "timeout":
            raise TimeoutError("private wire data")
        value = response(json.loads(body), result={"schema": "strata/NativeGameActionReceipt/1",
            "request_id": "action-id", "epoch": 1, "action_seq": 1, "status": "emitted",
            "attempted_events": 2, "emitted_events": 2, "release_confirmed": True,
            "error_code": None, "requires_resync": True})
        if case == "session":
            value.session_id = "foreign"
        else:
            value.result["status"] = "completed"  # This unqualified motor cannot assert completion.
        return value

    monkeypatch.setattr(client._transport, "_exchange", exchange)
    with pytest.raises(GameOutcomeUnknown) as error:
        client.call("act", {"batch": batch})
    assert error.value.action_id == "action-id" and error.value.operation == "act"
    assert calls == ["POST"]
