"""Non-model Windows writer canary using existing Codex sandbox enrollment.

Only newly owned fixture paths are accessed. Does not launch Minecraft, change
accounts/firewall, read sandbox credentials or issue a qualification certificate.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import threading
import time

from mcbench.inventory import file_hash
from mcbench.native import _toml_value
from mcbench.processes import ManagedProcess
from mcbench.storage import require
from strata_evaluator.craft_reference import private_path, write_new
from strata_evaluator.windows_writer import WindowsSecurity, WriterTree
from native_dispatch_probe import BINARY_SHA256


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def native_writer(binary, workspace, sandbox_home, writer_sid, *, prepare=False, diagnostic=None,
                  access_fixture=None, diagnostic_target=None):
    require(file_hash(binary) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    # Setup metadata only. Never open .sandbox-secrets or account auth caches.
    marker = json.loads((sandbox_home / ".sandbox/setup_marker.json").read_bytes())
    require(marker.get("version") == 5, "SANDBOX_ENROLLMENT_REQUIRED")
    native = Path(os.environ["SystemRoot"]) / "System32"
    world = workspace / "guarded/world"
    level = world / "level.dat"
    command = [
        "$ErrorActionPreference='Stop'",
        "$observed = & " + literal(native / "whoami.exe") + " /user /fo csv /nh",
        "$identity = $observed | ConvertFrom-Csv -Header 'name','sid'",
        "if ($identity.sid -ne " + literal(writer_sid) + ") { throw 'WRITER_IDENTITY_MISMATCH' }"]
    command += (["[ordered]@{writer_sid=$identity.sid} | ConvertTo-Json -Compress"] if prepare else [
        "New-Item -ItemType Directory -Path " + literal(world) + " | Out-Null",
        "Set-Content -LiteralPath " + literal(level) + " -Value 'synthetic-writer' -Encoding UTF8",
        "Rename-Item -LiteralPath " + literal(level) + " -NewName 'level-next.dat'",
        "Rename-Item -LiteralPath " + literal(world / "level-next.dat") + " -NewName 'level.dat'",
        "$text = Get-Content -LiteralPath " + literal(level) + " -Raw -Encoding UTF8",
        "if ($text.Trim() -ne 'synthetic-writer') { throw 'WRITER_CONTENT_MISMATCH' }",
        "[ordered]@{writer_sid=$identity.sid;write=$true;rename=$true;read=$true} | ConvertTo-Json -Compress",
    ])
    if access_fixture is not None:
        # Exercise the actual Windows API, not PowerShell's Rename-Item path
        # handling/permissions. The separately retained PowerShell failure is
        # not relabelled as a successful Rename-Item test.
        command = command[:6] + [
            "& " + literal(access_fixture) + " " + literal(level),
            "if ($LASTEXITCODE -ne 0) { throw 'WRITER_ACCESS_FIXTURE_FAILED' }",
            "[ordered]@{writer_sid=$identity.sid;write=$true;rename=$true;read=$true} | ConvertTo-Json -Compress",
        ]
    if diagnostic is not None:
        command = ["& " + literal(diagnostic) + " " + literal(diagnostic_target or level),
                   "exit $LASTEXITCODE"]
    settings = {"windows.sandbox": "elevated", "default_permissions": "strata-writer-fixture",
        "permissions.strata-writer-fixture.filesystem": {
            ":root": "deny", ":minimal": "read", ":workspace_roots": {".": "write"}},
        "permissions.strata-writer-fixture.network.enabled": False}
    argv = [str(binary), "sandbox", "--include-managed-config", "--permission-profile",
            "strata-writer-fixture", "--cd", str(workspace)]
    for key, value in sorted(settings.items()):
        argv.extend(["-c", key + "=" + _toml_value(value)])
    argv.extend(["--", str(native / "WindowsPowerShell/v1.0/powershell.exe"),
                 "-NoProfile", "-Command", "\n".join(command)])
    env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
    env["CODEX_HOME"] = str(sandbox_home)
    process = ManagedProcess(argv, workspace, env, "")
    captured = {}
    readers = [threading.Thread(target=lambda name, stream: captured.update({name: stream.read(65537)}),
        args=(name, stream), daemon=True) for name, stream in (
            ("stdout", process.process.stdout), ("stderr", process.process.stderr))]
    try:
        for reader in readers:
            reader.start()
        until = time.monotonic() + 20
        while process.poll() is None and time.monotonic() < until:
            time.sleep(0.025)
        timed_out = process.poll() is None
        if timed_out:
            process.terminate()
        for reader in readers:
            reader.join(3)
        require(not any(reader.is_alive() for reader in readers), "WRITER_CAPTURE_UNCERTAIN")
        require(all(len(value) <= 65536 for value in captured.values()), "WRITER_CAPTURE_QUOTA")
        return {"exit_code": process.poll(), "timed_out": timed_out, **{
            key: value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
            for key, value in captured.items()}}
    finally:
        process.close()


def run(binary, output, sandbox_home, writer_sid, access_fixture, *, sibling_control=False):
    output = private_path(output)
    require(not output.exists(), "WRITER_OUTPUT_EXISTS")
    output.mkdir(parents=True)
    workspace = output / "workspace"
    workspace.mkdir()
    require(access_fixture.is_file() and access_fixture.stat().st_size <= 1024**2,
            "WRITER_FIXTURE_INVALID")
    fixture = workspace / "writer-access.exe"
    shutil.copyfile(access_fixture, fixture)
    result = {"schema": "strata/PrivateWriterCanary/1", "is_example": True,
              "model_calls": 0, "game_launched": False, "scoring_eligible": False,
              "production_qualified": False, "verdict": "fail", "checks": {}}
    result["fixture_sha256"] = file_hash(fixture)
    checks = result["checks"]
    try:
        preparation = native_writer(binary, workspace, sandbox_home, writer_sid, prepare=True)
        write_new(output / "enrollment.json", preparation)
        require(preparation["exit_code"] == 0 and not preparation["timed_out"]
                and json.loads(preparation["stdout"]) == {"writer_sid": writer_sid},
                "WRITER_ENROLLMENT_FAILED")
        group_sid, scope_sid = WindowsSecurity().workspace_scope(workspace)
        with WriterTree(workspace / "guarded", writer_sid, group_sid, scope_sid) as tree:
            result["native"] = native_writer(binary, workspace, sandbox_home, writer_sid,
                                               access_fixture=fixture)
            write_new(output / "native.json", result["native"])
            require(result["native"]["exit_code"] == 0 and not result["native"]["timed_out"],
                    "WRITER_NATIVE_FAILED")
            observed = json.loads(result["native"]["stdout"].splitlines()[-1])
            require(observed == {"writer_sid": writer_sid, "write": True,
                                 "rename": True, "read": True}, "WRITER_NATIVE_FAILED")
            checks["separate_writer_read_write_rename"] = True
            lines = result["native"]["stdout"].splitlines()
            checks["native_token_scope_observed"] = (f"user={writer_sid}" in lines
                and f"token_11={scope_sid}" in lines and f"token_11={group_sid}" not in lines)
            tree.verify()  # Sandbox setup must not weaken the root descriptor.
            for path, directory in [(tree.path / "world", True), (tree.path / "world/level.dat", False)]:
                tree.security.verify(path, writer_sid, group_sid, scope_sid, directory=directory)
            checks["root_and_inherited_acls_exact"] = True
            level = tree.path / "world/level.dat"
            initial = level.read_bytes()
            denied = {
                "same_user_overwrite_denied": lambda: level.write_bytes(b"invalid"),
                "same_user_create_denied": lambda: (tree.path / "unauthorized").write_bytes(b"invalid"),
                "same_user_delete_denied": level.unlink,
                "same_user_rename_denied": lambda: level.rename(level.with_name("stolen")),
                "held_root_replace_denied": lambda: tree.path.rename(workspace / "stolen"),
            }
            for name, action in denied.items():
                try:
                    action()
                except PermissionError:
                    checks[name] = True
                else:
                    checks[name] = False
            checks["bytes_unchanged_after_denials"] = level.read_bytes() == initial
            if sibling_control:
                sibling = output / "sibling-workspace"
                sibling.mkdir()
                sibling_fixture = sibling / "writer-access.exe"
                shutil.copyfile(fixture, sibling_fixture)
                # A different native permission root, but the same enrolled
                # account. This must not be confused with a distinct principal.
                sibling_result = native_writer(binary, sibling, sandbox_home, writer_sid,
                    diagnostic=sibling_fixture, diagnostic_target=level)
                write_new(output / "sibling.json", sibling_result)
                # Only explicit OS ACCESS_DENIED for the read/write/delete
                # attempts can count; startup/fixture/timeout failures cannot.
                sibling_lines = sibling_result["stdout"].splitlines()
                bound_sibling = (not sibling_result["timed_out"]
                    and sibling_result["exit_code"] in {0, 4}
                    and f"user={writer_sid}" in sibling_lines
                    and f"token_11={scope_sid}" not in sibling_lines)
                checks["same_account_sibling_write_delete_denied"] = (bound_sibling and all(
                    f"access_{access}=5" in sibling_lines for access in (0x40000000, 0x10000)))
                checks["same_account_sibling_read_denied"] = (
                    bound_sibling and "access_2147483648=5" in sibling_lines)
                checks["bytes_unchanged_after_sibling"] = level.read_bytes() == initial
            result["verdict"] = "pass" if all(checks.values()) else "fail"
        # Closing authority must not reset the persisted write restrictions.
        tree.security.verify(tree.path, writer_sid, group_sid, scope_sid, directory=True, root=True)
        try:
            level.write_bytes(b"invalid-after-close")
        except PermissionError:
            checks["close_preserves_write_denial"] = True
        else:
            checks["close_preserves_write_denial"] = False
        result["verdict"] = "pass" if all(checks.values()) else "fail"
    except Exception as exc:
        result["error"] = getattr(exc, "code", type(exc).__name__)
        raise
    finally:
        write_new(output / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sandbox-home", type=Path, required=True)
    parser.add_argument("--writer-sid", required=True)
    parser.add_argument("--access-fixture", type=Path, required=True,
                        help="Compiled tests/fixtures/writer_access.cs; synthetic native operations only")
    parser.add_argument("--sibling-control", action="store_true")
    args = parser.parse_args()
    report = run(args.codex, args.output, args.sandbox_home, args.writer_sid, args.access_fixture,
                 sibling_control=args.sibling_control)
    print(json.dumps({"verdict": report["verdict"], "checks": report["checks"], "model_calls": 0}))
    raise SystemExit(0 if report["verdict"] == "pass" else 1)
