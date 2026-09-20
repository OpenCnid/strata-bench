# Original-world restart with reusable journal staging

M0.2k.2 / M0.2k.2a / M0.2c.1a; partial T03/T07/T12/T13 and G0 items 4/6.

The new pair uses the original cancellation-reference server and its current
saved player, matching the end of the prior [failed-shutdown pair](2026-09-20-forge-reconnect.md).
No world reset or resources are supplied. The previously observed three-step
route remains clear in the stopped save; the public checker must independently
select a currently delivered route under its unchanged rules.

Resource profile `g1-heap-cap3072/1` changes the client maximum heap from 4096
to 3072 MiB, retaining the 512 MiB minimum, default G1 free-space ratios 40/70
and disabled periodic collection. Bounded private GC logs are retained. This
is distinct from the [failed aggressive-ratio candidate](2026-09-20-guardian-memory-profile.md).
Game options, mod artifacts, server telemetry 0.2.0 and public action policy
remain unchanged. Both phases use the same new resource profile. Client/worker/
action/guardian limits remain 480 s/90 s/5 s/500 ms.

The two phases share one immutable 1200-s native authority and 1000-primitive
cap. After a safe terminal cancellation source, phase 02 calls the reusable
`stage_journals` and `verify_staged` operations. It retains the complete native
and worker database bytes in a committed private staged set. Exact verified
copies feed the existing native/worker paths; previous public receipt evidence
is copied separately. No old descriptor, observation grant or credential is
transferred. Authority is unchanged and no uncertain request is replayed.

After the second server starts, its driver verifies the staged set again against
the original receipt, checks the actual launch-source copies and requires more
than 370 seconds of original authority remaining before client launch. The
terminal phase-02 audit additionally binds these staging/verification receipts
to the actual journal prefixes and cumulative costs. Failed guardian timing
remains failed even if eventual termination permits the continuation check.

All public checkers, audits, staging adapter, sequential controller and exact
operator/evaluator source pins were prepared before dispatch. Both preflights
and cached phase-01 session preparation pass. Phase 01 completed under
`C:\Users\Darian\.strata\evidence\2026-09-20-forge-reconnect-03`.
Phase 01 fails before movement because its reference selector assumes the player
is within 0.15 blocks of the starting cell center. The previous cancellation
left the player off-center. `SUPPORTED_START_FOOTPRINT_UNAVAILABLE` is retained;
no movement intent exists and phase 02 was correctly not dispatched. This is a
reference-procedure prerequisite failure, not evidence that native movement failed.

The 3 GiB client becomes ready in 251.672 s. Its complete guardian root/tree/held
handle proof passes in 490.7032/500 ms for this one sample. Final resident memory
is 4,772,691,968 bytes and private memory 5,616,644,096 bytes. This is not a broad
reliability or capacity qualification. Normal server stop, retired arguments,
terminal processes, saved position and full Inventory/EnderItems are confirmed.
Two global safety releases and 528.922 s remain charged. Completed linked
references now total 746 primitives/9408.894 s, plus the earlier setups/gap and
other separately retained scopes. No inference.

The original failed audit and unused phase-02 preparation are preserved. Its
authority must not be renewed. Subsequent work replaces the centered-fixture
assumption with explicit public-map support for the whole standing footprint;
the route length, displacement, cancellation and stop criteria remain unchanged.
