# Two authentic settings write-boundary recoveries

September 20, 2026. Operator-only. Partial M1.1a.2.3c.2b, T05/T07/T13;
this does not close M1 or G1. Source `bb22448`, client SHA256
`6332576ea722a9ab49255cb0187851b22e4e9f4fb8e42f70dbbdc19eb723f051`.

Four actual E9E title clients execute two distinct crash/recovery pairs on the
separate non-input desktop. Each crash calls Runtime.halt(86) at its selected
write boundary. Its fresh recovery process calls status, snapshot, rollback,
snapshot and status, with **zero apply calls**. The source-bound Curios setting
is unbound initially; F13 is a stored test value, never physical input.

| Boundary | Captured interrupted state | Crash / recovery elapsed | Independent audit |
|---|---|---|---|
| apply_runtime_written | Prepared journal, runtime changed, original disk | 137.844 / 139.078 s | pass |
| apply_prepared | Prepared journal, original runtime and disk | 144.578 / 147.578 s | pass |

Each audit verifies one forward transaction, the original journal prefix,
five final frames ending in rolled_back, all 253 restored runtime/persisted
bindings and exact original options bytes. All four processes are terminal,
temporary arguments retired, input desktop unchanged and Java count zero.
No world/server, inference or gameplay admission occurs. This tests abrupt
process loss at explicit boundaries, not power loss or arbitrary setter faults.

The separately pinned profile is `ctm-startup-bg1-diagnostic/1`, with
`-Dmax.bg.threads=1`; native fingerprint
`42541e18f97c1bc4a03254af60ade0a40bb6235b68d17bc2dd916040f66574f8`.
Existing 480-second lifetime, 280-second readiness and five-second API limits
remain. The [default-profile CTM startup failure](2026-09-20-settings-crash-startup.md)
is retained. These successful starts do not prove CTM reliability or global
serialization; see the [exact-source review](2026-09-20-ctm-source-review.md).
JVM flags must accompany artifact fingerprints when comparing conditions.

Private immutable evidence is under
`C:\Users\Darian\.strata\evidence\2026-09-20-settings-crash-native-02`.
Audit SHA256 values are:

- apply_runtime_written: `50abcd3108aa99e13005229370f501b30497c8645adfc68ef402c246fad1bcf4`.
- apply_prepared: `7f27a303873b1c19cc5026200af70b29b56dddb5c68975b1c2df30c04bc0dc3d`.

The apply_options_written and three rollback-boundary pairs remain **not run**.
Following the user's milestone-priority correction, the next implementation
work returns to G0's exact-pack mechanics and independent server evidence.
The four pending recovery cases, physical key effects, foreign runtime changes,
writer isolation and full settings acceptance remain required M1 work.
