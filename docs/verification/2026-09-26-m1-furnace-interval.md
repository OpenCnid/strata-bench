# M1.5b.8 — native furnace interval candidate

The telemetry0.3.18 / ServerStarted19 candidate adds complete ordered furnace
server-tick observations and actual object lifetime identities. This is
`implemented_unverified`: focused source checks pass, but transformed Forge
execution, retirement/replacement and a prior-bound continuous operating window
remain unverified. It does not pass T10 or G1.

Scope: F10/F16, N01/N04/N06/N08, C12/C18/C24 and T01/T06/T10, inherited from
M1.5b.7. The baseline is2066303 and the successful, separately identified
[operation08](2026-09-26-m1-furnace-transitions-native.md). All earlier failures,
consumed decisions, held amounts and M2–M7 dispositions remain unchanged.

`thermal1192-native-furnace-server-tick/1` observes actual `tickServer` entry and
return, linking the existing processing, completion and start/refund events by
ordered transaction IDs. Inline before/after stages cover input/output transfer,
charging, activation and process-off. The reader checks the exact pinned native
path order, every sampled state boundary and the existing child arithmetic.
Completion arithmetic uses native resolved facts; an independently registered
recipe/fixture plan remains necessary. Transfer/charge resource changes are
explicit observations, not proof of resource provenance or player attribution.

The Java registry keys on actual tile object identity, level object and position.
Each activation starts a new registry. Removal, chunk unload and reactivation
retire observed identities; a replacement at the same coordinates or a reused
retired object obtains a new identity. Ordinals and world ticks must increase.
The lifetime quota is64 ever-issued identities and the tick quota is16,384 total;
retirement cannot reset either. Each tick permits at most four child events and
ten ordered steps. Missing, nested or unpaired boundaries fail rather than
fabricating an uninterrupted interval.

The new private records are `NativeFurnaceServerTick/1`,
`NativeFurnaceServerTickRefusal/1` and `NativeFurnaceLifetimeEnd/1`. Both online
receipt and offline inspection require the new startup policy and exact
supported profile; all records share the transaction duplicate fence. Offline
inspection joins child scope, event order, lifetime and clock continuity, and
rejects orphan children or identity reuse. A complete authenticated, cleanly
stopped stream is required before returning a report. Native refusals and tick
gaps remain explicit rejected observations.

`qualify_window` accepts only exact inclusive bounds, with no trimming or gap
filling. Every tick must exist, world ticks and ordinals must be consecutive,
inter-tick states must join, and no rejection or lifetime end may occur within
the window. Its result is sampled lifetime continuity only: prior registration,
setup/team qualification, loaded-code authentication and scoring eligibility
remain false. The current V4 machine plan has not been extended to admit these
windows. Unsupported resource paths, fluids, automation, augmented profiles and
full setup/resource provenance retain their wider contract gaps.

Verification executed:

- 285 distinct Python cases pass; four existing native opt-in cases are skipped.
  The initial focused selection passed280, followed by five additional interval
  cases; overlapping runs are counted once. The41 interval cases cover active,
  inactive, completion/restart and refund/stop paths, exact window bounds,
  child/state/order/scope gaps, retirement, identity reuse, quotas, native
  refusals, authenticated import and online receipts. Related transition,
  processing, registration, capture, telemetry, setup and gameplay-package tests
  remain in the focused selection.
- 20 selected Java cases pass with no failures/skips, and the offline
  reobfuscated artifact build passes. Four lifetime-registry and three interval
  bytecode cases extend the prior13 cases. These inspect the pinned native
  instruction sites and compiled hooks; they do not execute transformed Forge.
- The inspected inheritance chain delegates removal to BlockEntity; no selected
  subclass overrides its clearRemoved/unload hooks. The initial guessed
  RedstoneControlBlockEntity lookup failed and is retained with the subsequent
  exact hierarchy inspection. This read failure is not an integration result.
- The original operation08 seal verifies and the current authenticated reader
  reproduces its archived329-record inspection exactly. No older evidence is
  migrated or replayed.
- The initial63 Ruff findings and pre-format test source remain archived.
  Formatting and the intentional pytest-fixture import annotation resolve them;
  final focused Ruff checks pass. The intermediate build is retained separately
  from the final candidate after the child-step quota guard.

Final candidate:146,855bytes, SHA-256
`061712cee52408d7514da3879c538ccb4cc496e485c378c43f23409decca2cf0`.
The build additionally pins Forge1.19.2-43.4.23 SRG artifact
`b33801d8996d5579c7e5fe98224d05483c165f8d45a97d3e1d67e13bbe5d367b`.
Private archive: `2026-09-26-m1-furnace-interval-source-01`.

No new game/model execution or artifact installation occurred. The durable
accounting exposure remains4,887,796microUSD; D18/D19 remain M0-only. Next prepare
a fresh bounded native reference with interval criteria fixed before launch,
then verify actual retirement/replacement and rejection controls. Full operating
window registration, setup/team/loaded producer, alternate/negative scorer
controls, parity/isolation and the remaining keybinding/native-host/probe G1
contracts remain required. Preserve the successful earlier positive slices and
all historical failures without expanding their claims.

Final audit passes:813 source pins,451 unique/preserved milestone IDs and1,886
local links; append-only progress and the SPEC insertion are verified. All40
accounting tables and installed client/server pins remain unchanged, with no
owned runtime. The69-file/3,197,911byte private archive verifies under seal
`dc219511f11fbcb400e88c8216873a181ca624eaf7c986b03386ef02550601bc`.
This pointer follows the archived document snapshot; the archive is unchanged.
Authentic interval capture and full G1 remain not_run.
