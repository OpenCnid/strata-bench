# M1.6o — registered worker identity before readiness

The registered saved-body declaration must identify the account actually connected
to each probe body. This change adds explicit identity binding to the worker and
a complete both-arm invocation compiler. Authentic probe admission and complete
live-state matching remain open; this is implemented_unverified for that integration.

`VanillaProbeInputs.worker_invocations` requires the saved-body software /3 policy,
rechecks held pair/source/resource custody, reads committed destination bindings,
and derives UUIDs from the verified player declarations. It requires every member
in both arms, epoch1, distinct lease identities and fresh disjoint state/config
paths. Caller UUID overrides, incomplete rosters, foreign scopes, overlapping paths
and helper principals refuse. It neither starts a process nor releases a hold.

An invocation with an expected UUID emits `DevelopmentWorker/2`; absent identity
retains the original /1 configuration and digest behavior. Within the protected
cache lock, the worker checks the bound account profile before token refresh.
Provider identity validation and the private identity callback precede session
assignment and TCP connection. On spawn, the server login UUID must also match.
The pinned minecraft-protocol login handler sets `client.uuid` from the server
success packet; the check does not depend on later `bot.player` initialization.
Wrong identity, repeated authentication, closed identity or failed receipt storage
permanently fences readiness. Valid respawns produce increasing private sequences.

The operator journal stores strict `WorkerPlayerIdentity/1`, including the UUID
triple, campaign/agent/epoch/lease and spawn/time measurements. The Python reader
checks the configured scope and exact UUID agreement. A parsed record alone proves
no producer provenance. These records, account names, tokens and private paths
are not added to public observations or signals. Public capability/tool schemas,
Forge behavior, budgets and native admission remain unchanged.

Focused verification uses actual configuration, worker lane, authentication/cache
ACL and private journal code with **synthetic token provider and game transport**.
No game server, authentication network or model executes. Run with fresh private
logs, XML and basetemp, and `PYTHONPATH=src;tools;evaluator/src`:

```text
pytest tests/test_pack_worker.py tests/test_probe_saved_body_runtime.py -q
pytest tests/test_worker_identity.py -q
npm run build
node --test dist/tests/authentication.test.js dist/tests/authentication_dependencies.test.js dist/tests/player_identity.test.js dist/tests/worker_startup.test.js dist/tests/worker_health.test.js dist/tests/signals.test.js
```

The Python selections pass47 cases in92.91s and2 in0.19s. Node passes28 cases
in6.628s. After moving the full receipt header/scope to the journal sink, the four
identity cases pass again in1.387s with a successful build. Those overlap the28:
there are **49 distinct Python and28 distinct Node passing source cases**.
An audit reads the actual emitted TypeScript journal record through the Python
contract and passes15 checks, including scope/schema/mismatch refusals and unchanged
real accounting. It remains substituted transport evidence.

Two initial TypeScript fixture compilation failures and the first Python identity
selection (one failure, one pass) remain retained. The latter expected the internal
Fault instead of Pydantic's wrapping ValidationError; only the test assertion was
corrected. No authentic execution was repeated to repair these test errors.

Coverage: F01/F02/F04/F07/F08/F09/F16, N01/N02/N04/N06,
C06/C20/C23/C24/C36, partial T01/T06/T11. Full T11 still needs fresh pinned
runtime integration, all-N authenticated readiness and matched live state,
authoritative clocks and one-way disposal. Capable T05, protected T10 controls
and remaining combined runtime isolation also remain open. G1-G5 stay not_run;
M0/G0, unrelated M2-M7, historical failures and consumed decisions are unchanged.
All40 real authority tables retain $4.887796/$10 exposure and prior holds.
D18/D19 supplies no M1 paid inference allowance.

Private evidence `2026-09-25-m1-worker-identity-01` is sealed and independently
verified:4,778 files/15,571,913 bytes, SHA-256
`17950cd4dea1d7fd6f45260c49c5515419d6d26a23d4a798d9060322cd56e76b`.
It retains complete Python/TypeScript source and tests, generated worker code,
locks, the inspected protocol login source, failures, passing logs/XML, emitted
receipt, cross-language audit and final WAL-aware authority comparison. No owned
runtime remains. Focused Ruff and whitespace checks pass. Documentation QA
preserves407 prior milestone IDs, adds only M1.6o, preserves prior progress/SPEC
text and resolves1,594 local links. Subsequent seal pointers do not change source
or test evidence. Archived absolute paths remain data, never read grants.
