# 2026-09-18 Forge client gesture implementation

Operator-only. Scope: M0.3b.1b.2a, partial F01/F06/F09/F11/F16,
N02/N03/N04/N05/N06, C09/C15/C18, T01/T03/T06/T07/T12 under G0/G1/G2.
No authentic suite, milestone or release gate closes.

## Implemented behavior

The separately identified Forge development route now accepts eight ordinary
action kinds. Added `use_item`, `attack`, `interact_entity` and `chat` through
the existing scoped public worker, private native protocol and durable lane.
Production calls compile against the pinned Minecraft 1.19.2 / Forge 43.4.23
mapped artifact; these are ordinary game-mode/player APIs, not raw packets,
server administration or desktop automation.

`GameGestures` sequences one item-use start and bounded charged held ticks, and
requires delivered entity identity plus checks before/after aiming. The native
runtime uses Forge's reach checks, nearest native ray hit and conservative
observed-map visibility, then rechecks after the ordinary mod input hook. It
preserves hook cancellation/swing policy and reports input-only `emitted`, not
authoritative gameplay success. Main-hand entity interaction retains native
interaction-at/`PASS` fallback. Item use supports main/off hand and zero-hold tap.
Signed chat retains its native Forge hook while rejecting command input, controls,
format codes, malformed UTF-16 and the network's 256-unit length overflow.

The motor now runs at tick START before held-key polling. Owned use suppresses
additional native use-input events until release; a finished/rejected item never
causes the motor to start another use. Selected hotbar slot is bound privately
to every captured page and affects revisions. Entity IDs include a salted UUID
digest, reset with observation authority/body changes, so recycled numeric IDs
cannot address replacement entities and cross-probe raw UUID tracking is absent.
No hidden inventory, raw NBT, credentials or evaluator data is added to public
observations or gameplay packaging.

Capability minor 7 pins `durable-intent-client-thread-eight-actions/1` and
`opaque-voxel-fixed305-radius16/2` across Java, TypeScript and Python. Scope,
single-lane ownership, intent-before-emission, release reserve, unknown recovery
and no-replay behavior remain in the existing lane. Local primitive units and
their composite native gesture boundaries are declared in the
[operator contract](../operations/forge-game-api.md).

## Executed checks

Environment: Windows 11; Python 3.12.14; Node 24.19.0; pinned Temurin JDK
17.0.20.1+1 and Forge 43.4.23. No real Minecraft client/server was launched.

- `java/gradlew.bat :forge1192-client:test :forge1192-client:build
  :forge1192-client:writeTestClasspath --no-daemon --console plain`:
  **67 Java tests passed**, zero errors/failures. Production native calls compiled
  and the mod JAR was reobfuscated. New tests cover held-use completion/rejection,
  tap, lost context, exhausted primitive allowance, cancellation through the
  actual durable lane, no replay, target loss after aiming, missing/reused/occluded/
  unreachable targets, Unicode/command/length/surrogate cases, and private selection
  fences across pages/revisions/expiry. Runtime ports and geometry are synthetic;
  these checks do not prove actual Forge hook, ray-picking or item effects.
- `npm run build` and `node --test dist/tests/*.test.js`, with explicit pinned
  Java/classpath and guard Python environment: **96 passed**, zero skipped,
  49.775 s. Added gesture-envelope routing through the public broker and actual
  test JVM, exact Unicode journal bytes and one native intent per request.
  That fixture's generic synthetic effect proves routing/deduplication only;
  gesture mechanics are tested separately through the motor ports.
- Selected Python native client/JVM/guard/process/package run: initially
  **48 passed, one failed**, zero skipped, 44.20 s. The new Unicode assertion
  exposed a test reader using Windows' default code page for a UTF-8 journal.
  Corrected fixture/journal text encoding explicitly; no production transport
  relaxation or test expectation change. Reran all tests using that fixture:
  `pytest tests/test_native_game_jvm.py tests/test_forge_guard.py`:
  **17 passed**, zero skipped, 23.26 s. Existing xunit2 `record_property` warnings
  remain; they do not change test outcomes.
- Targeted Ruff check passed for the changed Python client and JVM tests.

Private logs, copied Java XML, Python XML, source/artifact hashes and command
metadata are retained in
`%USERPROFILE%/.strata/evidence/2026-09-18-forge-gestures-01/`.
No credentials, private grant bytes or live account identity are included in
this report. The rebuilt JAR was not installed into the live profile.

## Remaining requirements

M0.3b.1b.2a is **implemented but unverified in Minecraft**. The remaining
`move_to`, `place`, `equip` and `craft` actions are tracked explicitly under
M0.3b.1b.2b. Both groups still need authentic effects, resource/reach preservation,
failure/cancellation timing and custom mod interaction evidence. Expert-altered
recipes, modded metadata/collision/menus/machines and quest surfaces remain
M0.3b.3 and M0.3.4–10; native API compilation does not satisfy those cases.

Controller authority/repair/aggregate accounting, full timing, runtime isolation,
keybinding, native model/budget, soaks, simultaneous teams, scientific studies
and later packs retain their required gates. T03/G0 retain the actual failed
Mineflayer/E9E handshake; authentic Forge-candidate T03 is still `not_run`.
Desktop remains paused, with no live profile change or inference dispatch.
