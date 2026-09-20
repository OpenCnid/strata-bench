# Authentic quest lifecycle and moving-cancellation trial

Operator-only. SPEC v0.2.33. M0.3b.3.2.4a and M0.3b.1b.2b.2c.2
are in_progress. F01/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08,
C09/C15/C18, partial T01/T03/T06/T07/T12/T13. No aggregate gate passes.

The exact E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23 / pinned Temurin 17
client remains minor34 b2a91155...; all 34 compiled broker modules and 97 launch
pins match the preceding [level-walk trial](2026-09-19-native-movement.md).
The dedicated non-input desktop leaves shared-desktop input paused. Current
operator/SYSTEM directory ACLs and desktop placement are not gameplay isolation.

Prepared procedure: use only scoped public CLI observations to select a visible
chapter/quest; open, navigate chapter/detail, read text, back and close. Check
known-terminal opening dedup without replaying an uncertain mutation. Select a
two-step level route from delivered supported ground and air cells. Wait for
public displacement over 0.05 blocks, then request cancellation once, confirm
release and fencing, and reject a fresh action in the cancelled epoch.

After the public checker has finished, two private read-only native snapshots
600 ms apart check settling. They never return to gameplay or authorize actions.
Independent stopped before/after player and region copies check actual effects;
selected reference fields do not prove complete conservation or checkpointing.
No world restore, account change, desktop input or paid inference is involved.

Bounds are unchanged: client 480 seconds, worker 90 seconds, action five seconds,
1,000 primitives, server 600 seconds plus normal-stop grace, guardian process
wait 500 ms. Cancellation motion search is at most 2.5 seconds; saved/native
position and settling tolerance 0.02 blocks. All failed samples remain evidence.
Prior startup rendering and shutdown failures remain open independently.

Private evidence:
`C:\Users\Darian\.strata\evidence\2026-09-19-native-quest-cancel-01`.
Preparation is not execution evidence. Actual results will be recorded below.

## First attempt: startup failure before gameplay

`worker-01` failed before bridge/world/worker startup. Exact installed CTM
1.19.2-1.1.6+8 threw `HashMap$Node cannot be cast to HashMap$TreeNode` during
TextureStitchEvent.Pre, at ResourceUtil.getMetadata line 64. The upstream
[CTM concurrency issue](https://github.com/Chisel-Team/ConnectedTexturesMod/issues/176)
describes this signature and an unsynchronized metadata cache. This is a matching
failure report, not proof of this run's exact thread interleaving or a repaired
dependency. No mod was removed, replaced or patched.

The client procedure ended after 113.985 s; server normal save/stop passed at
283.672 s with complete logs. Zero Java, argument retirement and unchanged input
desktop were verified. All five selected before/after save files are byte-identical.
There were no worker actions, native intents/primitives, frames or inference.
Gameplay checks remain not_run. Logs, crash report, hashes and the failed sample
are preserved. One fresh bounded startup uses unchanged runtime artifacts/limits;
this is a new trial after confirmed terminal processes, not a gameplay replay.

## Second attempt: opening passes, stale navigation fails

`worker-02` reached world readiness in 169.406 s without read retries. Actual
quest opening, local book-state confirmation and known-terminal dedup pass.
Chapter selection then returned ACTION_UNKNOWN with confirmed release and
resynchronization required. The checker stopped; detail/back/close and moving
cancellation were not_run. Two broker actions but only one native intent, four
total charged primitives and 14 native frames reconcile. The private diagnostic
was UNCLASSIFIED_NATIVE_FAILURE; its original native code cannot be recovered.

The recorded root catalog revision was 1; the checker then read a quest catalog
at revision 2 and incorrectly retained root revision 1 for chapter selection.
The actual catalog deliberately advances its revision when query focus changes.
The [regression test](../../java/forge1192-client/src/test/java/io/github/opencnid/strata/client/GameQuestNavigationTest.java)
now composes the real catalog and navigation motor: that stale selection rejects
with GAME_QUEST_CHANGED before emission; an explicitly refreshed root selection
succeeds. This is consistent with the real failure, not recovery of the discarded
native code. The harness will refresh/revalidate its chosen chapter before a new
trial. No production contract or runtime artifact was relaxed.

Nineteen focused Java tests pass (zero skips/failures/errors). The first Gradle
invocation did not start because JAVA_HOME was unset; the rerun explicitly used
the pinned JDK and exact FTB Library artifact. Synthetic sources/callbacks test
the revision invariant; they do not establish authentic navigation success.

Independent saved player position and selected inventory fields remain unchanged;
256 observed before/after block IDs match stopped saves. Private settling reads
agree. The overall reference audit correctly fails because navigation/movement
did not complete. Its first collector rejected native block coordinates encoded
as integral doubles; a separate v2 collector asserts exact integrality before
conversion, preserving the original script/failure and strict saved-world reader.
The dependent startup audit initially lacked the failed collector's output and
was then run after correction. No runtime change followed from that correction.

Bootstrap 428.9222 ms and initialization 294.6583 ms pass their independent
deadlines. This sample's guardian shutdown passes, with reported wait 437 ms;
earlier shutdown failures remain open. Client procedure 272.172 s; normal server
save/stop 440.782 s. Zero Java and argument retirement verified. One 854x480 PNG
decoded and visually shows terrain/HUD; no quest-menu image was taken. The second
world frame was intentionally not requested after the unfinished menu lifecycle.
Complete UI/resource/geometry/cancellation/isolation/reliability gates stay open.

## Third attempt: quest lifecycle passes; cancellation reference and shutdown fail

`worker-03` refreshes the root catalog after inspecting quests and rechecks the
chosen chapter before selecting it. Runtime artifacts, scope rules and limits
are unchanged. The public checker passes across 53 scoped CLI calls: open, known-terminal dedup,
chapter/detail selection, readable text, Back, Close, an in-flight walk cancel,
released/fenced observation and rejection of a fresh action in the cancelled
epoch. Five ordinary quest mutations plus one walk produce six native intents,
39 charged primitives, 72 journal frames and 15 reconciled native usage records.
No native call failure or duplicate native intent was observed.

**The stronger stopped-position cancellation case fails.** The checker observed
1.0727510775 blocks of displacement before asking to cancel; its end-to-end CLI
cancel call took 297 ms and returned cancelled/released/resynchronization-required.
The saved position changed from (-49.42724892248985, 7, 10.5) to
(-50.5, 7, 11.357169526313502), a net displacement of 1.3731476509 blocks.
The target was (-50.5, 7, 11.5); saved target distance 0.1428304737 is already
inside the declared 0.2-block tolerance. Therefore this does not prove stopping
short of the destination. Preserve the failed predicate and the public success
separately; do not relax its threshold or describe full movement cancellation as
verified. The 297 ms CLI measurement also cannot certify the separate 250 ms
responsive-worker target; it includes process startup/transport and no isolated
worker timing was established here.

The stopped reference matches all 256 before/after observed block IDs and the
private settled position/dimension. Both private samples 600 ms apart agree;
selected inventory fields are unchanged. Seven of eight player checks pass, with
the target-arrival condition failing. Twelve of thirteen broader audit checks
pass; the aggregate remains fail because it requires all player checks. This
does not prove complete resource conservation, GUI rendering/parity, hidden/team
isolation, occupied crafting, submissions/claims or machine mechanics.

World readiness 167.218 s, no read retries; bootstrap 1,197.3598 ms,
initialization 330.9449 ms, overall gateway 3,304.8975 ms including guardian
binding. Both independent startup deadlines pass. Public executor exits 0;
worker parent exits 1 because guardian termination fails again: successful job
call 0.8438 ms, then the unchanged 500 ms wait times out after measured
507.6092 ms. Later process exit does not turn this into a pass. The client
procedure ended at 266.843 s; server saved/stopped normally at 426.25 s.
Arguments retired, zero Java, unchanged input desktop, all 34 broker and 97
launch pins verified. Both 854x480 PNGs decode and visibly contain terrain/HUD;
neither is a quest-menu reference or evidence of complete graphics readiness.

The complete procedure remains fail. Next: test cancellation with a fresh,
observed route that leaves enough distance to distinguish cancellation from
arrival, and retain the loaded native quest/menu/JEI/resource/visual qualification
work. Preserve the current saved position and all costs; no gameplay restore or
inference occurred. CTM startup and repeated shutdown/render failures remain open.
