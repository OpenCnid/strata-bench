# Public gameplay remains held until control publication

M1.1c.3.4 implements a separate worker completion boundary in
`ForgeDevelopmentWorker/6`, with `verified-controls-after-settlement/1`.
This is a manual-conformance candidate, implemented but unverified in Minecraft.
All complete G1 suites and G1 remain `not_run`.

## Implemented behavior

Native resume prepares the client but leaves public actions suspended. The
original resume lease continues counting down; the worker does not renew it while
publication is pending. A durable publication hold is inserted with resume intent.
Native completion alone cannot clear recovery on journal reopen or a new epoch.
Worker/5 retains its earlier immediate private-candidate resume behavior.

The worker creates a separate private `WorkerControlPublicationGrant/1`, bound
to the exact resume grant. Requests reject public credentials, browser origins,
unknown fields and malformed decisions. `WorkerControlPublication/1` binds the
original plan, consumed resume digest, terminal control revision/keymap,
verification reference, settlement reference and cumulative worker primitives.
The native instance and original decision must still match, and the worker count
must equal the supplied accounted count before publication can proceed.

The settlement reference comes from the trusted operator/controller. This worker
checks its shape and binds it durably; it cannot resolve private CAS or prove the
reference represents complete settlement. A production controller producer and
completion transaction are still required. The connected test's settlement
producer is explicitly synthetic, and it does not settle real campaign costs.

One durable publication intent and a fresh observation precede release of public
actions. Failed persistence or a concurrent stop prevents late release. Duplicate
publication queries the consumed result; stopped input is never rearmed. Closing
drains publication work before disposing of the journal. The current policy still
has the unchanged original health/termination and worker lifetime bounds.

Observations carry the published control revision and keymap digest. The CLI
copies them into its action, and the worker checks both current state and the
cited observation. It stores the original public request, then journals a native
translation and both digests before dispatch. The native structured contract
retains the worker epoch and null keymap. This is metadata translation only;
the action, identity, sequence, deadline and physical bounds are unchanged.
Historical request replay returns its original receipt even after controls change.
No public controls endpoint or keybinding capability is newly advertised.

## Verification

The actual Python controller → Node worker → Windows guardian → replacement JVM
test executes an action before repair, blocks public input after native resume,
publishes control metadata, executes the next action through the real CLI/native
transport, and retrieves the old action without re-emission. Both native input
release and the synthetic body's yaw change are checked. The journal proves the
same epoch/action sequence and retains distinct public/native request metadata.
The game body, settings qualification, verification and settlement producers are
synthetic. No Minecraft or model trial was launched.

The original Worker/5 lost-reply case also passes after the shared changes.
Focused Node tests cover pending publication, changed proof, stale control
metadata, accounting mismatch, foreign native instance, publication-store failure,
stop/read races, journal reopen and endpoint credential/origin rejection. Shared
actual-JVM checks cover ordinary observation/action receipts, cancellation and
the scoped CLI. Config checks admit Worker/6 only with its exact policies and
reject attempts to import its extra field into Worker/5.

Executed commands and results:

- `pytest tests/test_controller_restart_jvm.py -k 'publish or resume_lost' -q`:
  2 passed, 5 deselected; explicit Windows Node/Java/classpath.
- Node `worker_resume.test.js`: 12 passed before the additional reopen/instance
  checks. Focused publication checks on the final implementation: 8 passed
  (Node includes the nested failure group in its count).
- Selected publication/config/ordinary action/cancellation/CLI checks across
  `worker_resume.test.js` and `forge.test.js`: 11 passed with explicit JVM paths.
- Node build/schema-validator check, Ruff and whitespace checks pass.

Initial failures are retained. The first Node fixture used the wrong `look_at`
shape and was correctly rejected. The first process fixture accidentally copied
the worker-only publication policy into the strict guardian grant; attachment
was refused. The fixture was corrected, without relaxing the guardian schema.
An auxiliary cleanup edit initially used the wrong working-directory-relative
Python path; it was applied from the repository root before final verification.

## Remaining gate work

Implement the strict controller publication consumer and actual settlement
producer. Account for the complete repair interval and all primitives without
double charging previously settled gameplay, and publish the original lease and
controller completion together. A reference or cumulative count alone is not
that evidence. Generic `Reconfigurations.finish` remains closed for worker repairs.

Restored-effect rollback, repeated repair ownership, the qualification issuer,
selected gameplay skill, real launcher and authentic effect/context/failure/
isolation matrix remain required. Preserve essential-native04's health failure.
No unchanged real-game retry, M1 inference spending or installed-client change
was made. This component evidence closes no complete G1 suite.

Final connected check after binding publication to the original native instance:
`pytest tests/test_controller_restart_jvm.py -k publish -q`:1 passed,6 deselected.
This repeats the changed-profile scenario, not an additional acceptance case.

Private evidence bundle `2026-09-27-m1-control-publication-01` is sealed:46 files,
2,772,163 bytes, SHA-256
`34f92bf83bd917769b481cba4a60851a049fd68b52f683d03336cb655aed9791`.
It retains changed source, compiled pins and original failed/passing logs.
All40 authority tables and eight retained holds match before/after. Installed
JAR/options unchanged; no owned runtime remains. All460 ledger IDs are preserved
and2,118 local links in the five reviewed documents resolve. The archived source
snapshot precedes this appended seal pointer. M1 in_progress; G1 not_run.
