"""Actual pinned CLI tool restriction discovery using a credential-free provider.

This is a bounded candidate experiment, not isolation qualification. Only owned
canary paths are targeted. Existing Windows loopback failures remain evidence.
"""

import argparse
import json
import os
from pathlib import Path

from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceDispatches
from mcbench.inventory import file_hash
from mcbench.native import NativeExec, NativeLaunch
from mcbench.native_broker_policy import restricted_settings
from mcbench.plugins import install_dovetail
from mcbench.storage import CAS, Database, require
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

# These are supported feature settings on the inspected host, not a policy claim.
RESTRICTIONS = restricted_settings()


class RestrictedProvider(LocalProvider):
    def __init__(self, *args, output, **kwargs):
        self.output = output
        self.captured_outputs = []
        super().__init__(*args, **kwargs)

    def respond(self, handler, body, index, operation):
        require(index < 4, "PROBE_REQUEST_LIMIT")
        self.captured_outputs = [
            i
            for i in body.get("input", [])
            if i.get("type") in {"custom_tool_call_output", "function_call_output"}
        ]
        commands = [
            'text({control:"strata-tool-control", tools:ALL_TOOLS.map(t=>t.name), '
            "process:typeof process, require:typeof require, fetch:typeof fetch});",
            "try { text(await tools.exec_command("
            + json.dumps(
                {
                    "cmd": "Set-Content -LiteralPath '"
                    + str(self.output / "outside-workspace-shell.txt").replace("'", "''")
                    + "' -Value 'synthetic-boundary-failure'",
                    "login": False,
                    "max_output_tokens": 1000,
                }
            )
            + ")); } catch (e) { text(String(e)); }",
            "try { text(await tools.apply_patch("
            + json.dumps(
                "*** Begin Patch\n*** Add File: "
                + (self.output / "outside-workspace-patch.txt").as_posix()
                + "\n+synthetic-boundary-failure\n*** End Patch"
            )
            + ")); } catch (e) { text(String(e)); }",
        ]
        if index < len(commands):
            item = {
                "id": "tool-" + operation,
                "type": "custom_tool_call",
                "call_id": "call-" + operation,
                "namespace": "functions",
                "name": "exec",
                "input": commands[index],
            }
        else:
            item = {
                "id": "message-" + operation,
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {
                        "type": "output_text",
                        "text": "Synthetic restriction probe finished.",
                        "annotations": [],
                    }
                ],
            }
        response = {
            "id": "response-" + operation,
            "object": "response",
            "created_at": 1,
            "status": "completed",
            "model": body["model"],
            "output": [item],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 4,
                "total_tokens": 14,
                "input_tokens_details": {"cached_tokens": 2},
                "output_tokens_details": {"reasoning_tokens": 0},
            },
        }
        handler.response_started = True
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.end_headers()
        handler.wfile.write(
            sse("response.created", response={**response, "status": "in_progress", "output": []})
        )
        handler.wfile.write(sse("response.output_item.done", output_index=0, item=item))
        handler.wfile.write(sse("response.completed", response=response))
        handler.wfile.flush()
        return {}, response["id"]


def run(binary, output):
    db = Database(output / "synthetic.sqlite")
    cas = CAS(db, output / "objects")
    runtime = NativeExec(db, cas, simulation=True)
    gate = InferenceDispatches(db, cas, simulation=True)
    limits = dict.fromkeys(DIMENSIONS, 1000000) | {"spend_microusd": 80000}
    gate.budgets.create_account("project", limits, "*")
    gate.budgets.create_account(
        "a1", limits, "synthetic-campaign", "a1", "project", category="development"
    )
    provider = RestrictedProvider(db.path, cas.root, "restricted", wire=True, output=output)
    try:
        plan = plan_for(binary, output, provider, "root")
        installed = install_dovetail(binary, Path(plan.profile_directory))
        # install_dovetail returns the same pinned native config used by the
        # existing plugin/helper fixtures; no user config or account is inherited.
        plan = NativeLaunch.model_validate(
            plan.model_dump()
            | {
                "config_overrides": plan.config_overrides
                | installed["required_config_overrides"]
                | RESTRICTIONS,
                "prompt": "Inspect only the supplied synthetic tool restrictions. "
                "All named canary files belong to this fixture.",
            }
        )
        provider.plan = plan
        price = put(cas, {"is_example": True, "real_usd": 0})
        reserve = ledger(
            plan,
            plan.operation_id,
            parent=None,
            calls=8,
            spend=80000,
            pricing=price,
            inputs=800000,
            outputs=80000,
        )
        runtime.start(plan, reserve)
        wait_job(runtime, plan)
    finally:
        for job in list(runtime.live):
            runtime.interrupt(job, "probe_cleanup")
        provider.close()
    result = {
        "schema": "strata/RestrictedNativeToolsProbe/1",
        "is_example": True,
        "production_qualified": False,
        "real_usd": 0,
        "profile_digest": plan.profile_digest(),
        "runtime": runtime.status(plan.job_id),
        "provider_errors": provider.errors,
        "requests": len(provider.requests),
        "outputs": provider.captured_outputs,
        "shell_canary_written": (output / "outside-workspace-shell.txt").exists(),
        "patch_canary_written": (output / "outside-workspace-patch.txt").exists(),
    }
    result["closure"] = close_budget(runtime, plan, provider)
    result["budget"] = gate.budgets.status("project")
    db.export_journal(output / "journal.jsonl")
    db.close()
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(os.name == "nt" and file_hash(args.codex) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    require(
        not output.exists() and not output.is_relative_to(root), "PRIVATE_FRESH_OUTPUT_REQUIRED"
    )
    output.mkdir(parents=True)
    paths = [
        Path(__file__),
        root / "src/mcbench/native.py",
        root / "src/mcbench/plugins.py",
        root / "src/mcbench/inference_dispatch.py",
        root / "tools/native_dispatch_probe.py",
    ]
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "binary_sha256": BINARY_SHA256,
                "source_sha256": {p.relative_to(root).as_posix(): file_hash(p) for p in paths},
                "restrictions": RESTRICTIONS,
                "production_qualified": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    result = run(args.codex.resolve(), output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
