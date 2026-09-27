# Native pending-repair restart handoff

M1.1c.3.2 now implements the native half of an intentional repair restart. The
actual Python→JVM route preserves a pending settings transaction across process
termination, consumes one exact continuation and permits post-restart verification
input while gameplay remains fenced. Body/input are synthetic. Worker-owned
replacement, controller rebinding and authentic Minecraft repair/resume remain
incomplete; this does not close T05 or another complete G1 suite.

## Contract and identity

`strata.settingsRestartOwner=true` requires effects and repair ownership. The
native game fingerprint includes `operator-owned-settings-restart/1`; previous
profiles gain no continuation permission. Public capabilities are unchanged.

The private NativeSettingsRestartRequest/1 binds transaction, original control
plan digest, one restart ID and the exact pending settings revision/digest.
Preparation verifies the complete native runtime/persistent head, releases input
and journals NativeSettingsRestartCheckpoint/1 with its originating lane-instance
ID. It suspends forward settings/effect work before shutdown. Ordinary shutdown
release remains charged and cannot extend the handoff.

On reopening, the same journal/authority and pending settings head are required.
An exact private checkpoint may continue only once, under the original wall
deadline, immutable campaign/avatar/lease/body and primitive cap. A new instance
is required; a request in the original instance is refused. Monotonic expiry is
bounded by the remaining original wall window, and backward wall time is refused
at journal open. Used requests/effects, prior consumption and journal history
remain intact. An unplanned reopen or another reopen after continuation retains
recovery instead of obtaining another continuation.

NativeSettingsRestartState/1 exposes the consumed checkpoint, instance IDs,
original expiry and charged primitive count with `input_resumed=false`. Read-only
status reconciles lost replies. Under this opt-in profile, before_restart effect
requests require the pre-handoff phase and after_restart requests require the
consumed continuation. A supplied stage label cannot bypass that transition.
The settings patch remains pending until complete independent verification and
commit; native restart alone claims neither physical effects nor gameplay resume.

An instance ID proves journal-instance separation, not process death. The worker
must independently verify the old process tree is terminal, maintain the running
server/team, bind the replacement client and account for downtime before adopting
the new connection. Those orchestration joins are still required. The test below
does independently observe actual JVM exit, but is not that worker implementation.

## Executed evidence

Windows, Java17.0.20.101, Node24.19.0 and pinned offline Gradle dependencies. No
installed client artifact changed; no Minecraft or model call ran. Private root:
`2026-09-27-m1-native-restart-01`.

- Initial NativeRepairRestartTest, NativeRepairAdmissionTest and SettingsCommitTest:
  16 pass, one assertion fails because clock rollback is rejected earlier, during
  journal opening. The corrected assertion requires that exact failure. Original
  log/XML retained; no production relaxation.
- Corrected restart and affected GameActionLaneTest run:25 pass. After adding
  explicit before/after-stage enforcement, focused restart/admission tests:14 pass.
- Python restart wire, settings-effect and commit contract checks:67 pass. These
  refuse foreign checkpoints, false resume/continuation claims, invalid primitive
  counts and status requests without an exact expected identity.
- `pytest -q tests/test_native_restart_jvm.py`:6 pass with no skips. Actual JVM
  exit/reopen, same pending head, fresh connection session, continued raw effects,
  no gameplay arm and rollback are exercised. Lost prepare/continue delivery
  reconciles by status; each journal transition occurs once. Another process
  reopen, disabled mode, changed settings head and original deadline expiry are
  refused without advancing the settings transaction.
- Ruff and whitespace checks pass. Existing Java deprecation and Git line-ending
  warnings remain. Preparation diagnostics retained: two Windows literal-glob
  searches failed; ACL creation rejected the already-created evidence directory;
  Set-Acl attempts failed to remove its inherited administrator entry. A native
  DACL-only removal succeeded and the existing verifier confirmed exactly the
  operator/SYSTEM boundary before fixture execution. No credentials were created
  there before protection was confirmed.

Final WAL-aware audit: all40 authority tables unchanged at4,887,796microUSD; all
five historical256MiB telemetry holds unchanged. No Java or owned fixture process
remains. D20 implementation authority persists; D18/D19 remain M0-only spending
authority. Preserve every original failure, hold, consumed decision and profile.

## Remaining work

Affected: M1.1c.3.2, F06/F09/F11/F16, N01/N02/N04/N05/N08, native settings/input,
journal, clocks, accounting and private transport. M1 remains in_progress;
complete T01/T04/T05/T06/T10/T11 and G1 remain not_run.

Next implement worker-owned replacement and controller connection handoff against
this durable checkpoint, then complete the qualified control projection and
authentic verification producer, accounting settlement and explicit resume.
Verify the full workflow in Minecraft and complete the remaining T05 matrix,
T01 references, matched probes, scorer controls and exact-profile T04/T06. No
unrelated M2–M7 work is added, and no new epoch or unrelated clean worker may
substitute for continuity of the existing repair.

Ledger audit: all459 milestone IDs preserved; all1634 local ledger links resolve.

Private evidence sealed108files/2,950,696bytes at
`0dfa2e1a76a4ba12355961cb5073154549faba085da15c6faecb3281f181900a`.
It retains all test logs/XML, JVM fixture journals, source/document snapshots
before this pointer, durable/process audits and preparation diagnostics.
