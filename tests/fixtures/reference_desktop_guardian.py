"""Private pair fixture with actual nested desktop/guardian Jobs; no Minecraft."""

import json
import os
from pathlib import Path
import time

from mcbench.desktop_process import DesktopApi, DesktopProcess
from mcbench.process_guard import AttachedJava, inspect_process
from strata_evaluator.reference_abort import ParticipantAbortGuard, failure_record
from strata_evaluator.reference_participant import ParticipantReady, publish, submit_completion

root = Path(__file__).parent
launch = json.loads((root / "launch.json").read_bytes())
config = json.loads((root / "desktop-config.json").read_bytes())
evidence = Path(launch["evidence_directory"])
ready = ParticipantReady.model_validate_json((evidence / "participant-ready.json").read_bytes())
abort = ParticipantAbortGuard(launch, evidence)
before = DesktopApi().input_name()
environment = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
marker = root / "late-effect"
child = guard = None
result = {"status": "fail", "synthetic": True, "scoring_eligible": False}
try:
    child = abort.start(lambda: DesktopProcess(
        [config["java"], "-cp", config["classpath"],
         "io.github.opencnid.strata.client.ProcessGuardFixture", "child", str(marker)],
        root, environment, max_wall_ms=2000))
    deadline = time.monotonic() + 1
    while not Path(str(marker) + ".ready").exists():
        abort.check()
        assert child.poll() is None and time.monotonic() < deadline
        time.sleep(.01)
    child.job.observe_members()
    guard = AttachedJava(inspect_process(child.pid), deadline=time.monotonic() + 1)
    # Keep the now-running chain observable to the independent outer monitor.
    time.sleep(.2)
    abort.check()
    guard.terminate()
    result["guardian_timing"] = guard.termination_timing
    result["inner_job"] = child.job.accounting()
    result["inner_members"] = child.job.member_status()
    assert child.poll() is not None and result["inner_job"]["active_processes"] == 0
    assert result["inner_members"]["signaled_processes"] == result["inner_job"]["total_processes"]
    assert not marker.exists()
    result["status"] = "pass"
except Exception as error:
    result["failure"] = failure_record("client_driver", error).model_dump()
finally:
    if guard:
        guard.close()
    result["abort_guard"] = abort.close()
    result["input_desktop_unchanged"] = DesktopApi().input_name() == before
    if (result["abort_guard"]["abort"] or result["abort_guard"]["cleanup_errors"]
            or not result["input_desktop_unchanged"]):
        result["status"] = "fail"
    report = Path(launch["participant"]["report_path"])
    publish(report, result)
    submit_completion(evidence, ready, report,
                      "completed" if result["status"] == "pass" else "failed")
raise SystemExit(0 if result["status"] == "pass" else 1)
