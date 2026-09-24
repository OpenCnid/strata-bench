"""Fixed negative-control producer; synthetic local bytes, no model or game launch."""

import hashlib
import io
import json
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from mcbench.inference_transport import ResponsesUsage
from mcbench.storage import Fault
from native_game_failure_probe import GameTransportFailureProbe, contains_observation
from native_mcp_identity_probe import run


@pytest.fixture
def probe():
    return GameTransportFailureProbe({"url": "http://127.0.0.1:1/v1/game", "token": "fixture-token-0000",
        "campaign_id": "c1", "agent_id": "a1", "epoch": 1}, "lease-1")


def handler():
    return SimpleNamespace(wfile=io.BytesIO(), send_response=lambda *_: None,
        send_header=lambda *_: None, end_headers=lambda: None)


def test_truncation_retains_exact_nonterminal_wire_and_cannot_repeat(probe):
    output = [{"output": json.dumps({"native_failure_observation_received": True})}]
    sink = handler()
    with pytest.raises(Fault, match="SYNTHETIC_STREAM_INTERRUPTED"):
        probe.truncate(sink, "operation-1", "gpt-6-luna", output)
    raw = sink.wfile.getvalue()
    assert probe.injected == {"operation": "operation-1", "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest()}
    parser = ResponsesUsage("gpt-6-luna", "text/event-stream")
    parser.feed(raw)
    with pytest.raises(Fault, match="TRUNCATED_EVENT_STREAM"):
        parser.finish()
    with pytest.raises(Fault, match="GAME_FAILURE_TRIGGER"):
        probe.truncate(handler(), "operation-2", "gpt-6-luna", output)


@pytest.mark.parametrize("model,outputs", [("gpt-5.6-luna", {"native_failure_observation_received": True}),
    ("gpt-6-luna", []), ("gpt-6-luna", {"native_failure_observation_received": False})])
def test_fault_requires_target_model_and_observation_output(probe, model, outputs):
    sink = handler()
    with pytest.raises(Fault, match="GAME_FAILURE_TRIGGER"):
        probe.truncate(sink, "operation-1", model, outputs)
    assert not sink.wfile.getvalue() and probe.injected is None


def test_output_marker_decodes_native_wrapping_without_matching_prose():
    assert contains_observation({"output": 'log\n{"native_failure_observation_received":true}\n'})
    assert not contains_observation('text({native_failure_observation_received:true});')
    assert not contains_observation({"native_failure_observation_received": "true"})


def test_large_observation_produces_compact_parseable_acknowledgment(probe):
    script = "const run=Object.getPrototypeOf(async function(){}).constructor;\n" + (
        "const code=" + json.dumps(probe.code()) + ";\n" + r'''
const outputs=[], requests=[];
const observation={status:"ok",result:{is_example:false,observation_id:"observed-1",
  state:{connected:true,nearby_blocks:Array(2000).fill({block_id:"minecraft:stone"})}}};
await new run("ALL_TOOLS","tools","text","setTimeout",code)([{name:"fixture__game"}],
  {fixture__game:async({request})=>{requests.push(request);return {
    content:[{text:JSON.stringify(observation)}]};}}, v=>outputs.push(v), resolve=>resolve());
console.log(JSON.stringify({outputs,requests}));
''')
    result = subprocess.run([shutil.which("node"), "--input-type=module", "-e", script],
        capture_output=True, text=True, timeout=10, check=True)
    body = json.loads(result.stdout)
    assert body["outputs"] == [{"native_failure_observation_received": True,
        "observation_id": "observed-1", "connected": True}]
    assert len(json.dumps(body["outputs"])) < 200 and contains_observation(body["outputs"])
    assert [r["method"] for r in body["requests"]] == ["observe"]


@pytest.mark.parametrize("change", ["no-probe", "wrong-model", "no-oauth", "checkpoint", "recovery"])
def test_failure_mode_refuses_incompatible_profiles_before_materializing_output(probe, tmp_path, change):
    options = dict(broker_mode=True, admission_mode=True, bootstrap_mode=True, ingress_mode=True,
        oauth_mode=True, tool_projections={}, no_patch_catalog=tmp_path / "catalog.json",
        game_probe=probe, game_failure=True, model="gpt-6-luna")
    if change == "no-probe":
        options["game_probe"] = None
    elif change == "wrong-model":
        options["model"] = "gpt-5.6-luna"
    elif change == "no-oauth":
        options["oauth_mode"] = False
    else:
        options["game_retention" if change == "checkpoint" else "game_recovery"] = object()
    with pytest.raises(Fault, match="GAME_FAILURE_PROFILE_REQUIRED"):
        run(tmp_path / "unused.exe", tmp_path / "output", **options)
    assert not (tmp_path / "output").exists()
