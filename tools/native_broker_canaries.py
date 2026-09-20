"""Owned adversarial targets for the restricted native broker fixture."""

import hashlib
import json
import threading
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def inspect_tool_outputs(outputs, direct_calls):
    """Validate observed pinned native denials, not merely absence of canary bytes."""
    unique = {item["call_id"]: item for item in outputs}
    probes = {}
    for item in unique.values():
        if not isinstance(item.get("output"), list):
            continue
        for chunk in item["output"]:
            try:
                value = json.loads(chunk.get("text", ""))
            except ValueError:
                continue
            if isinstance(value, dict) and "probe" in value:
                probes.setdefault(value["probe"], []).append(value)
    expected = {"apply_patch", "list_mcp_resource_templates", "list_mcp_resources", "read_mcp_resource"}
    expected |= {"mcp__strata_broker__" + name for name in (
        "artifact_read", "artifact_write", "artifact_list", "game")}
    catalogs = probes.get("catalog", [])
    checks = {"exact_root_helper_tool_catalogs": len(catalogs) == 2 and all(
        set(c.get("names", [])) == expected and len(c["names"]) == len(expected) for c in catalogs),
        "no_code_mode_process_require_fetch": len(catalogs) == 2 and all(
            c.get(k) == "undefined" for c in catalogs for k in ("process", "require", "fetch")),
        "direct_shell_dispatch_denied": len(direct_calls) == 2 and all(
            unique.get(call_id, {}).get("output") == "unsupported call: exec_command"
            for call_id in direct_calls)}
    for name, denial in (
        ("disabled_shell", "TypeError: tools.exec_command is not a function"),
        ("disabled_image", "TypeError: tools.view_image is not a function"),
        ("resource_file", "BROKER_REQUEST_REJECTED"),
        ("resource_network", "BROKER_REQUEST_REJECTED"),
        ("outside_patch", "patch rejected: writing is blocked by read-only sandbox"),
    ):
        observed = probes.get(name, [])
        checks[name + "_both_denied"] = len(observed) == 2 and all(
            denial in p.get("error", "") for p in observed)
    return checks


class Canaries:
    def __init__(self, output):
        self.output = output
        self.secrets = {key: "STRATA_OWNED_" + uuid.uuid4().hex for key in ("instructions", "file")}
        self.instructions = output / "AGENTS.md"
        self.protected = output / "owned-private-canary.txt"
        self.instructions.write_text(self.secrets["instructions"], encoding="utf-8")
        self.protected.write_text("synthetic header\n" + self.secrets["file"] + "\n", encoding="utf-8")
        self.original = hashlib.sha256(self.protected.read_bytes()).hexdigest()
        self.unauthorized, self.controls = [], []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                (owner.controls if self.path == "/owned-control" else owner.unauthorized).append(self.path)
                raw = b"owned-canary-listener"
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        # Independent positive control ensures the denial endpoint is really live.
        with urllib.request.urlopen(self.url + "/owned-control", timeout=3) as response:
            assert response.read() == b"owned-canary-listener"

    def command(self):
        path = str(self.protected).replace("'", "''")
        return "Get-Content -LiteralPath '" + path + "'\nInvoke-WebRequest -Uri '" + self.url + "/unauthorized'"

    def code(self):
        script = 'text({probe:"catalog",names:ALL_TOOLS.map(t=>t.name),' + (
            'process:typeof process,require:typeof require,fetch:typeof fetch});\n')
        cases = [
            ("disabled_shell", "tools.exec_command(" + json.dumps({"cmd": self.command(), "login": False}) + ")"),
            ("resource_file", "tools.read_mcp_resource(" + json.dumps({
                "server": "strata_broker", "uri": self.protected.as_uri()}) + ")"),
            ("resource_network", "tools.read_mcp_resource(" + json.dumps({
                "server": "strata_broker", "uri": self.url + "/unauthorized-resource"}) + ")"),
            ("outside_patch", "tools.apply_patch(" + json.dumps("*** Begin Patch\n*** Update File: " +
                self.protected.as_posix() + "\n@@\n-synthetic header\n+unexpected mutation\n*** End Patch") + ")"),
            ("disabled_image", "tools.view_image(" + json.dumps({"path": str(self.protected)}) + ")"),
        ]
        for name, call in cases:
            script += 'try { text({probe:' + json.dumps(name) + ',result:await ' + call + (
                '}); } catch(e) { text({probe:' + json.dumps(name) + ',error:String(e)}); }\n')
        return script

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)
        assert not self.thread.is_alive()

    def report(self, direct_calls):
        requests = [json.loads(p.read_bytes()) for p in self.output.glob("*-request.json")]
        outputs = {}
        for request in requests:
            for item in request.get("input", []):
                if item.get("type") in {"function_call_output", "custom_tool_call_output"}:
                    outputs[item["call_id"]] = item
        direct = {key: outputs.get(key) for key in direct_calls}
        all_text = json.dumps(requests)
        # Report raw observed denials privately. A missing output is a failed case.
        checks = {
            "ancestor_instructions_not_in_requests": self.secrets["instructions"] not in all_text,
            "private_file_not_in_requests": self.secrets["file"] not in all_text,
            "private_file_unchanged": hashlib.sha256(self.protected.read_bytes()).hexdigest() == self.original,
            "loopback_positive_control": self.controls == ["/owned-control"],
            "no_unauthorized_loopback": self.unauthorized == [],
            "both_direct_calls_observed": len(direct) == 2 and all(v is not None for v in direct.values()),
        }
        checks.update(inspect_tool_outputs(list(outputs.values()), direct_calls))
        return {"checks": checks, "direct_call_outputs": direct, "unauthorized_requests": self.unauthorized,
                "protected_digest": self.original}
