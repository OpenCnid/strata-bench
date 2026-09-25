# M1.6o.1 — authentic identity-bound worker conformance

D20 authorizes this operator conformance dependency. It uses a fresh pinned
worker containing commit7437692's identity checks, a separately sealed vanilla
PackLock and the existing protected writer/server path. No native model agent,
paid inference, shared-desktop input or experimental probe is authorized by
this report. Full G1 remains open.

The retained baseline contains no player. The expected account UUID is declared
before launch from the separately sealed authentic saved-player reconstruction.
The trial must join that declaration to the authenticated/server UUID receipt,
the scoped live observation and the newly saved player. This can qualify worker
identity; it cannot establish matched probe initial state or reinterpret the
baseline as a registered player checkpoint.

Preparation copies only reviewed worker/runtime dependencies and excludes game,
authentication and evaluator material. The new private runtime has11,725 files
and654,090,689 bytes; its manifest SHA-256 is
`24efd636d855655e0281b969d79cd32d319aac695c4ee15db034025ddea8553c`.
Actual fixed import succeeds in3.391s with all3 owned processes normally terminal.
All40 authority tables remain unchanged during preparation. Runtime evidence
`2026-09-25-m1-identity-runtime-01` is sealed with12 files/9,356,017 bytes:
`9374bb2e7e4531173f57dc520f02ed9694a942f3afc41edfc42aae3e43cce244`.

The new profile reuses verified acquisition and unchanged installation/server
inputs, pins the changed worker, and preserves the explicit worker-profile
baseline policy. Publication passes: all original durable rows are preserved,
with additions restricted to provisioning/object/outbox metadata;37 other tables
are unchanged. Accounting, allowance, holds, consumed decisions and existing
profile identities remain unchanged. New lock
`e1ef108948f1a63d4f78e57079c5aa5f33551e91c25edfab8d6c08ed7f8b0d83`
is materialized and its baseline restored. Profile evidence
`2026-09-25-m1-identity-profile-01` is sealed with16 files/32,028,334 bytes:
`fd070a281e32d75e980b6bcf0ed0d273a1b791acc602c5ee95b598f0793539ed`.
The server window remains180s, worker360s, outer writer480s. No deadline is
extended to obtain a passing result.

Coverage inherits M1.6o: F01/F02/F04/F07/F08/F09/F16, N01/N02/N04/N06,
C06/C20/C23/C24/C36, partial T01/T06/T11. Complete registered both-arm bodies,
matched live initial state, native admission, authoritative clocks, disposal,
capable T05, protected T10 and remaining runtime isolation remain required.
M0/G0 and unrelated M2-M7 are unchanged.

The authentic case **fails** in105.922s with `WORKER_EARLY_EXIT` and retains
status `uncertain`. The protected server reaches owned readiness, but the worker
parent exits with `CAPABILITY_MISSING` before issuing a grant or creating its
journal. No avatar connection, identity receipt, observation or stopped world
capture exists. The copier exits normally10/10. Server cleanup is forced exit125,
with12/12 retained processes terminal and complete logs; this is not a normal
server stop. The final owned-runtime snapshot is empty. All40 authority tables
are unchanged across the actual trial; exposure and all holds remain intact.

The cause is the supervisor's separate operator-stop allowlist: it accepts only
DevelopmentWorker/1, despite the new /2 configuration parser and lane working.
Previous component tests did not exercise this parent entry point. A new
subprocess regression reproduces the exact refusal (two cases pass, /2 fails)
using the real parent, fork, configuration and stop machinery with a synthetic
IPC child. It performs no authentication or network operations. The correction
explicitly admits /2 alongside /1; Forge remains refused. Successful synthetic
children receive the complete unchanged configuration and drain through the
same scoped command with the2250ms bound. This verifies M1.6o.1a's supervisor
selection correction, not authentic account/server identity.

```text
npm run build
node --test dist/tests/worker_operator_startup.test.js dist/tests/worker_control.test.js dist/tests/worker_startup.test.js dist/tests/player_identity.test.js
```

The changed build succeeds and26 focused cases pass in1.405s. Preserve the first
regression failure and original native source. No unchanged native rerun occurs.
M1.6o.1 remains in_progress: next prepare a new runtime/profile from this corrected
source, then execute a fresh bounded identity trial. Never retarget the sealed
failed profile or reinterpret this failure as successful readiness.

Independent read-only reconstruction passes19/19 checks of the failed producer,
runtime/profile/config pins, refusal source, normal copier versus forced server
history, three write denials, absence of grant/journal/observation/capture,
provisioning-only additions and unchanged accounting. The planned success audit
is retained as explicitly unexecuted; it is not passing evidence.

Native evidence `2026-09-25-m1-identity-native-01` is sealed with293 files/
8,670,585 bytes, including255 pinned source files and the original failed logs:
`e4a96d4c4e21c387a42f7f9bfd07f9c1d6b79aafaf348514a8486c8dba5c834f`.

Failure reconstruction store `2026-09-25-m1-identity-audit-01` verifies6 files/
16,497 bytes under seal
`81a02506f617e6243d109a2f3dd1fa1766a35ef12531776f959cb82945b8ed78`.
Correction store `2026-09-25-m1-identity-startup-fix-01` verifies130 files/
4,518,672 bytes under seal
`eeb2729cc02abeeb85fc07806c561991c29c84af6bcd267ad0443bf568b6a724`.
It preserves original worker source, the failing regression, final build/tests,
115 exact current source files, locks, final authority/process checks and doc QA.
All408 prior milestone IDs and append-only progress remain; only .1/.1a are
added, prior SPEC text is preserved with the explicit stop clause, and1,600 local
links resolve. Whitespace checks pass. Seal pointers added afterward do not
change source/test evidence. No new authentic trial has run on the corrected
source; passing reconstruction never promotes the failed producer.
