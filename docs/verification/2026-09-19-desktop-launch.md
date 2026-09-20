# Non-input desktop launch and graphics prerequisite — September 19, 2026

Operator-only. No gameplay workspace, tool or helper may receive this report,
the launcher, probe command, arguments, private evidence or account material.

M0.3b.2c.3c.1 is **implemented_unverified** for production use. SPEC v0.2.26,
launch policy `windows-noninput-desktop-suspended-job/1`. This addresses the user's
need to keep using their computer while Strata is developed and tested.
The existing Forge minor-33 client identity is unchanged and remains uninstalled.
Coverage: F06/F09/F16, N01/N02/N03/N04/N05/N06/N08, C02/C09/C15/C18,
partial T01/T06/T07/T12; no aggregate gate passes.

[DesktopProcess](../../src/mcbench/desktop_process.py) creates a randomly named
non-input Win32 desktop, starts the exact operator command suspended, assigns
the existing kill-on-close/no-breakaway Job Object, then resumes the initial
thread. Environment variables are explicit, handles are not inherited, command
arguments do not pass through a shell, and startup requests hidden windows with
no launch feedback cursor. It never switches desktops or injects input.

An independent Python thread checks the input-desktop identity and monotonic
deadline every 50 ms; this is not the production guardian's independent-process
certificate. On changed/unavailable input context or exhaustion it stops the
owned job. Suspended startup failures cannot run child code. Holding kernel
process handles avoids PID-reuse termination. Normal cleanup also kills orphaned
descendants. A forced stop is not a clean Minecraft/agent checkpoint.

Desktop placement is not a security sandbox: same-user code retains its account's
filesystem/network/process rights. Authentication isolation, production guarded
launch, budgets/storage limits, native focus/pointer/key behavior and Minecraft
rendering remain required under .2c.3c.2 and native .1b.4/M1.1.

Verification used Windows and CPython 3.12 from the project environment:

- First real launch reached the separate desktop and created its hidden window,
  but failed an overly narrow root-PID assertion: the Windows venv redirector
  created the actual interpreter as a descendant. It also exposed redundant
  termination during an asynchronous job stop. The implementation now waits for
  job termination; direct termination is reserved for unassigned startup failure.
  Tests verify native job membership of redirector/interpreter/descendants.
  Both first-attempt processes were subsequently confirmed absent.
- Eight launch tests then passed in 2.72 s. After adding failure-path coverage,
  **12 launch tests and 6 existing process tests passed** in a combined run.
  Cases include exact Unicode arguments/environment, hidden window placement,
  unchanged input desktop, startup/job-attachment failures, pre-resume fencing,
  deadline stop, input-observation failure, timeout without replay, resource
  closure, owner crash and orphan-child termination. Context-failure tests inject
  observations; no real desktop switch is performed.
- That combined run had one unrelated gameplay-package test failure from an old
  recipe-query help string. Updated it for the existing category/item/fluid CLI
  and explicitly retained launcher exclusion. Its focused rerun **passed** in
  0.29 s. Original failed logs remain private; no packaging boundary was weakened.
- Gradle compileTestJava/writeTestClasspath passed in 16 s. This builds a test-only
  [graphics fixture](../../java/forge1192-client/src/test/java/io/github/opencnid/strata/client/DesktopRenderFixture.java),
  not a client mod change or Java test-suite rerun.
- [Graphics probe](../../tools/probe_desktop_render.py): JDK 17.0.20.101 with
  recorded LWJGL 3.3.1/Gson input hashes, hidden/unfocused 64×64 window, requested
  OpenGL 3.2 core context. **20 alternating-color frames passed pixel readback**;
  input desktop unchanged, child exit 0, no watchdog stop. Reported renderer:
  NVIDIA GeForce RTX 3090, OpenGL 3.2.0 NVIDIA 591.86; fixture elapsed 398 ms.
  After adding explicit launcher/probe/fixture fingerprints and structured
  preflight errors, the final focused graphics rerun passed in 393 ms.
  This is synthetic test imagery on the actual graphics stack, not Minecraft
  frames, a performance certificate, screenshot capture or physical-key parity.
- Initial graphics preflight rejected Gradle's absent empty build/resources/test
  directory. Created that empty build output directory before the successful
  probe; no missing library was substituted or ignored. Ruff and final source/
  artifact/link/diff checks pass. No broad game or paid suite was rerun.

Private evidence:
`C:\Users\Darian\.strata\evidence\2026-09-19-desktop-launch-01`.
The final render evidence records Java, classpath/library, launcher, probe and
compiled-fixture hashes. Earlier attempts remain separate. No Minecraft client/server was launched or mutated, no account
sign-in was automated, and no shared-desktop controls or paid inference were used.

Reproduce the graphics prerequisite after compiling test classes, with the empty
Gradle test-resource directory present, by running `tools/probe_desktop_render.py`
with absolute `--java`, `--classpath-file` and a new private `--output-directory`.
It returns bounded private JSON evidence and cannot admit campaigns.

Primary API references checked: Microsoft's [CreateDesktopW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createdesktopw),
[STARTUPINFOW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-startupinfow)
and [desktop connection rules](https://learn.microsoft.com/en-us/windows/win32/winstation/thread-connection-to-a-desktop)
define desktop selection and handle behavior. GLFW's [window hints](https://www.glfw.org/docs/3.3/window_guide.html#window_hints_wnd)
and [offscreen contexts](https://www.glfw.org/docs/3.3/context_guide.html#context_offscreen)
describe hidden context creation. Local results above qualify only the tested scope.
