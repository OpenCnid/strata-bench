# Sealed Forge bootstrap and pinned skin cache

M0.3a.4j and its new child M0.3a.4j.1 are **verified for the named sealed
development bootstrap**. Both actual resolved commands execute against the
successor PackLock, the client returns its connected body state, and stopped
reconstruction passes 34/34. Together with the retained vanilla join, exact E9E
negotiation failure, expert assertions, cold restart and thirteen provisioning
checks, this closes **G0 item 2 for the named D14 development profiles**. M0 stays
in_progress and aggregate G0 stays fail.

Coverage: F01/F05/F06/F16, N01/N04/N06/N08, C03/C04/C24, partial T01/T02/T13.
Known startup-input work M0.3a.4k and installed-role preparation M0.3a.4 are now
verified in their declared scopes. Full helper accounting, private scorer joins,
applicable recovery and authoritative time/save/cost joins remain under G0
items 1/4/5/6. D14 defers full isolation to M1/G1; M1–M7 remain unchanged.

## Source and negative cases

[forge_assets.py](../../src/mcbench/forge_assets.py) implements the separate
operator policy `forge-pinned-skin-cache/1`. Original asset files retain strict
FileLease write/delete denial. At most sixteen explicitly declared new skin
paths may appear; each must match its predeclared SHA-256 and size, have one
hard link, and validate as a bounded 64×32 or 64×64 RGBA8 PNG. Chunk ordering,
CRCs, scanline filters, inflate bounds and trailing data are checked. Captured
entries acquire retained leases through client termination. Unlisted files,
changed originals and disappearing captured entries fail. This policy does not
change general FileLease tree checks or qualify rendering/network isolation.

[pack_forge.py](../../src/mcbench/pack_forge.py) validates optional skin pins in
ForgeClientInvocation and emits `ResolvedPackLaunch/4` with their exact policy.
The empty-list legacy path remains /3. `ForgeAssetLease/1` binds the original
inventory, declared cache digest and actually captured entries. Neither record
is one of the thirteen canonical public records; no gameplay action is added.

Focused verification executed:

```text
python -m pytest tests/test_forge_assets.py tests/test_pack_forge.py -q
56 passed in 65.86s
```

These tests include real Windows sharing denial, preserved strict FileLease
behavior, malformed/altered/unlisted cache files and a complete synthetic
seal/materialize/resolver path. PNG and provisioning fixtures are synthetic;
they do not replace the authentic case below. Two existing Typer/Click
deprecation warnings remain.

Final `ruff check .` and `git diff --check` pass. Read-only final verification
rehashes all 238 sealed files and compares all 39 live authority tables with
the sealed stopped snapshot. All 1,491 checked local links resolve; the 359
existing milestone IDs, all 51 M1–M7 rows and append-only history are preserved,
with only the new .4j.1 child added.

## Authentic changed case

The already prepared `e9e-sealed-snapshot3-01` instance was reverified while
pristine. Both server and client resolved before either process launched. The
runner then used those exact executable paths, arguments, working directories
and environments. It retained original software/config/asset leases, a fresh
protected session, Snapshot/3 inputs and bounded owned-process watchdogs. The
instance is now used and must not be replayed as a fresh materialization.

The run passes in **386.000 seconds**, including a **182.375-second client**.
Three public bootstrap reads—identity, lane status and bound observation—take
**0.297 seconds**. The authentic body is connected; its lane remains NOT_ARMED
with zero input events. There are no model/helper calls or gameplay actions.
The prior recipe/quest reference and craft are not repeated.

The server emits **194 authenticated records / 3,712 ticks**, preserves expert
mode and the exact altered furnace recipe, then stops normally. All **three
server and eight client owned processes** are terminal. Client shutdown uses
owned-Job termination; this is not D13 or client clean-save qualification.
Signed telemetry authentication does not promote its separate private scorer
transport/custody flags, which remain unqualified.

Exactly one predeclared **979-byte skin PNG** appears. Its bytes match the
retained prior observation. All **3,366 original asset files** remain held and
unchanged; cache receipts before and after server stop agree. The filename is
not asserted to be a SHA-1 of the PNG. Renderer and isolation flags remain false.
All 39 authority tables remain unchanged; exposure is **$2.831942/$10**, with
every old unresolved reservation retained.

Stopped capture retains 163 changed/new files totaling 34,690,674 bytes. The
independent audit passes **34/34**; the complete private archive contains
**238 files / 63,172,789 bytes** and passes EvidenceBundle readback. Preparation
takes 80.954 seconds and capture/audit 38.281 seconds. A runner-generation
syntax failure is retained separately; it happened before Java/native startup
and caused no game or model execution.

## Retained boundaries and evidence

The [previous reference run](2026-09-24-e9e-sealed-reference.md) remains failed
because its strict tree policy rejected the new PNG. Its narrow public-reference
assertions still pass. The new source policy and changed authentic case resolve
that launch issue without relabeling the old run. Historical config findings,
class refusals, ZIP metadata drift and renderer/optional-network dispositions
remain in their original evidence.

The vanilla backend remains Mineflayer. Its [actual GPT-6 Luna pilot](2026-09-23-support-coordinate-pilot.md)
already verifies model-selected turning and walking. E9E uses the separately
identified Forge structured backend. The retained Mineflayer 4.39.0 / MC 1.19.2 /
Forge 43.4.23 attempt did not spawn: `FORGE_HANDSHAKE_UNSUPPORTED`; the bounded
FML3 offer diagnostic reported `FORGE_CHANNEL_IMPLEMENTATIONS_REQUIRED` with
233 mods, 111 channels, 39 registries and two datapack registries. No false
acknowledgement or Mineflayer E9E pass is claimed. These historical raw diagnostic
files were read and hashed again, not replayed or retroactively sealed.

| Artifact | SHA-256 |
|---|---|
| New archive seal | `e11fa80d6ab939f785a9c663d07305f2d33e39650eb9f0b5a8e97cf473b61762` |
| Independent audit | `c68893b705ceb64158448c2f6232e4e30a6adc19b04ebe2aea3a7fb2a3079e14` |
| Passing execution | `7d56663800538fa6ea6a2efd50394622967614d6a3033f1a545df8a31b348539` |
| Successor PackLock | `660dceda185db8f11b0ff5d9bb99b6f4c192f7295ddd5dded9d5d6331b75570a` |
| LaunchProfile/4 | `023fc52227314bb1cf73b1de354c99816e16c66f7808e888b684eec3bf50d172` |
| Retained failed strict-tree execution | `e972662340f456c20d55a349cef9a34f16586cf210a6bacccb7f6b45bc7cb047` |
| Historical Mineflayer handshake diagnostic | `2d6a49f41ad618301626f43cda8224ac228ded964ca3edd419c66c28539a2e5d` |
| Historical FML3 offer diagnostic | `6eb63d5f7ffceff360fbfcbe1802b053e117164b755c2754d48c3228c3266112` |

Private archive: `C:/Users/Darian/.strata/evidence/2026-09-24-e9e-sealed-launch-01`.
No private account data, credentials, game assets or live fixtures are published.
Do not repeat this successful bootstrap, public reference, craft or zero-helper
pilot unchanged. Next close the remaining bounded root/helper model accounting
case and private scorer/recovery/time joins rather than expanding installation
qualification.
