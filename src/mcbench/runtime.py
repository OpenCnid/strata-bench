"""Read-only native-host inspection. This does not launch a model or certify a runtime."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

CODEX_VERSION = "codex-cli 0.154.0-alpha.6.2"
DOVETAIL_COMMIT = "15c306ccfef28eb5f616fadcd5fd8eac0663e361"
# Official rust-v0.154.0-alpha.6.2 Windows x64 release artifacts. The CLI
# executable alone does not contain its code-mode execution host.
CODEX_COMPANION_PINS = {
    "codex-code-mode-host.exe": "0dd178def204eca52efc690c86bbc2f66cce492b502587b89b12f2fe3bb4bc81",
    "codex-command-runner.exe": "7766665be04450649622771101425f4635b3f9adc37b669242ca4b9fbec78df1",
    "codex-windows-sandbox-setup.exe": "ffacc2a0010f6df93965758526bc2b9f4d92734853a3925964e18a1ab1bc6d35",
}


def native_companion_paths(executable):
    """Fail before game/native dispatch; never discover or substitute newer bytes."""
    from .inventory import file_hash
    from .storage import reject_links, require
    binary = Path(executable)
    require(binary.is_absolute(), "RUNTIME_PIN_MISMATCH")
    paths = []
    for name, expected in CODEX_COMPANION_PINS.items():
        path = binary.parent / name
        reject_links(path)
        require(path.is_file(), "NATIVE_COMPANION_MISSING")
        require(file_hash(path) == expected, "NATIVE_COMPANION_CHANGED")
        paths.append(path)
    return paths


def inspect_codex(executable: str | None = None) -> dict:
    binary = executable or shutil.which("codex")
    if binary is None:
        return {"status": "blocked", "code": "CAPABILITY_MISSING", "component": "codex"}
    path = Path(binary).resolve(strict=True)
    version = subprocess.run(
        [str(path), "--version"], capture_output=True, text=True, timeout=10, check=True
    ).stdout.strip()
    help_text = subprocess.run(
        [str(path), "exec", "--help"], capture_output=True, text=True, timeout=10, check=True
    ).stdout
    with path.open("rb") as stream:
        binary_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    flags = {
        flag: flag in help_text
        for flag in ("--json", "--ignore-user-config", "--ignore-rules", "--cd", "resume")
    }
    return {
        "status": "blocked",
        "code": "CAPABILITY_MISSING",
        "inference_started": False,
        "binary": {"version": version, "sha256": binary_digest},
        "version_matches_candidate": version == CODEX_VERSION,
        "exec_help_features": flags,
        "exec_help_sha256": hashlib.sha256(help_text.encode()).hexdigest(),
        "dovetail_candidate_commit": DOVETAIL_COMMIT,
        "unverified_required": [
            "native_plugin_load_and_invocation",
            "actual_exec_event_schema",
            "isolated_command_execution",
            "helper_filesystem_process_network_boundary",
            "root_and_descendant_all_call_accounting",
            "interrupt",
            "export_and_resume",
            "provider_credential_broker",
            "approved_inference_ceiling",
        ],
    }


class ExecUsageReader:
    """Documented JSONL usage observer, NOT all-call accounting or a runtime adapter.

    Source cursors identify ingestion, not calls. Identical actual events at different
    cursors still charge. Native turn totals alone never prove helper/retry coverage.
    """

    def __init__(self):
        self.events: dict[int, str] = {}
        self.totals = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
        self.completed_turns = 0

    def ingest(self, cursor: int, line: str) -> None:
        if type(cursor) is not int or cursor < 1:
            raise ValueError("OUT_OF_ORDER")
        fingerprint = hashlib.sha256(line.encode()).hexdigest()
        if cursor in self.events:
            if self.events[cursor] != fingerprint:
                raise ValueError("IDEMPOTENCY_CONFLICT")
            return
        if cursor != len(self.events) + 1:
            raise ValueError("OUT_OF_ORDER")
        event = json.loads(line)
        if not isinstance(event, dict) or event.get("type") not in {
            "thread.started",
            "turn.started",
            "turn.completed",
            "turn.failed",
            "error",
            "item.started",
            "item.updated",
            "item.completed",
        }:
            raise ValueError("SCHEMA_UNSUPPORTED")
        if event["type"] == "turn.completed":
            usage = event.get("usage")
            if not isinstance(usage, dict) or not set(self.totals) <= usage.keys():
                raise ValueError("METERING_UNAVAILABLE")
            for key in self.totals:
                if type(usage[key]) is not int or not 0 <= usage[key] <= 2**53 - 1:
                    raise ValueError("METERING_UNAVAILABLE")
            if usage["cached_input_tokens"] > usage["input_tokens"]:
                raise ValueError("METERING_UNAVAILABLE")
            for key in self.totals:
                self.totals[key] += usage[key]
            self.completed_turns += 1
        self.events[cursor] = fingerprint

    def report(self) -> dict:
        return {
            "scope": "documented_turn_totals_only",
            "usage": self.totals.copy(),
            "completed_turns": self.completed_turns,
            "model_calls": None,
            "spend_microusd": None,
            "all_call_accounting_verified": False,
        }
