"""Bounded operator graphics prerequisite probe; no Minecraft, input or screenshots.

Run only with the reviewed Java test classpath. The fixture is not bundled in the
client mod. A pass does not qualify full Minecraft, physical keys or isolation.
"""

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from mcbench import desktop_process
from mcbench.desktop_process import POLICY, DesktopApi, DesktopProcess
from mcbench.storage import Fault, canonical, reject_links, require


def run(java: Path, classpath_file: Path, output: Path):
    for path in (java, classpath_file, output):
        require(path.is_absolute(), "UNSAFE_PATH")
        reject_links(path)
    require(not output.exists(), "TARGET_EXISTS")
    require(java.is_file() and classpath_file.is_file(), "PREREQUISITE_MISSING")
    require(classpath_file.stat().st_size <= 131072, "CLASSPATH_QUOTA")
    classpath = classpath_file.read_text(encoding="utf-8").strip()
    require(classpath and "\n" not in classpath and "\r" not in classpath, "CLASSPATH_INVALID")
    artifacts = {}
    for raw in classpath.split(os.pathsep):
        path = Path(raw)
        require(path.is_absolute() and path.exists(), "CLASSPATH_INVALID")
        reject_links(path)
        if path.is_file() and (path.name.startswith("lwjgl") or path.name.startswith("gson")):
            artifacts[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    require(artifacts, "CLASSPATH_INVALID")
    fixture_class = Path(classpath.split(os.pathsep)[0]) / "io/github/opencnid/strata/client/DesktopRenderFixture.class"
    reject_links(fixture_class)
    require(fixture_class.is_file(), "RENDER_FIXTURE_MISSING")
    output.mkdir(parents=True)
    result_file = output / "renderer.json"
    argfile = output / "java-args.txt"
    args = ["-Xmx128m", "-cp", classpath,
            "io.github.opencnid.strata.client.DesktopRenderFixture", str(result_file)]
    argfile.write_text("\n".join('"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
                                  for value in args), encoding="utf-8")
    evidence = {"schema": "strata/DesktopRenderProbe/1", "classification": "disposable-graphics-prerequisite",
                "launch_policy": POLICY,
                "minecraft": False, "campaign_admission": False, "physical_input": False,
                "credential_isolation_verified": False, "max_wall_ms": 30000,
                "java_sha256": hashlib.sha256(java.read_bytes()).hexdigest(), "artifacts": artifacts,
                "launcher_sha256": hashlib.sha256(Path(desktop_process.__file__).read_bytes()).hexdigest(),
                "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "fixture_class_sha256": hashlib.sha256(fixture_class.read_bytes()).hexdigest(),
                "classpath_sha256": hashlib.sha256(classpath_file.read_bytes()).hexdigest(),
                "status": "fail", "started_unix_ms": time.time_ns() // 1_000_000}
    try:
        before = DesktopApi().input_name()
        env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
        with DesktopProcess([str(java), "@" + str(argfile)], output, env, max_wall_ms=30000) as process:
            evidence["desktop"] = process.name
            evidence["pid"] = process.pid
            evidence["exit_code"] = process.wait(35)
            evidence["stop_reason"] = process.reason
        evidence["input_desktop_unchanged"] = DesktopApi().input_name() == before
        require(evidence["exit_code"] == 0 and evidence["stop_reason"] is None
                and evidence["input_desktop_unchanged"], "RENDER_PROCESS_FAILED")
        require(result_file.is_file() and result_file.stat().st_size <= 32768, "RENDER_EVIDENCE_MISSING")
        result = json.loads(result_file.read_text(encoding="utf-8"))
        evidence["renderer"] = result
        require(result.get("schema") == "strata/DesktopRenderFixture/1"
                and result.get("status") == "pass" and result.get("minecraft") is False
                and result.get("visible") is False and result.get("frames") == 20
                and result.get("red_samples") == [64, 191] * 10, "RENDER_PROBE_FAILED")
        evidence["status"] = "pass"
    except (Fault, OSError, ValueError) as error:
        evidence["error_code"] = error.code if isinstance(error, Fault) else "RENDER_PROBE_FAILED"
    finally:
        evidence["ended_unix_ms"] = time.time_ns() // 1_000_000
        (output / "probe.json").write_bytes(canonical(evidence) + b"\n")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", required=True, type=Path)
    parser.add_argument("--classpath-file", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    args = parser.parse_args()
    try:
        value = run(args.java, args.classpath_file, args.output_directory)
    except (Fault, OSError, ValueError) as error:
        print(json.dumps({"status": "blocked", "minecraft": False, "campaign_admission": False,
                          "error_code": error.code if isinstance(error, Fault) else "RENDER_PREFLIGHT_FAILED"}))
        return 2
    print(json.dumps({key: value[key] for key in ("status", "minecraft", "campaign_admission")}
                     | {"error_code": value.get("error_code"), "evidence": str(args.output_directory / "probe.json")}))
    return 0 if value["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
