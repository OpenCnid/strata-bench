# Authentic observed level-walk trial

Operator-only. SPEC v0.2.33; M0.3b.1b.2b.2c.2 in_progress;
F01/F06/F09/F16, N01/N02/N03/N05/N06/N08, C09/C15/C18;
partial T01/T03/T07/T12/T13. No aggregate gate passes.

The [loaded native collision prerequisite](2026-09-19-native-collision.md) passes
13 cases. This fresh exact E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23 /
pinned Temurin 17 / minor34 trial uses the unchanged native JAR and 34 compiled
broker modules. No new motor or limits: 480-second client, 90-second worker,
1,000 primitive units, five-second action and 500 ms guardian process wait.

The public checker selects a one-block cardinal step from a fresh delivered
snapshot. It requires a centered level start, delivered supported ground and
two delivered air cells at start/destination; missing terrain fails. Selection
has no server/save/native access. Declared target tolerance is 0.2 blocks;
post-release drift and saved/public position tolerance are 0.02 blocks.
The scoped CLI dispatches once, checks terminal release, reached position,
known-terminal dedup, half-second settling and final fencing. Uncertain movement
is never replayed. World state and consumed resources are not restored away.

Independent private audit runs only after normal server stop. It compares player
position/dimension/rotation before and after, checks displacement over half a
block and target tolerance, compares delivered block IDs to boundary saves,
and reconciles intent/primitive/usage evidence. Selected references do not prove
complete conservation, causal scoring, checkpoints or full movement conformance.
Interruption/cancellation, damage, obstructions, modded/vertical geometry and
physical-input parity remain separate required cases.

Eleven harness files are pinned and Python scripts compile. Target selection
accepts the prior public snapshot and rejects an empty map; these are harness
checks only. The authentic result is below. Shutdown failures remain separate.
Private evidence: `C:\Users\Darian\.strata\evidence\2026-09-19-native-movement-01`.

## Actual result

The public level walk, settling, known-terminal dedup and final fencing pass
through 12 scoped CLI calls. The action emitted 22 ordinary motor events with
confirmed release and no resynchronization requirement. The request was not
replayed; one native intent, 24 total charged primitives (including safety
releases), 34 native frames and six native usage records reconcile.

All 15 private movement-audit checks and six saved-player checks pass. The
independent before-save position is (-50.5, 7, 10.5); after-save position is
(-49.42724892248985, 7, 10.5), exactly matching the reported settled position.
Displacement is 1.0727510775 blocks and target error is 0.0727510775 blocks,
within the predeclared 0.2-block target tolerance. Rotation and dimension agree;
player copies match their independently stopped boundaries. All 256 delivered
before/after block IDs match saved state. Selected inventory fields are unchanged;
complete resource/mechanics/scoring proof is still outside this narrow trial.
The after-copy contains five selected files totaling 17,637,503 bytes.

World readiness took 212.750 s without read retries. Bootstrap was 1,008.4497 ms,
initialization 291.8282 ms and gateway 2,768.9977 ms including guardian binding;
the independent startup deadlines passed. Child executor exit 0, parent worker
exit 1 due the retained shutdown failure: successful job call 1.4162 ms, then
500 ms kernel wait returned timeout after measured 503.5059 ms. Later client
exit does not override PROCESS_STOP_UNCONFIRMED. Overall procedure remains fail.
Client procedure elapsed 328.015 s; server saved/stopped normally at 520.328 s,
exit 0, logs complete. Arguments retired, zero Java processes, unchanged input
desktop and all 34 prelaunch broker hashes verified.

## Visual finding and remaining qualification

Both 854x480 PNGs pass CRC/zlib/scanline decoding. Visual inspection of frame 1
shows HUD, bow, selection outline and particles but **no rendered terrain**.
Frame 2 shows terrain/vegetation and HUD normally. Neither captures the operator
desktop. Preserve the incomplete initial frame; do not claim two complete world
scenes or graphics-ready admission. The current tag/recipe/body/world-render
barrier explicitly is not a complete graphics-state certificate. This finding
remains under the private-frame/native-render qualification, independently of
structured movement and the existing shutdown failure.

No runtime source changed, no paid inference or OS input. The independent saved
position supports this one ordinary level walk; it does not satisfy complete
movement, cancellation while walking, damage/obstruction, modded/vertical paths,
physical controls, performance or release gates. Next: native menu/quest lifecycle
and moving-action cancellation under fresh scope; retain all prior resources and
failed shutdown/visual samples.

A stopped effective-mode reinspection still has 263 pass / five fail: missing
BHMenu/NoMoreWorldSettings/InventorySorter/SophisticatedCore target files and
Create overlay mismatch. Static role/mod inventory review is preliminary; no
finding was excluded or converted to a pass. Official role-specific semantics
and the remaining exact-pack acceptance still require resolution.
