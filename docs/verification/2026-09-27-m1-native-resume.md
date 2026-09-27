# Private native resume boundary

M1.1c.3.4 advances the required gameplay repair/resume workflow. This change
implements its native decision, journal and Python/TypeScript transport. It does
not yet release the worker's durable hold or complete the controller repair.
Full T05/G1 remains not_run. The essential-native04 health failure is retained;
no new Minecraft or model trial was selected.

## Contract and implementation

`strata.settingsResumeOwner=true` requires owned repair/effects mode and adds
`operator-owned-settings-resume/1` to the native fingerprint. Older profiles gain
no resume permission. Public gameplay capabilities remain unchanged.

`NativeSettingsResumeDecision/1` binds one resume ID, the entire original worker
plan, exact current settings revision/digest, committed or rolled-back phase,
private verification reference, connection generation and a bounded lease end.
The native coordinator requires the actual terminal settings phase and head.
For committed settings it also matches the stored commit's plan and verification
reference. The referenced verification is the private controller's responsibility;
the native parser cannot certify physical effects or read private CAS evidence.

The lane requires a healthy, live, idle repair with the same scope/body/generation,
no interrupted effect and the original deadline still valid. It confirms release,
clears old observation deliveries, journals the decision before opening input,
and preserves the epoch, worker lease identity, action sequence, receipts,
primitive consumption and immutable overall authority. The resumed lease is at
most6s and inside the original repair deadline. Normal renewal remains bounded
by the unchanged overall authority. Each transaction and resume ID is consumed
once; changing a decision cannot refresh it.

`NativeSettingsResumeState/1` returns the decision, originating/current native
instance, current lane health and actual `input_resumed` state. Duplicate requests
and explicit status reads do not rearm, extend the lease or repeat input. A later
stop, different executor epoch, journal reopen or subsequent repair cannot turn
the old receipt into live authority. Reopening retains the history while fenced.
Native effect verification remains explicitly false.

The new profile allows a successful, healthy rollback to remain held for restored
state verification before explicit resume. It never clears an existing failure.
Older profiles retain their original rollback/recovery behavior. Stop-all,
expiry, changed generation, failed release, stale settings, wrong verification,
uncommitted state and journal failure cannot resume input.

Python and TypeScript use strict request/receipt schemas and preserve a single
mutation POST. Uncertain replies remain unknown; recovery explicitly reads the
same transaction's status. The TypeScript worker must additionally match the full
returned decision to its durable intent before releasing its own hold. No public
tool or helper receives these private native operations or descriptors.

## Executed verification

- 48 distinct focused Java cases pass across resume, action lane, repair admission,
 restart and commit. The final changed-epoch and slow durable-write checks pass the11-case
 resume suite. Time spent persisting the decision cannot refresh its lease. The initial parameterized-test fixture error is retained in the
 first failed log and corrected; it is not a native behavior result.
- 16 Python contract cases and 10 actual JVM/HTTP cases pass, including committed
 and healthy rollback outcomes, lost resume replies, actual JVM replacement,
 reopen, negative admission cases and compiled Node→JVM transport. Game body,
 settings-effect verification and controller decisions are synthetic.
- 6 focused Node cases pass, covering resume and shared restart transport. The
 Node build and112 affected Python transport/commit/restart/deadline regressions
 pass. These are192 distinct focused cases, not192 accepted G1 requirements.

Exact environment: Windows, Python3.12.14, Node24.19.0, Java17.0.20.1+1 and the
existing offline Forge1192 test classpath. No installed game JAR was changed.
The installed `/6` artifact remains
`e2c718506b078f529e92fd25e31068af7377b079e1b591b2488bf98f9797c41d`.
The compiled Node distribution now includes the private resume transport.
All40 durable inference-authority tables and eight existing telemetry holds were
unchanged before and after work; no inference allowance was extended.

## Remaining integration

Worker/4 still holds repair state and rejects gameplay. Its replacement guardian/3
requires a fenced native lane; it cannot be used unchanged to supervise resume.
Connect an explicit worker/guardian transition, preserve journal/counters/expiry,
and reconcile unknown native delivery by status before releasing the worker hold.
Then connect controller ready-observation and complete consumption settlement;
`Reconfigurations.finish` still refuses a worker handoff with
`REPAIR_WORKER_RESUME_REQUIRED`. Do not remove that refusal without the actual
transport and evidence. Complete launcher, public control card/skill integration,
authentic essential/context/failure/isolation checks and final G1 qualification
remain required. No native rerun should precede a relevant completed integration
or an evidence-backed correction for the retained health failure.

## Preserved evidence

Private bundle `2026-09-27-m1-resume-source-01` is sealed:46 files,2,818,144 bytes,
SHA-256 `cd9a73bd9546b51908b9e1448c06fc2a213eb6e930ce36a82fd1565deb539d22`.
It contains source snapshots, original failed and passing logs, final11-case Java
resume results and10-case JVM transport rerun, compiled artifact hashes and
read-only authority/hold checks. No owned runtime remained. Installed JAR/options
are unchanged. All459 previous ledger IDs survive; M1.1c.3.4 makes460. The five
reviewed documents resolve all2,108 local links. This is a component checkpoint;
worker/guardian/controller integration and authentic acceptance remain open.
