# Native settings commit decision path

M1.1c.3.2 now has the native transaction finalization primitive needed by the
qualified adapter. A separate explicit profile records the controller's exact
commit decision, supports read-only reconciliation and retains rollback/recovery
history. Focused production-store/JVM/HTTP checks pass with synthetic body/input
and explicitly synthetic controller decisions. No full repair workflow, physical
verification, worker resume or aggregate G1 suite is passed by this work.

## Implemented contract

`strata.settingsCommitOwner=true` requires the existing effects and repair-owner
modes. Its distinct `operator-recorded-settings-commit/1` policy participates in
the native game fingerprint. Neither the earlier preplay nor repair-only profile
receives commit permission. The public gameplay capability remains unchanged.

The private NativeSettingsCommitDecision/1 contains transaction, original plan
digest, exact pending native revision/digest and a verification CAS reference.
The coordinator requires the live admitted plan and its original deadline;
the store validates the complete pending runtime/disk state before appending and
forcing the commit. It does not rewrite options or interpret configuration equality
as proof of effects. The controller's qualified adapter must validate the full
verification evidence before issuing the decision; that producer is still missing.
The native store accepts the authenticated operator decision and records its
reference, without fetching or independently evaluating the referenced evidence.

NativeSettingsCommitState/1 returns the exact consumed decision, current transaction
phase and journal revision, with `input_resumed=false` and
`effects_verified_by_native=false`. A changed decision cannot replace an existing
one. The Python client sends one mutation request and requires matching status
after uncertainty. The effects client understands committed transaction receipts;
the older title-screen transport retains its narrower receipt contract.

Commit releases the settings transaction's pending slot, while the independent
native repair hold continues to block all new executor arms. Reopening preserves
both the decision and that recovery hold. A rollback of a committed transaction
requires the original commit revision/digest and no later transaction. The full
existing runtime/disk/metadata CAS checks still apply. It cannot overwrite newer
settings, and rollback changes neither the original decision nor its evidence.
Replay validates the commit's original position in the journal.

## Executed verification

Local Windows, Java17.0.20.101, Node24.19.0 and existing pinned offline Gradle
dependencies. No installed artifact changed; no Minecraft or model run occurred.

- Initial SettingsCommitTest, SettingsStoreTest and NativeRepairAdmissionTest
  pass. The new cases exercise idempotence without another key write, unchanged
  pending-head rejection, reopening/rollback, refusal to overwrite a later
  transaction, invalid commit journal position and uncertain journal append.
- The initial Python run returns80 pass and one failure: the new test expected
  Fault from a direct Pydantic result validator, which correctly raised
  ValidationError for contradictory committed state. The assertion now requires
  ValueError with the precise rejection code. The original log/fixtures remain.
- Adding the distinct commit opt-in profile led to a focused Java run covering
  SettingsCommitTest, SettingsEffectAdmissionTest and SettingsEffectRunTest;
  it passes. No unchanged full suite was repeated.
- Final `python -m pytest -q tests/test_native_commit.py tests/test_native_commit_jvm.py`
  returns20 pass, no skips. Actual JVM/HTTP cases cover decision storage,
  immutable options bytes at commit, lost delivery followed by status, reopening
  with commit mode absent, rollback, stale/foreign/malformed decisions, repair-only
  profile refusal and expiry refusal with cleanup still possible.
- Ruff and whitespace checks pass. An initial patch application used the wrong
  local variable in its context and was rejected before editing; a PowerShell
  brace-expansion search was also rejected. These preparation diagnostics are
  retained; no runtime verification is inferred from them.

Java command: `java/gradlew.bat -p java --offline :forge1192-client:test` with the
named selectors and `:forge1192-client:writeTestClasspath`. Python uses explicit
pinned Java/classpath/Node environment and fresh retained fixture directories.
Private evidence root: `2026-09-27-m1-native-commit-01`.

## Remaining acceptance and next integration

Affected: M1.1c.3.2, F06/F09/F16, N01/N02/N04/N05/N08 and settings, journal,
deadline, input and evidence contracts. M1 remains in_progress; complete
T01/T04/T05/T06/T10/T11 and G1 remain not_run.

Next connect the qualified adapter's complete effect/restart proof validation to
this decision path, and implement worker-owned restart/rejoin and explicit
resume. The current native journal deliberately reopens in recovery and the
worker refuses retained repair holds. A repair must preserve the campaign/team,
original fixed deadline, charged downtime and consumption; raising the campaign
epoch or creating an unrelated clean worker is not a restart/resume solution.
Then verify authentic charged gameplay repair and the rest of T05's matrix.

D20 implementation authority persists; D18/D19 spending remains M0-only. Preserve
all historical failures, profile identities, consumed decisions and budget holds.
Final durable/process audit and evidence seal are recorded below.

Final audit: all40 authority tables unchanged at4,887,796microUSD and all five historical256MiB holds unchanged in their current WAL-aware databases. No Java or owned test process remains. All459 milestone IDs preserved; all1628 local ledger links resolve.

Private evidence sealed210files/3,260,559bytes at
`9a4d72a3209b4a2aa40faf81af9578dcccee88e5af1414ac61d67916d53a9be8`.
The archive contains the original failed assertion, final fixtures/logs, Java
result XML, source/document snapshots before this pointer and durable/process audits.
