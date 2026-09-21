# M0 authentic resource observation and native file-resource discrimination

September 21, 2026. Operator-only. M0.2c.3b.3b.2a and
M0.3b.2c.3c.2b.2b.2.2a.4/.5; F09/F16, N01/N03/N04/N05/N06/N08,
C14/C15/C18/C24, partial T01/T07/T12/T13/G0. M0 is incomplete,
G0 fails and G1–G5 are not run.

## Authentic prepared reference

Fresh private `2026-09-21-protected-craft-live-06` ran from source
`3dab9df100ce176e4207d347cecea31fb9d57f9f`, with 463 input pins and 119
archived source files. The original unplayed 8,609-file source remained unchanged;
neither the progressed case04 world nor failed case05 scope/grant was reused.
Private preparation and audit scripts are in
`2026-09-21-resource-reference-preparation-02`. These are actual game evidence,
separate from the native synthetic fixtures below.

The [prepared-client implementation](2026-09-21-client-preparation-admission.md)
now has narrow authentic evidence. A deliberately missing proof on the production
candidate plan rejects with `REFERENCE_CLIENT_PREPARATION_MISSING`, with zero
pair intents and zero server/client dispatches. The fresh case then prepares the
cached session before registration and pins its receipt, argument bytes and driver
in pair-v3. The original v2 plan and explicit pre-intent amendment remain private.
The 13-check admission audit passes: the same proof is verified before the server
with 915,000 ms of required remaining exposure and before the client with 425,000
ms. The proof asserts prepared bytes and expiry, **not authenticated-session or
isolation qualification**. The body subsequently joins the actual server.

Expert furnace crafting, all seven declared public operations, native
actor/team/mode/resource points and independent saved-state checks pass. All
**79 primitive charges** reconcile, with no unknown game request. The complete
authenticated stream contains **284 records / 5,641 sampled server ticks**.
Client startup takes 188.328 s; client total is 281.219 s. Pair total is 647.25 s.

The pair is nevertheless **UNCERTAIN**. The unchanged guardian's root wait times
out at **513.433/500 ms**; the independent observer sees exit at **630.8377 ms**
from wait start. Tree proof was not started and cannot be inferred afterward.
The complete trajectory audit passes only 28/32: paired lifecycle, guardian,
protected custody closure and candidate admission fail. Import rejects
`CRAFT_PROTECTED_REFERENCE_UNQUALIFIED`. The server stops normally; inner server
14/14, outer server 29/29 and outer client 118/118 histories are terminal, with
no inventory-list anomaly/reconciliation. Credentials retire, input desktop is
unchanged and no Java remains. This is neither a scored result nor a complete
game/agent checkpoint.

The failure-preservation audit passes 21/21 after a **separate retained
correction**: its first version compared the order of failure names after canonical
key sorting and passed 20/21. The corrected audit compares the exact set. Original
script, failed audit and authentic failed result remain; no run was repeated.

## What the authentic resource observer established

The independent journal contains 94 records / 118,975 bytes, SHA-256
`c64074099c5b57dd60cdc52cd98ea096f8b3984440711e2c3299995ea2e62f19`.
Identity, sequence, schema, counters and lifecycle checks pass. There are 93
complete live counter samples, including 92 before stop, plus a terminal sample.
There are **zero complete region censuses**: 21 hit the original 8,192-region
quota; other records retain segment-budget, teardown or not-run results. The
resource-phase audit remains **11/12, fail**, because complete pre-stop census
evidence is missing. Quotas were not raised to turn this into a pass.

The last pre-stop counters show 2,588 handles, 5,831,811,072 private bytes and
4,797,222,912 working-set bytes. That counter starts 394.5473 ms before stop;
its whole query finishes 353.7258 ms before stop. **No resource query overlaps
the first 500 ms after stop.** The next starts at +610.6544 ms during teardown;
its zero handles and reduced memory are not pre-stop state. This does not exclude
earlier sampler effects or prove a cause. Maximum counter query is 1.0714 ms;
maximum whole sample is 209.3976 ms, well before stop. The 25-ms budget is checked
between native calls; nonpreemptible-call overruns remain explicit.

The final quota-limited prefix covers 8,192 regions / 3,183 allocation bases,
not the whole address space. Its zero image bytes cannot describe the complete
process. By comparison, the retained passing native comparator had roughly
1,588 regions / 483 allocation bases and 593 handles at similar private bytes.
That measured difference motivated the following finite implementation.

## Implemented file-resource fixture and verification

[GuardianRenderFixture](../../tests/fixtures/GuardianRenderFixture.java) version 3
and [the operator probe](../../tools/probe_guard_graphics.py), policy
`held-native-file-resources/6`, add two explicit profiles to the existing hidden
graphics, 3,072-MiB heap, 1,024-MiB textures and silent OpenAL workload:

- `combined-file-handles`: retain 2,048 read-only channels to one new 65,536-byte
  patterned private fixture file, verifying size and readback.
- `combined-file-mappings`: retain 2,048 read-only mapped views of that same-size
  private file, checking each view and touched page; close each original channel.
  The pinned Windows JDK duplicates one handle for each retained mapping.

Strong references keep resources live through forced termination. Mappings have
no supported explicit close in this JDK; a normal terminal fixture report says
their release still requires process exit. Neither fixture reads game/world files,
credentials or other processes' contents. Scope/process/mode/count/byte/access
binding rejects incomplete, mismatched or old-schema readiness. Profiles are
fixed and distinct; existing desktop/GPU headroom, 45-second outer bound,
20-second ready expiry, five-second observation hold and 500-ms guardian remain.
No gameplay capability or game resource setting changes.

`pytest -q tests/test_guard_graphics_probe.py`: **46 pass / 0.23 s** (the previous
27 plus 19 new cases); focused Ruff and pinned JDK compilation pass. Three actual
JVM argument negatives reject before boot/resource creation: missing mode,
unbounded mapping count and incompatible load combination. Only the two new
profiles run; no old graphics/game sample is repeated.

Private `2026-09-21-guardian-files-native-01` retains exact compiled/source/runtime
pins, plans, readback evidence, resource streams, terminal proof and a **22/22
passing independent audit**. Windows x64, Python 3.12.14, Temurin 17.0.20.1+1,
existing nine pinned LWJGL 3.3.1/Gson artifacts, NVIDIA RTX 3090/591.86 and silent
OpenAL Soft 1.21.1/WASAPI. No download, Minecraft, inference or physical input.

| Profile | Pre-stop handles | Private bytes | Last complete pre-stop regions / allocation bases | Root wait ms | Complete tree ms from wait start |
|---|---:|---:|---:|---:|---:|
| File handles | 2,646 | 5,842,522,112 | 1,593 / 478 | 357.2092 | 357.3220 |
| File mappings | 2,643 | 5,889,466,368 | 3,599 / 2,536 | 365.3951 | 365.6211 |

Both have two complete pre-stop interval censuses and five wholly pre-stop counter
samples. The mapping census contains 2,091 mapped regions / 228,319,232 mapped
bytes. Each case has one resource-query interval overlapping stop; it is not a
pre-stop census. Both outer histories terminate 2/2, with no watchdog/cleanup
fault, unchanged input desktop and matching source pins. No Java remains.

The finite handle/mapping loads **did not reproduce or resolve game shutdown**.
Similar handle/private-byte totals do not make these workloads equivalent: the
game's partial region count still exceeds both fixtures. No resource reduction,
threshold change or unchanged game rerun is justified. Next advance the independent M0 native read/tool/broker boundary against the
retained sibling-read failure while preserving native Dovetail. The remaining
private-allocation fragmentation is an explicit shutdown evidence gap; another
game trial still requires a relevant implementation change or named question.

Original $10 authority and the $0.7554 unresolved model hold remain, counted once;
no model request, reset, replay, settlement or refund occurred. All prior 500-ms
failures, five effective-file failures, Mineflayer/E9E incompatibility, sibling-read
and loopback failures, scorer/provenance/recovery requirements, required M0–M6
and conditional M7/extensions remain represented.

The combined private manifest verifies **675 files / 118,615,180 bytes**, SHA-256
`86fd47535d180d0057c5933610d6e8d456cabeee12c6bd10660792069acc4969`.
Read-only accounting at Unix ms `1789997651047` confirms the original authority
digest, schema 2, one migration, 10,000,000-microUSD cap and 755,400-microUSD unknown
exposure. Source validation preserves the complete prior append-only log,
all 294 previous milestone IDs plus the new diagnostic child, and 1,101 checked
local links. Raw evidence, installations, credentials and private instances remain
outside public source and gameplay access.
