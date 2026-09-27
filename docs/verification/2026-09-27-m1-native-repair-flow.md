# Controller-owned native repair writes

M1.1c.3.2 now connects the controller's immutable control plan to native apply,
verification validation, commit and rollback. The actual controller → Node worker
→ Windows guardian → JVM settings path passes normal delivery and lost replies
for each mutation. The game body and effect/restart proof producer are synthetic.
This closes the connected write path, not authentic gameplay repair/resume or a
complete G1 acceptance suite. M1 remains in_progress; G1 remains not_run.

## Implemented behavior

`NativeRepairFlow` uses the previously confirmed worker/native admissions and
exact private descriptor, target, immutable plan and original fixed deadline.
Forward writes require live worker/native holds and retained controller budget
authority. Repair and settings-profile locks cover dispatch; native admission
shares that profile lock. Generic settings apply/rollback cannot bypass a native
handoff, including after acquiring the profile lock.

Each operation consumes one durable intent before dispatch. An uncertain reply
can only be reconciled by status. Commit validates the existing complete control
verification contract, including per-binding/context/stage checks and private
source bytes, before recording an immutable verification object and native commit
decision. A changed verification cannot replace a consumed decision. Complete
native runtime/persisted keymaps are checked after writes; mismatches cannot be
reported as success. Failure to publish observed success requires recovery.

Owned rollback remains available after a failed or expired forward repair, using
the original private bindings and native store's guarded rollback. It cannot
release input. Controller and worker leases stay fenced; the teammate remains
ready and the synthetic repair reservation remains held. No consumption is
refunded and no automatic budget settlement or gameplay resume is introduced.

The extracted `Controls.validate_verification` preserves the existing proof
requirements and additionally rejects a non-object checks container explicitly.
Native status/commit schemas and profile identities remain unchanged.

## Executed checks

Windows; Node24.19.0; Java17.0.20.101; the production Java fixture classpath built
at849fc00. No installed client artifact changed and no Minecraft/model call ran.
All outputs and fresh fixture directories are retained privately under
`2026-09-27-m1-native-repair-flow-01`.

- Initial focused flow/controls/reconfiguration/native-plan checks:70 pass.
- Initial actual worker/guardian/JVM flow:4 pass, including lost apply, commit
  and rollback delivery; each mutation dispatches exactly once.
- After profile-write exclusion, immutable verification copying and generic
  rollback protection: `pytest -q tests/test_native_repair_flow.py
  tests/test_controls_fencing.py` returns51 pass. Missing restart/effect/binding
  proofs, unavailable source bytes, a foreign plan, changed keymaps, evidence
  storage failure and changed consumed verification are refused.
- The four actual worker/JVM cases then pass again. Review subsequently extended
  profile exclusion to admission and rechecks the generic guard under its lock.
  The final focused lock tests and normal actual worker/JVM flow return3 pass,
  with28 explicitly deselected cases; no skips or failures.
- Ruff and whitespace checks pass. The earlier read-only Windows literal-glob
  search failed; the corrected search supplied the intended files. This was a
  preparation diagnostic, not a test or runtime failure.

The JVM cases explicitly use a synthetic verification producer; they do not
establish physical effects or an actual restart. The native body primitive cap
and controller reservation are fixture inputs, not a completed accounting join.

## Remaining acceptance

Affected: M1.1c.3.2; F06/F09/F11/F16; N01/N02/N04/N05/N08; control, authority,
evidence, journal, budget and deadline contracts. Complete T01/T04/T05/T06/T10/T11
and G1 remain not_run.

Next complete the qualified native control projection and authentic verification
producer, then owned restart/rejoin and explicit resume/recovery. Join all native,
verification and cleanup consumption to the original reservation and settlement.
Prove one authentic gameplay repair workflow before closing its acceptance row.
The current worker/native journal deliberately retains recovery after reopening;
a fresh unrelated worker or raised campaign epoch cannot substitute for resume.
Complete the remaining T05 matrix, T01 references, probes/scorer controls and final
exact-profile T04/T06 before assembling G1. Unrelated M2–M7 remain outside scope.

D20 authorizes implementation. D18/D19 inference authority remains M0-only.
Final WAL-aware audit: all40 authority tables unchanged at4,887,796microUSD;
all five historical256MiB telemetry holds unchanged. No Java or owned fixture
process remains. Historical failures, decisions, profile identities and holds
are preserved.

Ledger audit: all459 milestone IDs preserved; all1631 local ledger links resolve.

Private evidence sealed841files/19,206,632bytes at
`e61f5865c1716192ee64bf2399fcf7c0811e175b6403745c15452d38e5d94d24`.
It retains all five test runs and fixtures, source/document snapshots before this
pointer, authority/hold/process audits and the preparation diagnostic record.
