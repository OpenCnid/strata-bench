# Authentic native settings round trip and cold readback

2026-09-20. Operator-only. Partial M1.1a.2.2/.2.3a/.2.3b, F06/F09/F16,
N01/N02/N03/N04/N06/N08, C10/C11/C14/C18, T05/T07/T13. Two narrow
development cases pass; complete T05/G1 remain unqualified.

The existing [title-screen probe](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/ClientSettingsProbe.java)
is enabled for the first time in the authentic dedicated E9E 1.27.0 client.
The installed minor-34 JAR is unchanged:
`b2a91155a7698d3ce6095ae7c4005827ea10c7f3623bfa086312f29d56916896`.
Forge 43.4.23 / MC 1.19.2 / Java 17.0.20.1, official launcher/library pins,
current operator source hashes and each private runner are recorded. The source
checkpoint is `11c18f2`. No source/game artifact is rebuilt or substituted.

Both boots use a fresh non-input Windows desktop, the existing independent
Java lifetime guard, a 480-second outer lifetime and a 280-second readiness
limit. Server-join arguments and game/frame bridge properties are removed.
There is no server launch, physical input, live model, campaign or scored run.
The existing cached licensed account supplies protected temporary launch
arguments; only their digest and expiry are recorded outside credential storage.

## Apply, readback and rollback

The fresh private `roundtrip-01/transaction` directory enables
`strata.settingsTransactionDirectory`. On the title screen, with no player or
world, the native probe verifies its one allowed binding's source and registered
object identity:

- Binding: `curios:key.curios.open.desc:0`.
- Exact Curios artifact:
  `1f7742d6c4f6b6cd8d106e54181255c2d264194ba232d42901ef90da6b91e635`.
- Public registration: `KeyRegistry.openCurios`.
- Native settings fingerprint:
  `2f5a46d76c76e36da56a35be018559cc2b1c9159557d9982b828f86ccda61209`.

The initial value is unbound. Applying `key.keyboard.f13` yields
`applied_pending_verification`, with `committed:false`. Exactly that runtime
binding changes among 253 mappings. The options file differs by exactly its
owned field replacement; every unrelated byte is preserved. The probe always
attempts rollback in the same client tick and releases native input state.
It returns `rolled_back`; the complete before/restored runtime maps and file
digests match. It never presses F13 or establishes F13 as a usable physical key.

The native journal has six correctly sequenced/hash-linked frames: profile,
observed, prepared, applied_pending_verification, rollback_prepared and rolled_back.
Its SHA256 is
`e93e66eafa852f2a1eb9000ba39fdc2e12554d3cb405d22af1b24b345d406395`.
The native report is ready after 126.468 s; its SHA256 is
`154f82de19b6adfe0f9b871fa07edbf8714d47d76aa1d3498fd3dddf560b3e85`.
The procedure finishes in 127.015 s with transaction and lifetime results pass.

## Independent cold readback

After verifying the first process is terminal and the options file restored,
a distinct `readback-01` process enables only
`strata.settingsDiscoveryDirectory`. No transaction property or forward apply
is present. Its 253 runtime encodings match the prior restored map, and every
persisted value matches its runtime value without persistence ambiguity.

Comparison uses each stable key/registration occurrence after removing the owner
prefix. This matters because the general discovery module correctly retains
34 source-known vanilla owners and 219 unresolved mod owners; it does not gain
general Curios or mod mutation authority from this test. Duplicate comparison
keys reject. Discovery keeps `supported:false`, an empty tested physical pool,
`atomic_cas:false`, and all consumer/mutation flags false.

The discovery arrives after 124.625 s; the procedure finishes in 125.125 s.
The captured snapshot SHA256 is
`86e75c57816940a2fc3a668f5caba8bc1a1b1d0022d9231c8eec3070bf3ef068`.
The existing strict `python -m mcbench.client_discovery` operator audit executes
against that snapshot and the stopped profile's options file: 253 bindings,
format pass, gate not_run. Its SHA256 is
`a0775cc5a058197575d98e1711af8de7fac074071d61da8983978c75206fa4c5`.

Both boots retain options SHA256
`38b89fb282ee5c4cc0ecd9d3180dbc76b43a9aa7624e1d970ece9a07fda03833`.
Both independent lifetime guards emit a confirmed process-stop receipt with
the existing coarse `termination_wait_ms:250` field. Their full private journals
are retained; this is not a new high-resolution authentic-world timing result
and does not reverse the [current T07 failure](2026-09-20-guardian-live.md).
Both input-desktop identities are unchanged, all Java processes are absent,
no outer desktop watchdog fired, and both temporary argument files are retired.

## Limits and next evidence

Raw plans, pinned arguments templates, runners, guarded launch records, native
reports/journal, options before/applied/after, discovery, audit and client logs
stay under external `C:\Users\Darian\.strata\evidence\2026-09-20-native-settings-01`.
No credential cache or populated argument file is published. Neither boot is
repeated to improve an outcome. Local test counts from earlier implementation
remain historical; these are new authentic acceptance samples.

This closes the executed positive round-trip and rolled-back-map cold-readback
cases only. It does not establish a successful conflict repair, intended versus
competing effects, a tested key pool, modifiers/GUI/polling parity, full native
CAS against foreign writers, power-loss durability, interrupted patch recovery,
cross-client isolation or a gameplay settings capability. Repair time/cost
integration and host isolation remain open. Next exercise the private bridge's
interrupted pending transaction and conservative status/rollback recovery with
an exact journal and no forward replay; retain separate mid-write/conflict cases.
G0/T07 remain fail; G1–G5 remain not_run.
