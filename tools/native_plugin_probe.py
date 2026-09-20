"""Credential-free pinned Dovetail catalog/read conformance on the actual CLI.

The deterministic provider requests one fixed read of an installed public skill.
This tests native loading/tool plumbing, not model reasoning, skill effectiveness,
helper isolation, or a production sandbox. Raw requests remain operator-private.
"""

import argparse
import json
import os
import re
import time
import traceback
from pathlib import Path

from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceDispatches
from mcbench.inventory import file_hash
from mcbench.native import NativeExec, NativeLaunch, native_argv
from mcbench.plugins import EXPLICIT_SKILLS, PLUGIN_ID, inspect_plugin_tree, install_dovetail
from mcbench.storage import CAS, Database, Fault, require
from native_dispatch_probe import (
    BINARY_SHA256,
    LocalProvider,
    close_budget,
    ledger,
    plan_for,
    put,
    sse,
    wait_job,
)


def text_content(body):
    """Only messages/tool outputs, never the echoed tool-call input itself."""
    values = []
    for item in body.get("input", []):
        if item.get("type") == "custom_tool_call_output":
            values.append(item.get("output", ""))
        elif item.get("type") == "message" or "content" in item:
            values.extend(c.get("text", "") for c in item.get("content", [])
                          if isinstance(c, dict))
    return "\n".join(v if isinstance(v, str) else json.dumps(v) for v in values)


def catalog_paths(body):
    """Expand the native catalog's observed root aliases before comparison."""
    text = text_content(body).replace("\\", "/")
    roots = dict(re.findall(r"^- `(r\d+)` = `([^`]+)`$", text, re.MULTILINE))
    paths = []
    for location in re.findall(r"\(file: ([^)\n]+)\)", text):
        alias, _, tail = location.partition("/")
        paths.append(roots[alias] + "/" + tail if alias in roots else location)
    return paths


class SkillProvider(LocalProvider):
    def __init__(self, *args, enabled, explicit=False, **kwargs):
        self.enabled = enabled
        self.explicit = explicit
        self.installed = None
        self.checks = {}
        super().__init__(*args, **kwargs)

    def respond(self, handler, body, index, operation):
        paths = [self.installed / relative for relative in self.inventory["skills"]
                 if relative not in EXPLICIT_SKILLS]
        if index == 0:
            # Match actual paths, not a model's claim that a skill exists.
            listed = [p.as_posix() in catalog_paths(body) for p in paths]
            self.checks["catalog_entries"] = sum(listed)
            require(all(listed) if self.enabled else not any(listed), "PLUGIN_CATALOG_MISMATCH")
            extras = [p for p in catalog_paths(body) if p.startswith(self.installed.as_posix() + "/")
                      and p not in [v.as_posix() for v in paths]]
            self.checks["unexpected_plugin_entries"] = extras
            require(not extras, "PLUGIN_FIXTURE_EXPOSED")
            if self.explicit:
                initial = text_content(body).replace("\r\n", "\n")
                loaded = [self.installed.joinpath(p).read_text(encoding="utf-8").strip() in initial
                          for p in EXPLICIT_SKILLS]
                self.checks["explicit_bodies_in_initial_request"] = sum(loaded)
                require(all(loaded), "EXPLICIT_SKILL_NOT_LOADED")
        else:
            require(self.enabled and index == 1, "UNEXPECTED_NATIVE_REQUEST")
            expected = self.skill.read_text(encoding="utf-8").replace("\r\n", "\n")
            # exec returns a structured JSON string; decode its output before checking.
            outputs = [i.get("output", "") for i in body.get("input", [])
                       if i.get("type") == "custom_tool_call_output"]
            decoded = []
            for output in outputs:
                chunks = [c.get("text", "") for c in output if c.get("type") == "input_text"] \
                    if isinstance(output, list) else [output]
                for chunk in chunks:
                    try:
                        parsed = json.loads(chunk)
                    except (ValueError, TypeError):
                        parsed = chunk
                    decoded.append(parsed.get("output", "") if isinstance(parsed, dict) else str(parsed))
            self.checks["exact_skill_body_returned"] = any(
                expected.strip() in v.replace("\r\n", "\n") for v in decoded)
            require(self.checks["exact_skill_body_returned"], "SKILL_BODY_NOT_RETURNED")
        event = "response-" + operation
        if self.enabled and index == 0:
            catalogs = [i["tools"] for i in body.get("input", [])
                        if i.get("type") == "additional_tools"]
            require(any(t.get("name") == "functions" and any(
                v.get("name") == "exec" and "tools.exec_command" in v.get("description", "")
                for v in t.get("tools", [])) for catalog in catalogs for t in catalog),
                "NATIVE_TOOL_MISSING")
            # PowerShell literal quoting, never JSON-as-shell escaping.
            literal = "'" + str(self.skill).replace("'", "''") + "'"
            command = "Get-Content -LiteralPath " + literal + " -Raw -Encoding UTF8"
            arguments = {"cmd": command, "login": False, "max_output_tokens": 10000}
            item = {"id": "tool-" + operation, "type": "custom_tool_call",
                    "call_id": "call-" + operation, "namespace": "functions", "name": "exec",
                    "input": "text(await tools.exec_command(" + json.dumps(arguments) + "));"}
        else:
            item = {"id": "message-" + operation, "type": "message", "role": "assistant",
                    "status": "completed", "content": [{"type": "output_text",
                    "text": "Synthetic plugin fixture complete.", "annotations": []}]}
        response = {"id": event, "object": "response", "created_at": 1, "status": "completed",
                    "model": body["model"], "output": [item], "usage": {
                        "input_tokens": 10, "output_tokens": 4, "total_tokens": 14,
                        "input_tokens_details": {"cached_tokens": 2},
                        "output_tokens_details": {"reasoning_tokens": 0}}}
        handler.response_started = True
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.end_headers()
        handler.wfile.write(sse("response.created", response={**response, "status": "in_progress",
                                                             "output": []}))
        handler.wfile.write(sse("response.output_item.done", output_index=0, item=item))
        handler.wfile.write(sse("response.completed", response=response))
        handler.wfile.flush()
        return {}, event  # Receipts come from the independent wire parser.


def run(binary, directory, *, enabled, explicit=False, read_generated_config=False):
    directory.mkdir()
    db = Database(directory / "synthetic.sqlite")
    cas = CAS(db, directory / "objects")
    runtime = NativeExec(db, cas, simulation=True)
    gate = InferenceDispatches(db, cas, simulation=True)
    limits = dict.fromkeys(DIMENSIONS, 1000000) | {"spend_microusd": 80000}
    gate.budgets.create_account("project", limits, "*")
    gate.budgets.create_account("a1", limits, "synthetic-campaign", "a1", "project",
                                category="development")
    provider = SkillProvider(db.path, cas.root, "plugin", enabled=enabled, explicit=explicit, wire=True)
    result = {"is_example": True, "real_usd": 0, "production_qualified": False,
              "plugin_enabled": enabled, "explicit_invocation": explicit,
              "read_generated_config": read_generated_config,
              "verdict": "fail"}
    try:
        plan = plan_for(binary, directory, provider, "root")
        profile = Path(plan.profile_directory)
        installation = install_dovetail(binary, profile)
        commands = json.loads((profile / "installation-commands.json").read_bytes())
        provider.installed = Path(json.loads(commands[-1]["stdout"])["installedPath"])
        provider.inventory = installation["inventory"]
        provider.skill = provider.installed / "skills/prompt-engineering/SKILL.md"
        overrides = installation["required_config_overrides"] | {
            "features.plugins": True,
            "windows.sandbox": "unelevated",
            f"plugins.{PLUGIN_ID}.enabled": enabled}
        plan = NativeLaunch.model_validate(plan.model_dump() | {
            "config_overrides": plan.config_overrides | overrides,
            "prompt": ("$dovetail-codex:spark-steering $dovetail-codex:upsum\n" if explicit else "") +
                      "Synthetic host conformance: load the public prompt-engineering skill "
                      "if available. Read only that skill; do not change files or run other commands."})
        provider.plan = plan
        price = put(cas, {"is_example": True, "real_usd": 0})
        reserve = ledger(plan, plan.operation_id, parent=None, calls=8, spend=80000,
                         pricing=price, inputs=800000, outputs=80000)
        fixture_argv = None
        if read_generated_config:
            fixture_argv = [a for a in native_argv(plan) if a != "--ignore-user-config"]
        runtime.start(plan, reserve, fixture_argv=fixture_argv)
        wait_job(runtime, plan)
    except Exception as error:
        (directory / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        result["failure"] = error.code if isinstance(error, Fault) else type(error).__name__
    finally:
        for job in list(runtime.live):
            runtime.interrupt(job, "probe_cleanup")
        provider.close()
    result["checks"] = provider.checks
    result["requests"] = provider.requests
    result["provider_errors"] = provider.errors
    if provider.installed:
        result["immutable_tree_after"] = inspect_plugin_tree(provider.installed)["installed_tree_digest"]
        result["immutable_tree_before"] = provider.inventory["installed_tree_digest"]
    try:
        result["runtime"] = runtime.status("root")
        result["closure"] = close_budget(runtime, plan, provider)
        result["budget"] = gate.budgets.status("project")
        count = 2 if enabled else 1
        require(not result.get("failure") and not provider.errors and
                result["runtime"]["returncode"] == 0 and
                result["budget"]["committed_and_reserved"]["model_calls"] == count and
                result["budget"]["committed_and_reserved"]["spend_microusd"] == count * 14 and
                result["immutable_tree_before"] == result["immutable_tree_after"], "PLUGIN_PROBE_FAILED")
        result["verdict"] = "pass"
    except Fault as error:
        result["validation_error"] = error.code
    db.export_journal(directory / "journal.jsonl")
    db.close()
    (directory / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--read-generated-config", action="store_true")
    parser.add_argument("--cases", nargs="+", choices=["enabled", "disabled", "explicit"],
                        default=["enabled", "disabled", "explicit"])
    args = parser.parse_args()
    require(os.name == "nt" and file_hash(args.codex) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    root, output = Path(__file__).resolve().parents[1], args.output.resolve()
    require(not output.is_relative_to(root) and not output.exists(), "PRIVATE_FRESH_OUTPUT_REQUIRED")
    output.mkdir(parents=True)
    sources = [Path(__file__).resolve(), root / "tools/native_dispatch_probe.py",
               *[root / "src/mcbench" / name for name in ("plugins.py", "native.py", "budgets.py",
                    "inference_dispatch.py", "inference_transport.py", "processes.py")]]
    manifest = {"schema": "strata/SyntheticNativePluginProbe/1", "is_example": True,
                "binary_sha256": BINARY_SHA256, "started_unix_ms": time.time_ns() // 1000000,
                "cases": args.cases, "read_generated_config": args.read_generated_config,
                "source_sha256": {p.relative_to(root).as_posix(): file_hash(p) for p in sources}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    results = []
    for case in args.cases:
        result = run(args.codex.resolve(), output / case, enabled=case != "disabled",
                     explicit=case == "explicit",
                     read_generated_config=args.read_generated_config)
        results.append(result)
        print(json.dumps({k: result.get(k) for k in (
            "plugin_enabled", "verdict", "checks", "failure", "validation_error", "provider_errors")}),
            flush=True)
    (output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    require(all(r["verdict"] == "pass" for r in results), "PROBE_FAILED")


if __name__ == "__main__":
    main()
