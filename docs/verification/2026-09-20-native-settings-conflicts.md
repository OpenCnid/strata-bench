# Authentic foreign-options settings conflicts

2026-09-20. Operator-only. Partial M1.1a.2.3c.3, F06/F09/F16,
N01/N02/N03/N04/N06/N08, C10/C11/C14/C18, T05/T07/T13. The executed
disk-change negatives pass; in-memory foreign changes, qualified CAS/isolation
and full keybinding effects remain unverified.

Source checkpoint `4ade4e5`; unchanged E9E 1.27.0, Forge 43.4.23, Java
17.0.20.1 and installed minor-34 JAR, SHA256
`b2a91155a7698d3ce6095ae7c4005827ea10c7f3623bfa086312f29d56916896`.
The exact Curios artifact/registered object and fingerprint are those in the
[round-trip report](2026-09-20-native-settings.md). A fresh protected broker
journal/session and non-input desktop are used. The five-second calls,
480-second client lifetime and 280-second readiness limit are unchanged.
There is no server/world, physical input, live inference or campaign admission.

## Executed negatives

1. Capture the original snapshot, then toggle only the fixture-owned `bobView`
   options field on disk. An apply using the previous revision/digest returns
   `SETTINGS_REVISION_CONFLICT`. There is no active transaction, all 253 runtime
   values are unchanged and the foreign disk bytes remain exact. Remove only
   that known injection after matching the full expected current bytes.
2. Take a fresh snapshot and perform one Curios unbound-to-F13 apply. Confirm
   pending state and the exact owned-file replacement. Inject the unrelated
   options-field change again. Rollback returns `SETTINGS_ROLLBACK_CONFLICT`,
   status stays active at rollback_conflict, runtime values remain pending and
   all foreign disk bytes are preserved. A distinct apply returns
   `SETTINGS_RECOVERY_REQUIRED`, with no further mutation. Remove only the known
   injection after matching the full expected current file.
3. Replace only the persisted owned field's F13 encoding with F14, leaving
   runtime unchanged. Repeat rollback/status/snapshot/new-apply checks: the
   same conflict and recovery-required rejections preserve both states. Remove
   only the injected F14 encoding after checking exact expected current bytes.
4. Roll back the existing transaction. All 253 runtime and persisted values
   match their original state without ambiguity; the options bytes are exactly
   original. Final status is rolled_back, committed:false.

F13/F14 are file encodings in this procedure, not emitted or tested physical
keys. The operator's read/check/atomic replace is a controlled fixture action,
not qualified filesystem CAS or proof that foreign writers are excluded.
Each of the six injections/removals has a separate private intent, byte snapshot
and receipt. On error the runner preserves the failed state and may remove only
its exact known foreign edit after process termination; it never replays apply.

## Evidence and limits

The independent audit passes five expected rejection codes, one successful
apply and one successful rollback, six exact owned interventions, preserved
unrelated bytes, complete restoration and the ten-frame journal hash chain.
There is exactly one prepared transaction. The stale and blocked transaction
IDs never become prepared. Journal phases are profile, three observed frames,
prepared, applied_pending_verification, two rollback_conflict frames,
rollback_prepared and rolled_back.

Journal SHA256:
`bc6846adbe2a8886019d4eaf3526d1051b35c50776075e5799b09d858482bea2`.
Audit SHA256:
`d8559c8f82fa369780de8590da70d3df9739db4fc887f2dd55efa127ad95807c`.
Restored options SHA256:
`38b89fb282ee5c4cc0ecd9d3180dbc76b43a9aa7624e1d970ece9a07fda03833`.

Native readiness takes 126.438 s; total procedure time is 128.719 s. The
independent base guardian confirms stop with a coarse 344-ms field, the held
process observer signals, zero Java processes remain, input desktop is unchanged
and the protected temporary launch arguments are retired. This does not replace
the failed authentic-world high-resolution guardian timing case.

All plans, sources, option snapshots, API intents/receipts, journal, audit and
client logs remain external under
`C:\Users\Darian\.strata\evidence\2026-09-20-settings-conflicts-01`.
Bearer descriptors remain in separate protected broker storage. No credentials
or raw evidence are published; no inference budget is spent. No failed authentic
attempt or changed acceptance threshold preceded this passing sample.

The earlier [two-client pending recovery](2026-09-20-native-settings-recovery.md)
remains separate evidence. Next implement explicit operator-only crash points
between durable prepare, native mapping update and options replacement for both
apply and rollback, then qualify their recovery on the real runtime. General
ownership, physical input/effects, in-memory foreign changes, cross-client
isolation, repair costs and full T05/G1 remain open. G0/T07 remain fail;
G1–G5 remain not_run.
