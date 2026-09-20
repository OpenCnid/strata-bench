# Worker schema compilation and bounded startup

September 20, 2026. Operator-only. M0.3b.2c.3c.2b.2b.2.1a;
F01/F05/F16, N01/N02/N04/N06/N08; T01/T03/T07/T12, G0.
Implemented; authentic loaded-game timing remains unverified. G0/T07 remain fail.

[Machine operation-03](2026-09-20-native-machine.md) misses the fixed 2,250 ms
bootstrap deadline after the exact E9E client joins. Zero actions run. This is a
retained authentic failure, not an idle-host benchmark failure. Operation-02's
earlier successful bootstrap took 1,477.861 ms on the loaded host; its separate
guardian failure remains unchanged. The -03 journal does not identify a single
causal bottleneck.

The worker previously compiled four public JSON schemas with Ajv before sending
bootstrap readiness. The existing pinned Ajv 8.20.0 / ajv-formats 3.0.1 now generate
[standalone validators](../../backends/mineflayer/src/schema_validators.ts) during
`npm run generate`. [The generator](../../backends/mineflayer/tools/validators.mjs)
uses the exact previous strict-number/no-coercion/first-error policy. `npm run
build` verifies byte-for-byte reproducibility before TypeScript compilation.
[Protocol startup](../../backends/mineflayer/src/protocol.ts) compares each source
schema's SHA256 with the generated digest and rejects stale bytes. Existing
machine-window semantic checks remain. The compiled validator module participates
in the existing capability implementation digest. No deadline, heartbeat freshness,
authority ordering, public API or acceptance threshold changes.

Credential-free actual Node 24.19.0 child-process diagnostics, five samples before
and five after, pass no configuration, grant or avatar authority. Each child
reports real post-import bootstrap readiness and is then disconnected; exit one
is the intended lost-parent behavior. Games are stopped during these diagnostics.

| Measurement | Before | After |
|---|---|---|
| Actual child bootstrap, five samples | 396.419–424.254 ms | 158.171–181.280 ms |
| Separate protocol import, five samples | 284.015–306.297 ms | 38.602–43.650 ms |

These are idle-host diagnostics, not loaded-game reliability qualification.
No work is shifted outside the existing game initialization deadline.

Verification executed:

- `npm test`: 128 pass, 43 explicitly skipped JVM/Windows cases, zero fail.
  Three new tests cover 2,467 deep differential comparisons against freshly
  compiled Ajv, no data coercion/mutation, reproducible output/capability pinning,
  all four stale-schema failures and absence of the Ajv compiler at runtime.
  Existing schema/semantic/startup state-machine tests pass. An initial focused
  run matched all generated comparisons but failed a test's guessed minimum
  case count; boundary-value coverage was expanded and the original count
  assertion retained. No production threshold changed.
- Python canonical/contracts/records: 63 pass (1.26 s).
- Actual gameplay-client package exclusion: one pass (0.28 s); compiled worker
  validators and evaluator material remain outside the gameplay client bundle.
- The full generator also corrects a previously stale operator `NativeLaunch`
  TypeScript binding to include the already-exported `session_storage` field.
  No schema or runtime contract changed.

- Separate `node --test dist/tests/forge.test.js` with the pinned Java fixture
  classpath and Windows Python guardian: **55 pass, zero skip/fail** (113.082 s),
  including all 43 cases skipped by the general command. These are actual
  disposable JVM/process tests with synthetic game data, not Minecraft trials.

The next authentic trial is recorded when complete. Raw diagnostics, logs, failed-start audit and trial
evidence remain outside the repository under
`C:\Users\Darian\.strata\evidence\2026-09-20-machine-reference-01`.
No inference or shared-desktop input occurs. The operating-machine requirement,
500-ms guardian qualification, private scoring, host isolation/accounting and
remaining M0–M6 gates are still open.
