"""Actual Python/Java/HTTP with a synthetic world. Explicit opt-in, no Minecraft launch."""

import contextlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mcbench.native_game import GameAuthority, GameOutcomeUnknown, NativeGameClient
from mcbench.storage import Fault


@pytest.fixture
def game_jvm_factory(tmp_path):
    java = os.environ.get("STRATA_CLIENT_TEST_JAVA")
    classpath_file = os.environ.get("STRATA_CLIENT_TEST_CLASSPATH")
    if not java or not classpath_file:
        pytest.skip("explicit pinned Java/classpath required for synthetic game bridge integration")
    classpath = Path(classpath_file).read_text(encoding="utf-8").strip()
    root = tmp_path / "broker"
    root.mkdir()
    authority = GameAuthority.model_validate({"schema": "strata/NativeGameAuthority/1",
        "campaign_id": "campaign", "agent_id": "avatar", "capability_digest": "c" * 64,
        "body_fingerprint": "a" * 64, "expires_unix_ms": int(time.time() * 1000) + 120000,
        "primitive_limit": 1000})
    (root / "game-authority.json").write_text(authority.model_dump_json(by_alias=True), encoding="utf-8")
    launches = 0

    def quoted(value):
        return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'

    @contextlib.contextmanager
    def launch(*, actions=False, hold=False, freeze_file=None, recipe_mode=False):
        nonlocal launches
        launches += 1
        connection_file = tmp_path / f"game-connection-{launches}.json"
        argfile = tmp_path / f"java-args-{launches}.txt"
        arguments = ["-cp", classpath, "io.github.opencnid.strata.client.GameBridgeFixture", connection_file]
        if recipe_mode:
            arguments.insert(0, "-Dstrata.fixture.taskRecipes=true")
        if actions:
            arguments += [root]
            if hold:
                arguments += ["hold"]
            elif freeze_file:
                arguments += ["-"]
            if freeze_file:
                arguments += [freeze_file]
        argfile.write_text("\n".join(map(quoted, arguments)), encoding="utf-8")
        process = subprocess.Popen([java, "@" + str(argfile)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        client = None
        try:
            expires = time.monotonic() + 20
            while time.monotonic() < expires:
                assert process.poll() is None, "synthetic JVM exited before publishing connection"
                if connection_file.exists():
                    try:
                        client = NativeGameClient.from_file(connection_file)
                        break
                    except ValueError:
                        pass
                time.sleep(.02)
            assert client is not None, "synthetic JVM connection not ready within 20s"
            yield client, process, root
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


@pytest.fixture
def game_jvm(game_jvm_factory):
    with game_jvm_factory() as (client, _, __):
        yield client


def test_real_http_python_java_projection_pagination_and_negative_coordinates(game_jvm):
    caps = game_jvm.capabilities()
    assert caps["backend"] == "forge_client" and not caps["campaign_admission"]
    assert caps["actions"] == [] and caps["conformance"] == "unverified"
    first = current = game_jvm.observe()
    assert first["state"]["position"]["x"] == -1.25
    positions = set()
    pages = 0
    while True:
        pages += 1
        assert pages < 129
        assert current["state_revision"] == first["state_revision"]
        assert current["source_clock_id"] == first["source_clock_id"]
        assert current["captured_elapsed_ms"] == first["captured_elapsed_ms"]
        assert current["age_ms"] >= first["age_ms"]
        blocks = current["state"]["nearby_blocks"]
        assert len(blocks) <= 128
        for block in blocks:
            position = tuple(block["position"][key] for key in ("x", "y", "z"))
            assert position not in positions and position[1] >= 64
            assert block["block_id"] in {"minecraft:air", "fixture:floor"}
            positions.add(position)
        cursor = current["state"]["next_cursor"]
        if cursor is None:
            break
        current = game_jvm.observe(cursor)
    assert pages > 1 and len(positions) > 128
    assert not current["state"]["truncated"]
    with pytest.raises(Fault, match="STALE_OBSERVATION"):
        game_jvm.observe("guessed-cursor")


def test_focused_recipe_query_crosses_real_http_and_jvm_with_synthetic_source(game_jvm):
    query = {"source": "jei", "category": "minecraft:crafting", "item_id": "fixture:output", "role": "output", "after": 0}
    result = game_jvm.call("recipe_query", query)
    assert result["query"] == query and result["source_generation"] == 1
    assert result["recipes"][0]["craft_authority"] == "discovery_only"
    assert result["recipes"][0]["supported"] is True
    assert result["recipes"][1] == {"recipe_id": "fixture:unsupported", "supported": False, "craft_authority": "recipe_book"}
    assert result["body_fingerprint"] == "a" * 64 and result["connection_generation"] == 1


def test_current_quest_menu_crosses_actual_jvm_with_synthetic_visible_source(game_jvm):
    page = game_jvm.call("quest_menu", {"source": "ftb_quests", "after": 0})
    assert page["menu_kind"] == "item_alternatives" and page["menu_generation"] == 1
    assert page["entries"][0]["item_id"] == "minecraft:stone"
    assert page["controls"][0]["control"] == "submit" and page["controls"][0]["enabled"] is False
    assert page["body_fingerprint"] == "a" * 64 and page["connection_generation"] == 1
    assert game_jvm.call("quest_menu", {"source": "ftb_quests", "after": 1})["entries"] == []
    with pytest.raises(Fault):
        game_jvm.call("quest_menu", {"source": "ftb_quests", "after": 2})


def test_actual_recipe_transport_projects_synthetic_definition_and_unknown_serializer(game_jvm):
    page = game_jvm.call("recipes", {"after": 0})
    assert page["body_fingerprint"] == "a" * 64 and page["connection_generation"] == 1
    assert page["recipes"][0]["ingredients"] == [["fixture:changed_ingredient"]]
    assert page["recipes"][0]["result"] == {"item_id": "fixture:output", "count": 2}
    assert page["recipes"][1] == {"recipe_id": "fixture:unsupported", "supported": False}
    assert page["next_cursor"] is None
    assert game_jvm.call("recipes", {"after": 1})["recipes"] == page["recipes"][1:]
    with pytest.raises(Fault, match="GAME_RECIPE_BOUNDS"):
        game_jvm.call("recipes", {"after": 3})


def test_old_session_is_rejected_by_actual_java_endpoint(game_jvm):
    game_jvm.connection.session_id = "previous-session"
    with pytest.raises(Fault, match="GAME_SESSION_MISMATCH"):
        game_jvm.observe()


def action_batch(snapshot, epoch, request_id):
    now = time.time()

    def utc(t):
        return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    return {"schema": "mcbench/ActionBatch/1", "is_example": False, "campaign_id": "campaign", "agent_id": "avatar",
        "epoch": epoch, "seq": 1, "recorded_at": utc(now), "lease_id": f"lease-{epoch}",
        "request_id": request_id, "observation_id": "observation", "mode": "structured",
        "expected_state_revision": snapshot["state_revision"], "capability_digest": "c" * 64,
        "control_revision": epoch, "keymap_digest": None, "deadline_at": utc(now + 5), "duration_ms": 5000,
        "action": {"kind": "look_at", "target": {"x": -1.25, "y": 65.5, "z": 2.5}},
        "events": [], "release_at_end": True}


def prepare(client, epoch=1):
    state = client.call("lane_status", {})
    client.call("arm", {"epoch": epoch, "lease_id": f"lease-{epoch}", "lease_until_unix_ms": int(time.time() * 1000) + 6000,
                        "expected_fence_token": state["fence_token"]})
    snapshot = client.observe()
    client.call("deliver", {"observation_id": "observation", "snapshot_id": snapshot["snapshot_id"],
                            "state_revision": snapshot["state_revision"]})
    return snapshot


def wait_receipt(client, request_id, *, executing=False):
    expires = time.monotonic() + 5
    while time.monotonic() < expires:
        try:
            receipt = client.call("action_status", {"request_id": request_id})
        except Fault as error:
            assert error.code == "GAME_REQUEST_UNKNOWN"
        else:
            if receipt["status"] == "executing" if executing else receipt["status"] not in {"accepted", "executing"}:
                return receipt
        time.sleep(.02)
    pytest.fail("native synthetic action did not reach the expected phase")


def test_actual_native_intent_delivery_dedup_and_post_action_observation(game_jvm_factory):
    with game_jvm_factory(actions=True) as (client, _, root):
        caps = client.capabilities()
        assert caps["actions"] == ["attack", "chat", "click_slot", "close_window", "craft", "dig", "equip", "interact_block", "interact_entity", "look_at", "move_to", "place", "quest_menu", "quest_navigate", "quest_reward", "quest_task", "quest_ui", "recipe_navigate", "use_item"]
        assert caps["movement_policy"] == "level-forward-coast-neutral8-charged-ticks/1"
        assert client.call("identity", {})["body_fingerprint"] == "a" * 64
        initial = prepare(client)
        batch = action_batch(initial, 1, "look-1")
        client.call("act", {"batch": batch})
        receipt = wait_receipt(client, "look-1")
        assert receipt["status"] == "emitted" and receipt["emitted_events"] == 2
        assert receipt["release_confirmed"] and receipt["requires_resync"]
        assert client.call("act", {"batch": batch}) == receipt
        after = client.observe()
        assert after["state"]["position"]["x"] == initial["state"]["position"]["x"] + 1
        assert after["state"]["active_request_id"] is None
        events = [json.loads(line)["payload"] for line in (root / "game-actions.jsonl").read_text(encoding="utf-8").splitlines()]
        assert sum(event["kind"] == "intent" for event in events) == 1
        assert sum(event["kind"] == "delivery" for event in events) == 1
        assert client.call("lane_status", {})["attempted_primitive_events"] == 3


@pytest.mark.parametrize("action", [
    {"kind": "use_item", "hand": "off", "hold_ms": 250},
    {"kind": "attack", "entity_id": "fixture-observed"},
    {"kind": "interact_entity", "entity_id": "fixture-observed"},
    {"kind": "chat", "text": "café 中文 🧭"},
    {"kind": "equip", "inventory_slot": 10, "expected_item_id": "minecraft:stone", "destination": "hand"},
    {"kind": "place", "support": {"x": 0, "y": 64, "z": 0}, "face": {"x": 0, "y": 1, "z": 0}, "expected_item_id": "minecraft:stone"},
    {"kind": "move_to", "target": {"x": 2, "y": 65, "z": 2}, "tolerance": 0.1},
    {"kind": "craft", "recipe_id": "fixture:expert", "count": 1, "window_id": 0, "expected_window_revision": 1, "recipe_selection": None},
    {"kind": "craft", "recipe_id": "fixture:expert", "count": 1, "window_id": 0, "expected_window_revision": 1,
     "recipe_selection": {"source_generation": 1, "revision": 1, "query": {"source": "jei", "category": "minecraft:crafting", "item_id": "fixture:output", "role": "output", "after": 0}}},
    {"kind": "close_window", "window_id": 1, "expected_window_revision": 1},
    {"kind": "quest_ui", "operation": "open", "source": "ftb_quests", "source_generation": 1, "expected_catalog_revision": 1},
])
def test_gesture_envelopes_reach_synthetic_jvm_motor_once(game_jvm_factory, action):
    with game_jvm_factory(actions=True) as (client, _, root):
        batch = action_batch(prepare(client), 1, "gesture") | {"action": action}
        if action["kind"] == "move_to":
            batch["duration_ms"] = 30000
        client.call("act", {"batch": batch})
        receipt = wait_receipt(client, "gesture")
        assert receipt["status"] == "emitted" and receipt["release_confirmed"]
        assert client.call("act", {"batch": batch}) == receipt
        events = [json.loads(line)["payload"] for line in (root / "game-actions.jsonl").read_text(encoding="utf-8").splitlines()]
        assert [json.loads(event["batch_json"])["action"] for event in events if event["kind"] == "intent"] == [action]


def test_actual_jvm_quest_open_navigate_back_close_with_synthetic_native_ui(game_jvm_factory):
    with game_jvm_factory(actions=True) as (client, _, root):
        assert client.call("quest_screen", {})["kind"] == "closed"
        snap = prepare(client)
        opening = action_batch(snap, 1, "open") | {"action": {"kind": "quest_ui", "operation": "open", "source": "ftb_quests",
                                                            "source_generation": 1, "expected_catalog_revision": 1}}
        client.call("act", {"batch": opening})
        assert wait_receipt(client, "open")["status"] == "emitted"
        for seq, operation in enumerate(["chapter", "quest", "back", "close"], 2):
            state = client.call("quest_screen", {})
            select = None
            if operation in {"chapter", "quest"}:
                query = {"source": "ftb_quests", "chapter_id": "0000000000000001" if operation == "quest" else None, "after": 0}
                page = client.call("quests", query)
                select = {"query": query, "revision": page["revision"], "entry_id": page["entries"][0]["entry_id"]}
            snap = client.observe()
            observation = f"observation-{seq}"
            client.call("deliver", {"observation_id": observation, "snapshot_id": snap["snapshot_id"], "state_revision": snap["state_revision"]})
            action = {"kind": "quest_navigate", "operation": operation, "source": "ftb_quests", "source_generation": state["source_generation"],
                      "expected_screen_generation": state["screen_generation"], "expected_screen_revision": state["revision"], "selection": select}
            batch = action_batch(snap, 1, f"nav-{seq}") | {"seq": seq, "observation_id": observation, "action": action}
            client.call("act", {"batch": batch})
            receipt = wait_receipt(client, batch["request_id"])
            assert receipt["status"] == "emitted" and receipt["emitted_events"] == 2
            assert client.call("act", {"batch": batch}) == receipt
            after = client.call("quest_screen", {})
            assert after["kind"] == ("closed" if operation == "close" else "quest_book")
            assert after["quest_id"] == ("0000000000000002" if operation == "quest" else None)
        events = [json.loads(line)["payload"] for line in (root / "game-actions.jsonl").read_text(encoding="utf-8").splitlines()]
        assert sum(event["kind"] == "intent" for event in events) == 5


@pytest.mark.parametrize("opening_kind,recipe_mode", [("quest_task", False), ("quest_reward", False), ("quest_task", True)])
def test_actual_jvm_opens_selected_task_menu_once_with_synthetic_ui(game_jvm_factory, opening_kind, recipe_mode):
    with game_jvm_factory(actions=True, recipe_mode=recipe_mode) as (client, _, root):
        snap = prepare(client)
        for seq, kind in enumerate(["quest_ui", "quest_navigate", opening_kind], 1):
            action = {"kind": kind, "source": "ftb_quests", "source_generation": 1, "operation": "open"}
            if kind == "quest_ui":
                action["expected_catalog_revision"] = 1
            else:
                state = client.call("quest_screen", {})
                query = {"source": "ftb_quests", "chapter_id": "0000000000000001", "after": 0}
                if kind == opening_kind:
                    query |= {"quest_id": "0000000000000002", "part": "tasks" if kind == "quest_task" else "rewards"}
                else:
                    action["operation"] = "quest"
                page = client.call("quest_components" if kind == opening_kind else "quests", query)
                action |= {"expected_screen_generation": state["screen_generation"], "expected_screen_revision": state["revision"],
                           "selection": {"query": query, "revision": page["revision"], "entry_id": page["entries"][0]["entry_id"]}}
                snap = client.observe()
                client.call("deliver", {"observation_id": f"observation-{seq}", "snapshot_id": snap["snapshot_id"], "state_revision": snap["state_revision"]})
            batch = action_batch(snap, 1, f"task-{seq}") | {"seq": seq, "action": action}
            if seq > 1:
                batch["observation_id"] = f"observation-{seq}"
            client.call("act", {"batch": batch})
            receipt = wait_receipt(client, batch["request_id"])
            assert receipt["status"] == "emitted" and receipt["emitted_events"] == 2
            assert client.call("act", {"batch": batch}) == receipt
        if recipe_mode:
            state = client.call("quest_screen", {})
            assert state["kind"] == "task_recipes" and state["quest_id"] == "0000000000000002"
            rendered = client.call("recipe_page", {})
            assert rendered["coverage"] == "slot_header_control_draw_operands" and rendered["complete"] is False
            assert rendered["headers"] == [
                {"kind": "category", "state": "text", "text": "Visible café <&> \"title\" \\u2028 \u2028\u2029 😀"},
                {"kind": "page", "state": "text", "text": "1/4"},
            ]
            assert rendered["quest_id"] == state["quest_id"] and rendered["screen_generation"] == state["screen_generation"]
            assert rendered["controls"] == [{"kind": kind, "state": status} for kind, status in zip(
                ("category_next", "category_previous", "page_next", "page_previous"), ("enabled", "disabled", "clipped", "clipped"))]
            assert [slot["display"]["kind"] for slot in rendered["layouts"][0]["slots"]] == ["item", "fluid", "unsupported", "empty"]
            with pytest.raises(Fault):
                client.call("recipe_page", {"team_id": "private"})
            with pytest.raises(Fault):
                client.call("quest_menu", {"source": "ftb_quests", "after": 0})
            snap = client.observe()
            client.call("deliver", {"observation_id": "observation-nav", "snapshot_id": snap["snapshot_id"], "state_revision": snap["state_revision"]})
            navigation = {"kind": "recipe_navigate", "source": "jei", "control": "category_next",
                          "source_generation": rendered["source_generation"], "expected_screen_generation": rendered["screen_generation"],
                          "expected_screen_revision": rendered["screen_revision"], "expected_page_revision": rendered["revision"]}
            nav_batch = action_batch(snap, 1, "recipe-navigation") | {"seq": 4, "action": navigation, "observation_id": "observation-nav"}
            client.call("act", {"batch": nav_batch})
            nav_receipt = wait_receipt(client, nav_batch["request_id"])
            assert nav_receipt["status"] == "emitted" and nav_receipt["emitted_events"] == 4
            assert client.call("act", {"batch": nav_batch}) == nav_receipt
            after_nav = client.call("recipe_page", {})
            assert after_nav["revision"] != rendered["revision"] and after_nav["headers"][0]["text"] == "Synthetic category 1"
            assert after_nav["layouts"] == []  # Observed empty loop, not missing render evidence.
            for seq in (5, 6):
                current_page = client.call("recipe_page", {})
                snap = client.observe()
                observation_id = f"observation-history-{seq}"
                client.call("deliver", {"observation_id": observation_id, "snapshot_id": snap["snapshot_id"], "state_revision": snap["state_revision"]})
                history = navigation | {"control": "history_back", "expected_page_revision": current_page["revision"]}
                history_batch = action_batch(snap, 1, f"recipe-history-{seq}") | {"seq": seq, "action": history, "observation_id": observation_id}
                client.call("act", {"batch": history_batch})
                history_receipt = wait_receipt(client, history_batch["request_id"])
                assert history_receipt["status"] == "emitted" and history_receipt["emitted_events"] == 3
                assert client.call("act", {"batch": history_batch}) == history_receipt
                assert client.call("recipe_page", {})["revision"] == rendered["revision"]
                assert client.call("quest_screen", {})["kind"] == "task_recipes"
            snap = client.observe()
            client.call("deliver", {"observation_id": "observation-4", "snapshot_id": snap["snapshot_id"], "state_revision": snap["state_revision"]})
            action = {"kind": "quest_navigate", "operation": "close", "source": "ftb_quests", "source_generation": state["source_generation"],
                      "expected_screen_generation": state["screen_generation"], "expected_screen_revision": state["revision"], "selection": None}
            batch = action_batch(snap, 1, "recipe-close") | {"seq": 7, "action": action, "observation_id": "observation-4"}
            client.call("act", {"batch": batch})
            receipt = wait_receipt(client, batch["request_id"])
            assert receipt["status"] == "emitted" and receipt["emitted_events"] == 2
            assert client.call("act", {"batch": batch}) == receipt
            parent = client.call("quest_screen", {})
            assert parent["kind"] == "quest_book" and parent["quest_id"] == "0000000000000002"
            with pytest.raises(Fault):
                client.call("recipe_page", {})
            events = [json.loads(line)["payload"] for line in (root / "game-actions.jsonl").read_text(encoding="utf-8").splitlines()]
            assert sum(event["kind"] == "intent" for event in events) == 7
            return
        # The fixture forbids mislabeling either menu as a book after the actual motor.
        with pytest.raises(Fault):
            client.call("quest_screen", {})
        if opening_kind == "quest_reward":
            menu = client.call("quest_menu", {"source": "ftb_quests", "after": 0})
            assert menu["menu_kind"] == "reward_choices" and menu["context"]["reward_id"] == "0000000000000003"
            assert menu["entries"][0] == {"index": 0, "title": "Visible choice", "enabled": False,
                                          "tooltip": [{"kind": "text", "text": "Visible tooltip"}]}
            assert menu["controls"] == []
        for seq, direction in enumerate(["down", "up", None], 4):
            menu = client.call("quest_menu", {"source": "ftb_quests", "after": 0})
            snap = client.observe()
            client.call("deliver", {"observation_id": f"observation-{seq}", "snapshot_id": snap["snapshot_id"], "state_revision": snap["state_revision"]})
            action = {"kind": "quest_menu", "operation": "back" if direction is None else "scroll", "direction": direction,
                      "source": "ftb_quests", "source_generation": menu["source_generation"],
                      "expected_menu_generation": menu["menu_generation"], "expected_menu_revision": menu["revision"]}
            batch = action_batch(snap, 1, f"menu-{seq}") | {"seq": seq, "action": action, "observation_id": f"observation-{seq}"}
            client.call("act", {"batch": batch})
            receipt = wait_receipt(client, batch["request_id"])
            assert receipt["status"] == "emitted" and receipt["emitted_events"] == 2
            assert client.call("act", {"batch": batch}) == receipt
            if direction is not None:
                assert client.call("quest_menu", {"source": "ftb_quests", "after": 0})["revision"] > menu["revision"]
        assert client.call("quest_screen", {})["quest_id"] == "0000000000000002"
        events = [json.loads(line)["payload"] for line in (root / "game-actions.jsonl").read_text(encoding="utf-8").splitlines()]
        assert sum(event["kind"] == "intent" for event in events) == 6


def test_lost_http_ack_is_queried_without_a_second_native_action(game_jvm_factory, monkeypatch):
    with game_jvm_factory(actions=True) as (client, _, __):
        batch = action_batch(prepare(client), 1, "uncertain")
        original = client._transport._exchange
        posts = []

        def lose_ack(method, path, body, timeout):
            result = original(method, path, body, timeout)
            if method == "POST" and json.loads(body)["operation"] == "act":
                posts.append(json.loads(body)["request_id"])
                raise TimeoutError("injected after actual HTTP acceptance")
            return result

        monkeypatch.setattr(client._transport, "_exchange", lose_ack)
        with pytest.raises(GameOutcomeUnknown) as error:
            client.call("act", {"batch": batch})
        assert error.value.action_id == "uncertain"
        assert wait_receipt(client, "uncertain")["status"] == "emitted"
        assert len(posts) == 1


def test_actual_jvm_kill_requires_new_epoch_and_never_replays_pending_input(game_jvm_factory):
    with game_jvm_factory(actions=True, hold=True) as (client, process, root):
        batch = action_batch(prepare(client), 1, "interrupted")
        client.call("act", {"batch": batch})
        wait_receipt(client, "interrupted", executing=True)
        previous_session = client.connection.session_id
        process.kill()  # The synthetic fixture process only; never a Minecraft process.
        process.wait(timeout=5)
    with game_jvm_factory(actions=True) as (client, _, __):
        assert client.connection.session_id != previous_session
        receipt = client.call("action_status", {"request_id": "interrupted"})
        assert receipt["status"] == "unknown" and receipt["emitted_events"] is None
        assert client.call("act", {"batch": batch}) == receipt
        assert client.call("lane_status", {})["attempted_primitive_events"] == 2
        # The synthetic body starts fresh: this checks no replay, not real world recovery.
        assert client.observe()["state"]["position"]["x"] == -1.25
        with pytest.raises(GameOutcomeUnknown):
            prepare(client, 1)
        prepare(client, 2)
        assert client.call("lane_status", {})["attempted_primitive_events"] == 3


def test_actual_stop_releases_active_synthetic_motor(game_jvm_factory):
    with game_jvm_factory(actions=True, hold=True) as (client, _, __):
        client.call("act", {"batch": action_batch(prepare(client), 1, "running")})
        wait_receipt(client, "running", executing=True)
        stopped = client.call("stop_all", {})
        assert stopped["fenced"] and stopped["active_request_id"] is None
        receipt = client.call("action_status", {"request_id": "running"})
        assert receipt["status"] == "cancelled" and receipt["release_confirmed"]
