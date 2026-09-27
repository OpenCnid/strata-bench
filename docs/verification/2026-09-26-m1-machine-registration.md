# M1.5b.2 native recipe registration candidate

From `5057204`, add the native registration lineage missing from the
[completion collector](2026-09-26-m1-machine-producer.md). M1.5b.2 is
**implemented_unverified for authentic capture**. M1/M1.5 remain in_progress;
T10/G1 remain not_run. No game/model dispatch, installation, spending change or
unrelated M2-M7 work occurs. All40 real controller tables remain unchanged at
$4.887796; historical holds, failures and consumed decisions remain intact.

## Evidence-driven implementation

Inspect exact installed Thermal/CoFH bytecode for `ThermalRecipe`,
`ThermalRecipeManagers`, `AbstractManager`, `TCoreRecipeManagers`,
`SerializableRecipe` and the actual refresh callers. A class-byte search locates
`TCoreCommonSetupEvents`: its reload listener stores the server recipe manager,
then its tags-updated handler refreshes the server managers. This can precede
MinecraftServer construction; do not assume that initial registration already
runs inside a live server tick.

Furnace refresh first clears its map, adds converted ordinary cooking recipes,
then adds explicit furnace recipes. Conversion returns a new machine recipe;
registration can return several internal recipes for concrete alternatives.
The native converter's generated ID is not a reliable key for source identity.
Record the actual object chain, including both IDs, rather than recreating a
recipe or guessing from its input/output.

[FurnaceRegistration](../../java/forge1192-telemetry/src/main/java/io/github/opencnid/strata/telemetry/FurnaceRegistration.java)
and the two private Mixins observe those fixed native callbacks. Bind the
initial recipe-manager object from `refreshServer`; later require identity with
the live dedicated server's recipe manager and `byKey`'s actual registered source
object. Direct furnace recipes and native SmeltingRecipe conversions have
distinct origins. Other source subclasses remain unsupported, not removed
from the wider contract.

[RecipeRegistrationIndex](../../java/forge1192-telemetry/src/main/java/io/github/opencnid/strata/telemetry/RecipeRegistrationIndex.java)
uses identity maps, a65536-entry bound per map,256-character names, positive
generation through2^53-1, complete callback pairing and a single refresh-owner
thread. Ordinary rebuild/clear invalidates old entries. Null native returns
create no binding. Equal objects, equal IDs or equal outputs do not merge
sources. Structural/quota/thread failures poison the observer; its next callback
cannot silently recover authority. It performs no recipe registration itself.

The collector observes the same registration at all three completion phases.
Native furnace phases/2, module0.3.15 and startup16 carry this lineage in
`NativeFurnaceCompletion/2`; refusal/2 adds explicit unobserved/changed-registration
reasons. Prior module0.3.14/phases1 remains a separate identity with its sealed
artifact retained. Existing history6 and clock policy remain unchanged.

[Private models/readers](../../evaluator/src/strata_evaluator/machine_capture.py)
require the new startup, registration-hook declaration, direct/converted source
domains and complete typed metadata. Offline and pipe paths reject mixed
profiles and generation rollback. The raw records remain unscorable, with
recipe-registration qualification, loaded-code authentication and scoring
authority false. No source binding is promoted from marker presence alone.

## Executed verification

- Python new registration and prior capture selection: **65 pass**,2.68s.
  Covers direct/converted facts, scorer rejection, missing/malformed registration,
  bounds, unknown/promoted fields, signed stream and startup-prefix checks,
  profile mismatch, offline/online rollback and explicit refusals.
- Focused telemetry/pipe/package compatibility selection: **48 pass,1 opt-in
  native case skipped**,5.20s. Total113 distinct passing Python cases. The skip
  is not authentic integration evidence; the actual compiled gameplay package
  check is not a runtime-isolation claim.
- Offline Java compile, selected `RecipeRegistration*`/`Furnace*` tests and
  reobfuscated module build pass. Final14 Java cases: seven registration-index
  cases, one installed-registration-bytecode/compiled-hook check, and six retained
  furnace phase/bytecode checks. All run, none skipped. Verify actual pinned
  callback descriptors/return counts and refresh ordering; these are not a
  transformed Forge execution.
- Focused Ruff and `git diff --check` pass. Test/build processes terminate.

The first13-case Java selection passed. Review then added permanent poisoning
for native reflection failures and bounded name validation, with one added
negative case; retain intermediate outputs and final14-case results. No failed
game job was retried and no gate or deadline was weakened.

Private evidence/source root:
`C:/Users/Darian/.strata/evidence/2026-09-26-m1-machine-registration-01`.
Installed API inspection commands/output, test reports, source pins, module and
durable-state audit remain private. D18/D19 still authorize M0 inference only.

## Next acceptance work

Verify actual transformed hooks and native registration/capture under owned
Forge launch custody. The current authentic protected-reference route requires
a client binding; do not bypass that guard, relabel a legacy unprotected launch,
or reuse a consumed client/grant. Prepare a fresh bounded reference with the
necessary native client/fixture and zero model calls where feasible. No live
plan has been dispatched or declared qualified in this increment.

Then qualify actual resource effects/refusals, registration-to-fixture binding,
setup/team history, full continuous machine/RF/fluid operation, negative and
alternative-strategy controls, overhead/parity and isolation. The normalized
M1.5b resource verifier is unchanged and is not fed invented events. All other
G1 contracts, native root/helper, T05 and probe requirements remain open.

Final audit:483 source pins,439 preserved unique milestone IDs,1,765 local links,
113 Python passes/14 Java passes and1 native opt-in skip. All40 real authority
tables unchanged at$4.887796; no owned runtime or game/model dispatch. Source/
evidence archive66files/2,481,012bytes, seal
312be18a0b9df81015e578e48d8bd29728971bd4439c396d6ce6c18bce7d6012.
Module0.3.15 SHA256c462f6dfbbe675236c19b6d0d91b5f301053d1e15eef46ede712311972e72571.
This pointer follows the archived documentation snapshot; authentic transformed
capture, protected qualification and full G1 remain unverified.
