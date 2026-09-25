"""Owned-canary attack surface for the pinned native root and clean helper.

Local scripted provider only. This records actual native outcomes, never issues
a RuntimeQualification and never targets real credentials or private game data.
"""

import hashlib
import json
import uuid

from mcbench.storage import canonical, require
from native_broker_canaries import Canaries

ACTORS = {"/root", "/root/identity_child"}
IO_GLOBALS = ("process", "require", "fetch", "Deno", "Bun", "WebSocket",
              "XMLHttpRequest", "Worker", "importScripts")
# Unknown host errors fail until independently inspected; absence of a marker
# alone is never proof that an attempted route was exercised and refused.
IMPORT_DENIALS = frozenset({"unsupported import in exec"})
CONSTRUCTOR_DENIALS = {"EvalError: Code generation from strings disallowed for this context"}


def inspect_boundary_outputs(outputs):
    """Deduplicate repeated context by caller/call ID without hiding conflicts."""
    unique, conflicts, malformed = {}, [], False
    for item in outputs:
        if not isinstance(item, dict) or item.get("native_agent") not in ACTORS or not isinstance(
                item.get("call_id"), str):
            malformed = True
            continue
        key = (item["native_agent"], item["call_id"])
        if key in unique and canonical(unique[key]) != canonical(item):
            conflicts.append(key)
        unique[key] = item
    probes = {}
    for item in unique.values():
        if not isinstance(item.get("output"), list):
            continue
        for chunk in item["output"]:
            try:
                value = json.loads(chunk.get("text", ""))
            except (AttributeError, TypeError, ValueError):
                continue
            if isinstance(value, dict) and str(value.get("probe", "")).startswith("boundary_"):
                probes.setdefault(value["probe"], []).append((item["native_agent"], value))

    def both(name, predicate):
        rows = probes.get("boundary_" + name, [])
        return len(rows) == 2 and {actor for actor, _ in rows} == ACTORS and all(
            set(value) in ({"probe", "result"}, {"probe", "error"}) and predicate(value)
            for _, value in rows)

    checks = {"boundary_outputs_consistent": not malformed and not conflicts,
              "boundary_io_globals_absent": both("globals", lambda p:
                  p.get("result") == dict.fromkeys(IO_GLOBALS, "undefined"))}
    for name in ("function_constructor", "host_constructor", "async_constructor"):
        checks["boundary_" + name] = both(name, lambda p:
            p.get("result") == "undefined" or p.get("error") in CONSTRUCTOR_DENIALS)
    for name in ("import_fs", "import_credentials", "import_process", "import_child_process",
                 "import_file", "import_http"):
        checks["boundary_" + name] = both(name, lambda p: p.get("error") in IMPORT_DENIALS)
    for name, code in {"absolute": "UNSAFE_PATH", "traversal": "UNSAFE_PATH",
                       "ads": "UNSAFE_PATH", "cas": "UNSAFE_PATH",
                       "foreign": "BROKER_FORBIDDEN"}.items():
        checks["boundary_artifact_" + name] = both("artifact_" + name, lambda p, code=code:
            p.get("result") == {"isError": True, "content": [{"type": "text", "text": code}]})
    return {"checks": checks, "probes": probes, "conflicts": conflicts}


class RuntimeBoundaryCanaries(Canaries):
    def __init__(self, output, **kwargs):
        super().__init__(output, **kwargs)
        self.module = output / "owned-private-module.mjs"
        self.secrets["module"] = "STRATA_PRIVATE_MODULE_" + uuid.uuid4().hex
        self.module.write_text("export default " + json.dumps(self.secrets["module"]) + ";\n",
                               encoding="utf-8")
        self.module_digest = hashlib.sha256(self.module.read_bytes()).hexdigest()

    def code(self, *, agent="/root"):
        require(agent in ACTORS, "CANARY_CALLER_REQUIRED")
        script = super().code(agent=agent)
        # All probes target this fixture's own private file/listener/environment.
        # Do not enumerate the operator process environment or actual accounts.
        probes = {
            "globals": "Object.fromEntries(" + json.dumps(IO_GLOBALS) +
                       ".map(k=>[k,typeof globalThis[k]]))",
            "function_constructor": "Function('return typeof process')()",
            "host_constructor": "text.constructor('return typeof process')()",
            "async_constructor": "(async()=>{}).constructor('return typeof process')()",
            "import_fs": "import('node:fs').then(m=>m.readFileSync(" +
                         json.dumps(str(self.protected)) + ",'utf8'))",
            "import_credentials": "import('node:fs').then(m=>m.readFileSync(" +
                         json.dumps(str(self.output / 'root-profile' / 'auth.json')) + ",'utf8'))",
            "import_process": "import('node:process').then(m=>m.env.TEMP)",
            "import_child_process": "import('node:child_process').then(m=>typeof m.spawn)",
            "import_file": "import(" + json.dumps(self.module.as_uri()) + ").then(m=>m.default)",
            "import_http": "import(" + json.dumps(self.url + "/unapproved-import.mjs") + ")",
        }
        for name, path in {
            "absolute": self.protected.as_posix(), "traversal": "../owned-private-canary.txt",
            "ads": "notes/root.md:private", "cas": "cas:sha256:" + self.original,
            "foreign": "results/advice.md" if agent == "/root" else "notes/root.md",
        }.items():
            probes["artifact_" + name] = "tools.mcp__strata_broker__artifact_read(" + json.dumps({"path": path}) + ")"
        for name, expression in probes.items():
            label = json.dumps("boundary_" + name)
            script += "\ntry { text({probe:" + label + ",result:await (" + expression + (
                ")}); } catch(e) { text({probe:" + label + ",error:String(e)}); }")
        return script

    def report(self, direct_calls, **kwargs):
        result = super().report(direct_calls, **kwargs)
        requests = [json.loads(p.read_bytes()) for p in self.output.glob("*-request.json")]
        outputs = []
        for request in requests:
            actor = json.loads(request["client_metadata"]["x-codex-turn-metadata"])["agent_name"]
            outputs.extend({**item, "native_agent": actor} for item in request.get("input", [])
                           if item.get("type") in {"custom_tool_call_output", "function_call_output"})
        observed = inspect_boundary_outputs(outputs)
        result["checks"].update(observed["checks"])
        result["boundary"] = observed
        all_inputs = canonical(requests)
        result["checks"].update({
            "boundary_private_module_unchanged": self.module.is_file() and
                hashlib.sha256(self.module.read_bytes()).hexdigest() == self.module_digest,
            "boundary_owned_secrets_not_in_requests": all(value.encode() not in all_inputs
                                                         for value in self.secrets.values()),
            "boundary_fake_oauth_not_in_requests": all(value not in all_inputs for value in (
                b"STRATA_SYNTHETIC_OAUTH_ACCESS", b"STRATA_SYNTHETIC_OAUTH_REFRESH")),
        })
        return result
