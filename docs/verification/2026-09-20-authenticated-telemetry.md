# Private per-boot telemetry authentication

September 20, 2026. M0.2c.3; F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13,
G0 item 5. Source/synthetic checks include the actual Java spool and operator
CLI. The subsequent dedicated Forge reference below qualifies a narrow authentic
signed stream. No model request or shared-desktop input occurred in either phase.
M0 remains in progress, G0 fails, G1–G5 are not run.

## Implementation

[Private authority issuance and verification](../../evaluator/src/strata_evaluator/telemetry_auth.py)
bind a random 256-bit key and challenge to an instance, campaign and epoch.
Issuance uses a fresh external operator directory and refuses game/source
locations or overwriting an existing grant. Key material never enters command
arguments, config JSON, output reports or gameplay packages. The authority
fingerprint binds policy, scope, challenge and key digest; the key path can
relocate without changing the authenticated identity.

[Forge telemetry 0.3.3](../../java/forge1192-telemetry/src/main/java/io/github/opencnid/strata/telemetry/SpoolAuthentication.java)
accepts explicit `ForgeTelemetryConfig/3` authentication configuration. It
checks the private 32-byte key and digest, then creates and forces an exclusive
authenticated boot claim before creating the event stream. Reusing that key
file's grant for another boot fails even if the first boot published nothing.
There is no automatic grant renewal or deletion of uncertain claims.

Each `AuthenticatedTelemetry/1` wrapper preserves the exact original UTF-8
GameEvent line in base64. HMAC-SHA256 covers a domain-separated policy,
authority fingerprint, challenge, sequence, previous MAC and SHA-256 of that
exact line. The verifier checks the authenticated boot claim, expected scope,
chain, encoding, record limits and complete original telemetry contract.
Changed authority/instance labels cannot be used with the same signature.
Altered, duplicate, reordered, mixed-source, truncated or incomplete streams
do not produce a successful inspection.

The existing bounded queue and durable cursor remain. Encoded bytes count
against the existing spool quota. The reader now also enforces cumulative
wire bytes if a file grows after its initial stat. Raw configurations 1/2 stay
explicitly unauthenticated; the thirteen top-level GameEvent/other record
contracts are unchanged. No recipe, item, world, command, packet or admin
control was added.

## Executed checks and retained failure

Windows x64, existing pinned Temurin 17.0.20.1+1, Gradle 8.8/ForgeGradle 6.0.42,
Minecraft 1.19.2/Forge 43.4.23 compile dependencies and Python 3.12.14.
Build-input, compiler, dependency locks and existing verification remain active.

| Check | Result |
|---|---|
| Telemetry Gradle test, test classpath, JAR/reobfuscation | Initial corrected build succeeds in 20 s with 19 tests; final rebuilt candidate has 20 XML tests, zero failures/errors/skips |
| Authenticated-spool, telemetry/config, craft-witness, scorer-scope and evaluator Python tests | 136 pass, zero skipped, 3.72 s; actual Java writer opt-in enabled |
| Final authentication guards | 24 Python tests pass in 2.09 s; cross-worktree key issuance and optional-client profile denial included |
| Gameplay package exclusion | Initial BUILD_REQUIRED; cached locked dependencies/TypeScript build restored, then 1 pass in 0.27 s |
| Targeted Ruff and whitespace | Pass |
| Operator CLI issue → actual Java spool → CLI private inspection | Three synthetic records, 20 sampled synthetic ticks; signatures/chain/boot validate; score eligibility false |

The first cross-language test failed after successful MAC verification: Gson
omitted the explicitly null `fastbench_sha256` field, violating the existing
payload contract. The writer now preserves explicit nulls. Java tests cover
that behavior and the corrected cross-language case passes; the original
failure is not described as a passing sample.

Other controls include a fixed cryptographic wire vector, changed/malformed
keys, signed foreign campaign/epoch/boot, changed private instance authority,
field duplication, malformed/oversized encoding, grant reuse, actual encoded
quota exhaustion, file growth, missing stop and unchanged offline replay.
Authenticated raw recipe/health/resource events remain rejected by the scorer.

The final built candidate module SHA-256 is
`0c0df4688da4e9e54f5e34bc7de08dca35738cda86113642d1e5ebf5a28367e1`.
The earlier CLI control used candidate
`7674fc579f3dd76a51818e0919e66017bcf58411e879e37a9e5ae04476d50c03`;
its manifest is retained. The final candidate also rejects a server authentication
plan on the optional client probe, before consuming its grant. Issuance rejects
other Git worktrees as well as this checkout.
The synthetic phase did not replace an installed client/server module or
qualify a pack. The subsequent reference used a distinct private server clone.
Private control artifacts are under
`C:/Users/Darian/.strata/evidence/2026-09-20-authenticated-telemetry-01`:
commands, synthetic marker, authority/key/claim, signed spool, report and tests.
Keep this directory out of public source and gameplay access.

## Authentic dedicated reference

Source commit `ec15bbd` and the final candidate above ran once against the existing
official E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23 distribution. Preparation
copied and hash-checked 18,215 files from the stopped development reference into
a distinct protected directory. The changes were explicit: server telemetry
0.3.1 → 0.3.3, loopback port 25566 → 25568, and a fresh private version-3
authentication scope. Existing 2–5 GiB heap limits, `nogui`, online authentication
and disabled automatic restart remained. No setup command, player connection,
gameplay primitive or inference occurred.

The existing bounded development runner held the server in its Windows Job
Object, captured logs, and sent one normal stop after ten seconds of readiness.
The private observer recorded the descendant tree and executable hashes, including
the pinned Java launcher and actual Forge process. This is operator process
evidence, not an adversarial process-isolation certificate.

| Authentic check | Result |
|---|---|
| Startup, bounded run and normal stop | Exit 0, no forced stop; server elapsed 156.203 s, surrounding reference 156.859 s |
| Signed stream and private CLI import | 13 records: startup, two recipes, nine health samples and stop; all signatures/sequence/scope/claim checks pass |
| Actual clocks | 188 final server ticks; 186 sampled ticks over 9.2608555 s; zero avatar exposure |
| Expert recipe | Six existing exact assertions pass, including expert ingredients/output and absent vanilla recipe |
| Derived negative files | Changed module bytes reject `TELEMETRY_AUTH_MAC`; duplicate record rejects `TELEMETRY_AUTH_SEQUENCE`; missing stop rejects `TELEMETRY_CLEAN_STOP_MISSING`; changed authority rejects `TELEMETRY_AUTH_CLAIM` |
| Original reference preservation | All 18,215 recorded source file hashes unchanged after the run; installed candidate hash unchanged |
| Offline replay and shutdown state | Reinspection identical; zero remaining Java processes |

Logs retain the distribution's existing warnings/errors; the bounded critical
failure inspector passes. This is not a complete pack-health or save-integrity
certificate. No 500-ms guardian test was performed, so previous failed samples
remain unchanged.

A separate plain-JVM invocation of the actual writer then attempted to use the
consumed authentic grant. It rejected with `FileAlreadyExistsException` before
opening a spool; the claim and signed stream remained byte-identical, with zero
synthetic events emitted. That check did not boot Minecraft a second time and
does not qualify a complete server restart/recovery.

Private root:
`C:/Users/Darian/.strata/evidence/2026-09-20-authenticated-telemetry-live-01`.
It holds the preparation/source manifest, launch plan, process observations,
key/claim, raw spool/logs, CLI report, negative derivatives and audit scripts.
Spool SHA-256:
`c8590676febb74a991bd7a0dce2e9ce88b552e978230b65f10008c215bed818b`.
Independent audit SHA-256:
`088eae61841f451cee8cbbf0b2a0947c9bfc274bd5084ce6accb38e49d4ccefd`.
Keep this evidence private; publish only the source and sanitized report.

## Qualification limits and next M0 work

A valid MAC proves possession of the issued key and integrity of the admitted
stream. It does not prove which OS process held the key, protect against a
compromised signer, verify setup/team membership, establish mechanical parity
or validate a score. Reports keep `scoring_eligible=false`,
`transport_identity_verified=false`, `process_identity_qualified=false` and
aggregate gates unpassed. Registration is still not authoritative scoring;
no raw witness was promoted to credit. Online telemetry API/lifecycle and full
checkpoint/recovery integration remain required.

Next bind authenticated setup/team/recipe/resource evidence and scorer controls.
The narrow dedicated stream reference is complete; do not repeat it unchanged.
Retain the previous 500-ms shutdown failures, five effective-file failures,
Mineflayer/E9E incompatibility, loopback canaries and remaining provenance/
recovery requirements. Do not use this module change as an unchanged shutdown
rerun to seek a pass.

Original OAuth allowance remains unchanged with one unresolved request and
$0.7554 reserved once. This telemetry key grant cannot authorize inference or
modify that budget; no model request was replayed.
