"""Credential-free native collaboration conformance; synthetic output only.

Separate from the fixture that runs two independent CLI jobs. No production
helper isolation or per-helper usage attribution is inferred from discovery.
"""

import argparse
import json
import os
import time
import traceback
from pathlib import Path

from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceDispatches
from mcbench.inventory import file_hash
from mcbench.native import NativeExec, NativeLaunch
from mcbench.plugins import install_dovetail, inspect_plugin_tree
from mcbench.storage import CAS, Database, Fault, require
from native_dispatch_probe import (
    BINARY_SHA256, MODEL, LocalProvider, close_budget, ledger, plan_for, put, sse, wait_job,
)

PARENT_CANARY = "STRATA_PARENT_CONTEXT_4c57dca8"
CHILD_RESULT = "STRATA_CHILD_RESULT_88ab269e"


class HelperProvider(LocalProvider):
    def __init__(self, *args, mode, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog = []
        self.mode, self.lineage, self.root_step = mode, [], 0
        self.child_seen = False

    def respond(self, handler, body, index, operation):
        catalogs = [item["tools"] for item in body.get("input", [])
                    if item.get("type") == "additional_tools"]
        if index == 0:
            self.catalog = [tool for catalog in catalogs for tool in catalog]
        if self.mode == "discovery":
            return super().respond(handler, body, index, operation)
        require("spawn_agent" in json.dumps(self.catalog), "NATIVE_HELPER_TOOL_MISSING")
        metadata = json.loads(body["client_metadata"]["x-codex-turn-metadata"])
        agent = metadata["agent_name"]
        require(agent in {"/root", "/root/synthetic_child"}, "UNEXPECTED_NATIVE_AGENT")
        text = "Synthetic native parent complete."
        call = None
        with self.lock:
            self.lineage.append({"operation_id": operation, "agent_name": agent,
                "thread_id": metadata["thread_id"], "turn_id": metadata["turn_id"],
                "root_turn_id": metadata["root_turn_id"],
                "parent_canary_present": PARENT_CANARY in json.dumps(body), "model": body["model"]})
            if agent != "/root":
                require(not self.child_seen, "UNEXPECTED_HELPER_RETRY")
                require((PARENT_CANARY in json.dumps(body)) == (self.mode == "fork_all"),
                        "HELPER_FORK_CONTEXT_MISMATCH")
                self.child_seen = True
                text = CHILD_RESULT
            else:
                step = self.root_step
                self.root_step += 1
                if step == 0:
                    call = ("spawn_agent", {"task_name": "synthetic_child",
                        "fork_turns": "all" if self.mode == "fork_all" else "none",
                        "message": "Return " + CHILD_RESULT + ". This is a bounded synthetic fixture. "
                            "Do not call tools or read/write files."})
                elif step == 1:
                    call = ("wait_agent", {"timeout_ms": 10000})
                else:
                    delivered = any(item.get("type") == "agent_message" and
                        item.get("author") == "/root/synthetic_child" and item.get("recipient") == "/root" and
                        any(part.get("text", "").endswith("Payload:\n" + CHILD_RESULT) and
                            part["text"].startswith("Message Type: FINAL_ANSWER\n")
                            for part in item.get("content", [])) for item in body.get("input", []))
                    require(self.child_seen and delivered, "HELPER_RESULT_NOT_DELIVERED")
        event = "response-" + operation
        item = {"id": "message-" + operation, "type": "message", "role": "assistant",
                "status": "completed", "content": [{"type": "output_text", "text": text, "annotations": []}]}
        if call:
            item = {"id": "tool-" + operation, "type": "function_call", "call_id": "call-" + operation,
                    "namespace": "collaboration", "name": call[0], "arguments": json.dumps(call[1])}
        response = {"id": event, "object": "response", "created_at": 1, "status": "completed",
                    "model": MODEL, "output": [item], "usage": {
                        "input_tokens": 10, "output_tokens": 4, "total_tokens": 14,
                        "input_tokens_details": {"cached_tokens": 2},
                        "output_tokens_details": {"reasoning_tokens": 0}}}
        handler.response_started = True
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.end_headers()
        handler.wfile.write(sse("response.created", response={**response, "status": "in_progress", "output": []}))
        handler.wfile.write(sse("response.output_item.done", output_index=0, item=item))
        handler.wfile.write(sse("response.completed", response=response))
        handler.wfile.flush()
        return {}, event


def run(binary, output, variant, mode, persistent):
    db = Database(output / "synthetic.sqlite")
    cas = CAS(db, output / "objects")
    runtime = NativeExec(db, cas, simulation=True)
    gate = InferenceDispatches(db, cas, simulation=True)
    limits = dict.fromkeys(DIMENSIONS, 1000000) | {"spend_microusd": 80000}
    gate.budgets.create_account("project", limits, "*")
    gate.budgets.create_account("a1", limits, "synthetic-campaign", "a1", "project",
                                category="development")
    provider = HelperProvider(db.path, cas.root, "success", wire=True, mode=mode)
    result = {"is_example": True, "real_usd": 0, "production_qualified": False,
              "verdict": "fail", "mode": mode, "variant": variant, "ephemeral": not persistent}
    installed = None
    try:
        plan = plan_for(binary, output, provider, "root")
        installation = install_dovetail(binary, Path(plan.profile_directory))
        commands = json.loads((Path(plan.profile_directory) / "installation-commands.json").read_bytes())
        installed = Path(json.loads(commands[-1]["stdout"])["installedPath"])
        result["plugin_tree_before"] = installation["inventory"]["installed_tree_digest"]
        overrides = {"features.multi_agent": True, "windows.sandbox": "unelevated"}
        if variant in {"agents", "v2"}:
            overrides.update({"agents.enabled": True, "agents.max_concurrent_threads_per_session": 1,
                              "agents.default_subagent_model": MODEL})
        if variant == "v2":
            overrides["features.multi_agent_v2"] = True
        plan = NativeLaunch.model_validate(plan.model_dump() | {
            "session_storage": "private_profile" if persistent else "ephemeral",
            "config_overrides": plan.config_overrides | installation["required_config_overrides"] |
                overrides,
            "prompt": ("Synthetic native helper conformance. Delegate only the fixed child task and "
                "wait for its result while retaining this synthetic parent context: " + PARENT_CANARY +
                ". Do not execute shell commands or access files." if mode != "discovery" else
                "Synthetic native helper discovery. Return a brief result; do not access files.")})
        provider.plan = plan
        price = put(cas, {"is_example": True, "real_usd": 0})
        reserve = ledger(plan, plan.operation_id, parent=None, calls=8, spend=80000,
                         pricing=price, inputs=800000, outputs=80000)
        runtime.start(plan, reserve)
        wait_job(runtime, plan)
    except Exception as error:
        (output / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        result["failure"] = error.code if isinstance(error, Fault) else type(error).__name__
    finally:
        for job in list(runtime.live):
            runtime.interrupt(job, "probe_cleanup")
        provider.close()
    (output / "native-tools.json").write_text(json.dumps(provider.catalog, indent=2), encoding="utf-8")
    result["tool_names"] = {namespace.get("name"): [tool.get("name") for tool in namespace.get("tools", [])]
                            for namespace in provider.catalog}
    result["helper_tools_advertised"] = "spawn_agent" in json.dumps(provider.catalog)
    result["helper_qualification"] = "not_run" if result["helper_tools_advertised"] else "blocked"
    result["requests"], result["provider_errors"] = provider.requests, provider.errors
    result["lineage"] = provider.lineage
    if installed:
        result["plugin_tree_after"] = inspect_plugin_tree(installed)["installed_tree_digest"]
    try:
        result["runtime"] = runtime.status("root")
        result["closure"] = close_budget(runtime, plan, provider)
        result["budget"] = gate.budgets.status("project")
        result["turn_usage"] = runtime.usage_report("root")
        if mode != "discovery":
            roots = [item for item in provider.lineage if item["agent_name"] == "/root"]
            children = [item for item in provider.lineage if item["agent_name"] != "/root"]
            require(len(roots) == 3 and len(children) == 1 and
                    roots[0]["thread_id"] != children[0]["thread_id"] and
                    {item["root_turn_id"] for item in provider.lineage} == {roots[0]["turn_id"]},
                    "NATIVE_HELPER_LINEAGE_MISMATCH")
        require(not result.get("failure") and not provider.errors and
                result["runtime"]["returncode"] == 0 and
                result["budget"]["committed_and_reserved"]["model_calls"] == (1 if mode == "discovery" else 4) and
                all(item.get("receipt_deduplicated") for item in provider.requests) and
                result["plugin_tree_after"] == result["plugin_tree_before"], "NATIVE_HELPER_PROBE_FAILED")
        result["verdict"] = "pass"
    except Fault as error:
        result["validation_error"] = error.code
    db.export_journal(output / "journal.jsonl")
    db.close()
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=["feature", "agents", "v2"], default="feature")
    parser.add_argument("--mode", choices=["discovery", "fork_none", "fork_all"], default="discovery")
    parser.add_argument("--persistent", action="store_true", help="Keep fixture session in its private disposable profile")
    args = parser.parse_args()
    root, output = Path(__file__).resolve().parents[1], args.output.resolve()
    require(os.name == "nt" and file_hash(args.codex) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    require(not output.is_relative_to(root) and not output.exists(), "PRIVATE_FRESH_OUTPUT_REQUIRED")
    output.mkdir(parents=True)
    sources = [Path(__file__).resolve(), root / "tools/native_dispatch_probe.py",
               *[root / "src/mcbench" / name for name in ("plugins.py", "native.py", "budgets.py",
                    "inference_dispatch.py", "inference_transport.py", "processes.py")]]
    manifest = {"schema": "strata/SyntheticNativeHelperProbe/1", "is_example": True,
                "variant": args.variant, "mode": args.mode, "ephemeral": not args.persistent,
                "binary_sha256": BINARY_SHA256, "started_unix_ms": time.time_ns() // 1000000,
                "source_sha256": {p.relative_to(root).as_posix(): file_hash(p) for p in sources}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    result = run(args.codex.resolve(), output, args.variant, args.mode, args.persistent)
    print(json.dumps({k: result.get(k) for k in (
        "verdict", "variant", "tool_names", "helper_tools_advertised", "helper_qualification",
        "failure", "validation_error", "provider_errors")}), flush=True)
    require(result["verdict"] == "pass", "PROBE_FAILED")


if __name__ == "__main__":
    main()
