# Private game-frame evidence — September 19, 2026

Operator-only. M0.3b.2c.3c.2b.1 is implemented_unverified for full production use.
SPEC v0.2.28, private policy `private-main-target-pre-display-png4/1`.
Coverage: F01/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08,
C02/C09/C15/C18, partial T01/T03/T06/T07/T12/T13. No aggregate gate passes.

**Actual separate-desktop capture passed:** two 854×480 PNGs from exact E9E
1.27.0 / MC 1.19.2 / Forge 43.4.23, followed by live wrong-screen rejection and
no retry after correcting that failed request. The read-only game API survived
the diagnostic failure; screenshots:false/actions:[] remained unchanged.
No world/server connection, game mutation, physical input or inference ran.
Input desktop stayed unchanged; guardian requested-stop termination confirmed in
235 ms, total process elapsed 127.5 s. Owned Java was subsequently confirmed absent.

[ClientFrameProbe](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/ClientFrameProbe.java)
uses a separate optional exact SRG hook before Window.updateDisplay in
Minecraft.runTick, after main-render-target blit. The pinned mapped/native bytecode
was inspected; the standard Forge render-end event is earlier than profiler
rendering/blit and was not used. Actual session/frame records prove the new hook
executed in this run; they do not prove the nine existing JEI hooks executed.

The native Screenshot.takeScreenshot readback/PNG path copies the client's own
main render target. Texture binding and pack alignment are restored in finally;
nonzero pixel-pack buffer or row/skip state, wrong texture dimensions and
noRender reject. No keypress, screenshot notification, OS-window capture, cursor
movement, camera or screen action is dispatched. Drawing outside that render
target, the OS compositor and hardware cursor are outside this capture's coverage.
Complete native graphics-state fault/reference/physical-key parity remains open.

[PrivateFrames](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/PrivateFrames.java)
enforces a new disjoint directory, ten-minute session, four frames, at least one
second spacing, 1920×1080 and 12 MiB PNG bounds. Requests are strict 4 KiB records
with exact session/next sequence/screen and a ≤10 s deadline enforced against
UTC and a converted monotonic deadline. Intent is durable before readback;
PNG and receipt are separate forced writes. Failure stops capture, partial files
remain unqualified, and a reused directory cannot restart the session. This is
private diagnostic storage, not a complete production archival/sandbox service.

Verification:

- Full Java test/build/writeTestClasspath passed in 28 s after adding nine
  synthetic PNG/clock/file tests. A focused nine-test build passed in 15 s after
  adding noRender rejection. Final focused ten-test/build passed in 16 s after
  adding monotonic-expiry protection and its backward-wall-clock regression.
  Final XML records ten tests, zero failures/errors/skips. Synthetic tests cover
  positive files/receipt/PNG, no replay, count/spacing, strict request negatives,
  expiry, wrong screen/dimensions, source failure, partial evidence, root/restart
  rejection and PNG bounds. They do not exercise native GL or physical inputs.
- Initial real run initialized the new hook/session, but request 1 expected the
  exact vanilla TitleScreen class. It failed FRAME_SCREEN_MISMATCH before any
  pixels/intent. Exact installed PackMenu 1.19.2-5.1.0 bytecode confirms
  shadows.packmenu.ExtendedMenuScreen extends TitleScreen. The source artifact
  SHA-256 is 4d27944351c109798c6f1fa5d0f4f36508b78b2f7ffd45cbca8c71087b67f860.
  The failure is retained; screen matching was not weakened.
- A fresh process/bridge/capture directory requested that exact PackMenu class.
  Startup/session ready in 122.703 s. Frame 1 is 930,916 bytes; frame 2 is 943,899
  bytes. Native capture elapsed times, including request/readback/encoding/durable
  output work up to receipt construction, are 141.7151 and 101.2564 ms. These two
  timings are not a latency/performance certificate or overhead comparison.
- Independent bounded PNG parsing validated every chunk CRC, zlib stream and
  scanline filter, dimensions, opaque RGBA and hashes. Distinct colors: 19,497
  and 20,459. Visual inspection through the saved images shows the Enigmatica 9
  title/menu/background and Minecraft 1.19.2 footer. Frame 1 includes the fading
  Mojang loading overlay; frame 2 has the clear menu. Small-window footer/menu
  text overlaps are retained. A matching underlying screen class does not imply
  no overlay or complete visual stability. No operator desktop content appears.
- Request 3 used a deliberately wrong screen class and produced
  FRAME_SCREEN_MISMATCH. Replacing it with a valid request did not create another
  intent/image. The read-only game API still responded, then the guardian stopped
  Java. The driver retained its second-run summary member named frames-02; native
  session/request/intent/frame/failure schemas are unchanged, and verification
  uses their explicit files. Raw driver output remains unmodified.
- Frame-directory ACL verification passed for current operator and SYSTEM.
  Both temporary session-argument files were retired after their respective
  stopped runs. No original CurseForge profile mutation. Same-user filesystem,
  process/network or evaluator isolation is still unqualified.

Candidate/private-copy JAR SHA-256:
ef06b88892ea06f551d137ed0c0fc8bba99e5e5cfe8577b7d517207619a5d88a.
Public capability minor remains 33 with the same structured contract; the changed
JAR fingerprint and private capture policy distinguish this engineering run.
The original CurseForge profile remains minor 30 / f10e7ad6… . Dedicated-copy
options, official bootstrap/library pins and 4 GiB heap follow the preceding
[startup evidence](2026-09-19-desktop-client.md). Raw game logs remain private.

Private artifacts:
`C:\Users\Darian\.strata\evidence\2026-09-19-private-frames-01`.
The first run remains under frames/live-01; the successful capture/intentional
failure sequence is under frames-02/live-02. Source/compiled-callsite inspections,
test XML, scripts, PNG decoder/visual checks, hashes and final collector are there.
An initial JAR-manifest raw-substring check failed on standard line folding;
unfolding confirmed both configurations without changing the artifact.
The final collector initially expected a development method name in the
reobfuscated JAR. Pinned SRG-to-official mappings confirm bindTexture and
_pixelStore correspond to the compiled calls; the corrected collector passed
585 local links, 13 source snapshots, artifact/callsite checks and git diff check.
This was a collector correction; the tested client artifact did not change.

Remaining .2b.2/.1b.4 work: world/menu/recipe/machine visuals correlated with
structured observations and independent server evidence, full Forge guardian and
worker integration, focus/pointer/physical-key behavior, complete graphics-state
failure/overhead/reference checks, production resources/archival and actual
security principals. Loading/capturing a title screen cannot satisfy those gates.

Subsequent [authentic level-walk evidence](2026-09-19-native-movement.md) records
a new initial-scene failure: the first PNG decoded correctly and contained the
HUD/selection outline but no terrain; the later PNG contained terrain normally.
The native connection/tag/recipe/world-render barrier and successful PNG decoding
therefore do not certify a complete initial scene. Preserve both images and the
failure; full graphics-readiness and world/menu/reference qualification remain open.
