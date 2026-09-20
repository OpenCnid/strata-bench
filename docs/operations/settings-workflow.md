# Settings workflow — operator implementation, not qualified gameplay

`mcbench.controls.Controls` orchestrates a capability-tested adapter. The current
native Forge bridge still advertises `supported=false`, so this workflow rejects
it at planning. These services do not yet expose a qualified gameplay command,
produce authentic effect evidence, or suspend a live avatar's action lane.

## Profile ownership and recovery

Version 2 plans retain the requested binding IDs, profile ID, simulation flag,
revision, keymap backup, immutable settings-policy digest and required effect
matrix. Identical plan retries read the durable original without consulting a
changed/offline adapter. Changed intent under the same transaction ID is rejected.
No-change plans require no apply; an apply attempt returns `NO_CHANGE_REQUIRED`
without release/write/restart activity.

Applying or rolling back holds an OS file lock for that profile within the
operator database directory. This excludes another cooperating controller process
using the same database; the native writer's separate game-profile lock is still
required. SQL admission also checks both profile and avatar identity. Applying,
verifying and failed transactions keep their reservation. A failed rollback
cannot be bypassed by changing avatar or profile identifiers. Process exit
releases the OS lock but does not clear the persistent recovery hold.

The adapter's owner/context/protection/tested-pool/qualification metadata is bound
into the plan. Drift fences apply even when keys and a claimed revision remain
unchanged. Rollback restores only owned fields and requires unchanged unrelated
bindings and metadata; it never reports success while accepting a concurrent
foreign change. Rollback of an old committed transaction is also revision-fenced.
That committed revision survives failed attempts and controller/database reopenings;
retrying a failed rollback cannot adopt a newer revision. If a restore may have
changed the revision before a later failure, recovery remains fenced for operator
resolution rather than guessing ownership from matching key values alone.
Release is required before commit/rollback publication; a release or restore
failure leaves the profile in `failed` with `ROLLBACK_REQUIRES_OPERATOR`.

Existing tables gain a nullable profile column. Legacy active rows remain intact
and block new admission because their profile authority cannot be inferred.
Unsupported old plan versions require operator recovery; no automatic migration
relabels them verified or replays their mutations.

## Adapter and evidence contract

The private adapter supplies:

- `snapshot()`: qualified capability flags, profile/fingerprint/revision, bindings
  and the tested key pool. Native discovery/configuration alone is not qualification.
- `compare_and_swap(revision, changes, transaction_id=..., rollback=...)`: preserve
  the durable transaction identity and direction across dispatch/recovery. The
  adapter must perform native journaling and owned-field CAS, not raw file writes.
- `verify_and_restart(changes, transaction_id=..., plan_digest=..., binding_checks=...)`:
  run actual ordinary-input/effect checks and worker-managed restart, returning
  transaction/plan-bound evidence. No such qualified Minecraft provider exists yet.
- `stop_all()`: confirmed input release. OS release and polling conformance remain
  required on the actual backend.

Verification includes the global intended/competing/release/essential/restart
checks and every affected binding before and after restart. The affected set
includes changed controls and potential competitors on the old/new keys. GUI
checks include chat; universal or unknown contexts require conservative in-game,
GUI and chat coverage. Unknown contexts are not automatically proven by these
labels; a qualified verifier must implement the actual context/effect tests.
Missing, duplicated, mismatched, failed or unverified-context checks cannot commit.

Each check reference resolves to bytes for a private `strata/ControlCheck/1` object:

```text
schema, transaction_id, plan_digest, check, binding_id, context, stage,
status, is_example, source_refs
```

Global checks use null binding/context/stage. Binding checks use the exact required
binding/context and `before_restart` or `after_restart`. The workflow verifies the
object's SHA-256, exact fields, identities, pass status and referenced source-byte
hashes. Proof objects are at most 64 KiB; a versioned plan records a 32 MiB total
verification-read allowance. The injected `evidence_reader(ref, max_bytes=...)`
must enforce its bound before loading bytes and authorize the fixed namespace.
`CAS.read` accepts this bound and rejects oversized objects before file reads.
For example, bind an operator-owned CAS reader using `functools.partial` with a
fixed principal/namespace; never accept a namespace from the gameplay caller.

Production mode requires a reader and rejects example proofs. Explicit simulation
mode is persisted separately; its database cannot reopen in production mode.
Successful synthetic tests use real content-addressed example proof/witness bytes
and remain simulations. Hash consistency proves artifact binding, not that the
producer performed the claimed physical effects. Authenticated verifier provenance
and the actual Minecraft checks remain necessary acceptance evidence.

## Controller repair coordination

`mcbench.reconfiguration.Reconfigurations` connects the private settings workflow
to controller input authority and existing budget reservations. Its endpoints are
operator library methods, not gameplay tools. Configure a content-addressed
`strata/RepairPolicy/1` before campaign start: campaign/system/protocol identity,
distinct avatar profiles, condition and whether repairs are permitted. The policy
is immutable. Cognitive probes cannot enable repairs; a missing policy denies them.

The implemented sequence is:

1. `request`: bind a planned settings transaction to a reserved tool-budget
   operation. Persist `QUIESCING`, invalidate the target avatar's old input
   generation/lease and revoke its executor grants. The campaign stays RUNNING;
   other avatars keep their grants. Active repair profiles and budget operation
   IDs cannot be shared by another repair.
2. `enter`: require a fresh private `strata/RepairStop/1` receipt, including the
   old lease, generation, cancelled pending input and released controls. Only then
   publish `RECONFIGURING`. The stop acknowledgment window is one second; this
   controller check does not itself implement the 250 ms local input watchdog.
3. `apply`: durably record dispatch intent before calling `Controls.apply`.
   Expiry/owner loss or any interrupted call preserves the hold. Recovery can
   query or roll back; it cannot replay a forward write from an uncertain phase.
4. `finish`: require a fresh `strata/RepairReady/1` receipt, the actual referenced
   typed Observation, matching runtime revision/keymap, released input, completed
   settings outcome and settled tool-budget operation. Observation capture must
   follow settings completion. Readiness freshness is rechecked after adapter
   reads. Only an unexpired repair with remaining budget gets a new input lease
   and OBSERVING state. Overruns retain all costs and leave input interrupted.

Stop/readiness receipts and witness bytes live in a fixed private CAS namespace;
their schemas reject unknown fields. Simulation requires explicit example
receipts. Production requires non-example receipts but still needs authenticated,
qualified worker producers; these schema checks do not prove physical effects.
The reference provider/transport is not implemented or qualified yet.

`expire` is a supervisor polling hook, not a running watchdog. It uses UTC and a
process-local monotonic deadline. A new coordinator clock instance cannot resume
forward work from the old instance. `adopt_recovery` retains the hold under the
current controller epoch; rollback remains possible without replay. New runtime
readiness is required when the old clock/lease cannot authorize resumed input.
Legacy controller databases without avatar authority fail closed rather than
deriving new leases from old grants. Pending repairs also prevent whole-team
readiness from bypassing their holds.

Controller grants now require a ready avatar for `act`, bind its input generation,
and revoke a prior input-bearing grant when replacing its designated executor.
Read-only startup grants remain usable through the normal readiness transition.
This is controller authorization; the current development Mineflayer gateway does
not consult this store and must not be advertised as fenced by these changes.

`Clocks.record` continues to charge the whole team's measured active exposure and
reserved body time during repairs. It validates roster size and records separate
`clock_repairs` attribution for holds active when an interval is ingested. This
annotation does not add exposure again, apportion game ticks, or claim exact repair
boundary timing. Duplicate ingestion preserves the original annotation. A repair
alone cannot exclude a RUNNING interval as a whole-campaign offline pause.
Authoritative telemetry, complete interval coverage, automatic usage settlement
and all-call reconciliation remain required.

## Remaining integration

Wire the qualified Forge adapter and verified native commit to this workflow;
the development bridge has no commit operation. Connect the controller's avatar
authority to actual worker lease/cancel/stop transport and qualified receipt
producers, ordinary verification actions, worker restart/rejoin, complete time/cost
accounting and `KeybindingPatch` export. Terminal-campaign pending repairs need an
explicit operator recovery path; campaign cleanup cannot silently discard them.
Keep the server and other avatars running, retain costs/continuity, and honor the
probe condition's ban on reconfiguration. Native isolation and cross-client cases
remain unrun. The current locks and structural proof validation do not close T05,
T06, T07 or G1.
