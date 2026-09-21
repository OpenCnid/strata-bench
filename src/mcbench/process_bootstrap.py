"""Trusted suspended-dispatch equivalent for managed process trees.

Launched with Python -I -S -B. Wait for the parent to attach the Windows job BEFORE
receiving the child command. This file is operator-owned, never an agent tool.
Only standard-library imports: no workspace or user site initialization.
"""

import json
import os
import subprocess
import sys
import threading


def main():
    raw = sys.stdin.buffer.readline(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024 or not raw.endswith(b"\n"):
        return 125
    plan = json.loads(raw)
    # No shell expansion; argument boundaries survive spaces, Unicode and quotes.
    child = subprocess.Popen(plan["argv"], cwd=plan["cwd"], env=plan["env"],
                             stdin=subprocess.PIPE, stdout=sys.stdout.buffer,
                             stderr=sys.stderr.buffer, shell=False)
    try:
        if plan.get("interactive", False):
            child.stdin.write(plan["prompt"].encode("utf-8"))
            child.stdin.flush()

            def forward():
                try:
                    for line in sys.stdin.buffer:
                        child.stdin.write(line)
                        child.stdin.flush()
                    child.stdin.close()
                except (BrokenPipeError, OSError, ValueError):
                    pass

            # EOF is optional for console servers. A stopped child ends the
            # bootstrap even if its parent has not closed the input pipe yet.
            threading.Thread(target=forward, daemon=True).start()
            result = child.wait()
            # The console reader can still block in buffered stdin. Interpreter
            # finalization must not race its lock (fatal on CPython/Windows).
            # Child stdout/stderr are inherited handles, not bootstrap buffers;
            # the owning parent still closes the Job Object and reaps descendants.
            os._exit(result)
        else:
            child.communicate(plan["prompt"].encode("utf-8"))
    except BaseException:
        child.kill()
        child.wait()
        raise
    return child.returncode


if __name__ == "__main__":
    raise SystemExit(main())
