# Private saved-block reference — September 19, 2026

Operator-only. Never expose this reader, report, world copies or private evidence
to gameplay agents. M0.3b.2c.3c.2b.2c.1 and M0.3b.1b.4 remain **in_progress**.
Scope: F01/F06/F10/F13/F16, N01/N04/N06/N08, C09/C19 and private evaluation;
partial T01/T03/T06/T10/T13 support, with no aggregate test or gate pass.
SPEC v0.2.31 acceptance contracts are unchanged. This is an internal evaluator
utility, not another public record or gameplay affordance.

## Implemented scope

[saved_blocks.py](../../evaluator/src/strata_evaluator/saved_blocks.py) reads
selected persisted block IDs and properties from Minecraft 1.19.2 Anvil files.
It uses only the standard library and lives in the separate private evaluator
package. It has no gameplay CLI, service route, server mutation or model call.

- Exact DataVersion 3120, chunk coordinates and full-generation status required.
  Missing chunks/sections are errors, never inferred air. Standard overworld,
  nether/end and namespaced custom-dimension paths are supported.
- Region locations, bounds, sector overlaps, length/compression framing and
  external `.mcc` streams are checked. Gzip, zlib and uncompressed data supported;
  unknown compression, conflicting streams and detected file changes reject.
- Bounded NBT parsing handles Java modified UTF-8, all standard tag kinds,
  duplicate names, depth/node limits and truncation. Selected palettes enforce
  names, properties, data lengths and every stored index, including positions
  that were not requested. Singleton and 4–12-bit local palettes are supported.
- Limits: 256 unique positions; 8 MiB compressed/16 MiB expanded per chunk;
  32 MiB compressed/64 MiB expanded cumulative accepted input, with the final
  bounded chunk read before the cumulative check; 200,000 tags, depth 64.
  Reads are sequential and unused chunk data is discarded.
- Private output includes source/chunk digests and explicitly false flags for
  proven snapshot consistency, action causality, registry membership and scoring
  provenance. Hashes and stat checks do not authenticate a same-user file.

The exact installed mapped Forge 43.4.23 / official Minecraft 1.19.2 bytecode
was inspected using JDK 17.0.20.1 `javap`: RegionFile, ChunkSerializer,
PalettedContainer/Strategy, SimpleBitStorage and NBT classes. This caught an
initial incorrect assumption: this serializer writes `Status="full"` using
`getName()`, not `minecraft:full`. The reader and regression test use the actual
writer format. Storage indexes are Y/Z/X with non-crossing long entries.
Mapped JAR SHA-256:
`7498eb8ce73745150b3e3eed8aba0911a16466498cde970995d0036abf2b4dec`.
Full audit/tool/source hashes remain private.

## Executed checks

Windows, project Python 3.12.14, existing compiled gameplay CLI. No game launch,
desktop input, inference or broad-suite rerun.

```text
python -m pytest tests/test_saved_blocks.py tests/test_gameplay_package.py -q
ruff check evaluator/src/strata_evaluator/saved_blocks.py tests/test_saved_blocks.py tests/test_gameplay_package.py
git diff --check
```

**80 tests pass in 1.21 s**, no skips/failures: 79 synthetic save-format cases
and the existing actual compiled gameplay-package exclusion/CLI-denial check.
[Tests](../../tests/test_saved_blocks.py) cover compression/external streams,
negative coordinates/dimensions, known packed-word boundaries and unsigned bits,
every palette width, exact-version/status/coordinate errors, missing sections,
unrequested invalid indexes, malformed/truncated NBT, modified UTF-8, expansion
limits, region corruption, detected source changes and unsafe paths/point quotas.
Link rejection uses an injected filesystem observation; it is not a deployment
isolation test. Lint and diff whitespace checks pass (existing CRLF notices only).

## Actual stopped-server comparison

Private evidence:
`C:\Users\Darian\.strata\evidence\2026-09-19-saved-block-reference-01`.
The source is the [previous bounded E9E trial](2026-09-19-stop-boundaries.md):
official E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23, already stopped and saved.

The first comparison preflight rejected the selected post-cancel observation
because it was fenced/disconnected. No save copy or parsing happened in that
failed attempt. Its script/failure record remain retained. The corrected
procedure selects the last connected observation, `use_cancel.before`, sequence
5; the post-cancel record has the same sequence. Selection and timestamps are
recorded explicitly, with no synchronous-live-state claim.

Java-process absence checks pass before and after copying. One 4,980,736-byte
custom-dimension region is copied into the protected evidence directory, with
matching source/copy SHA-256 and unchanged source stat/hash checks. The copy is
marked read-only. It is a selected-region reference, not a complete checkpoint
or adversarially immutable seal.

**128/128 observed block IDs match** the persisted states, across two chunks.
The values include air, grass, grass blocks, cornflower and Twilight Forest
mayapple. Source chunks total 9,067 compressed / 62,271 NBT bytes. Properties
are decoded but this public observation contains no properties to compare.
The dig target is persisted as air. There is no independent pre-action save,
so neither causal dig credit nor resource/reach/mechanics qualification follows.

Private `comparison.json` SHA-256:
`ea9e9c16bc5b90f9b0ae8b061cbb59c44e210bf9c3157bdcb2dc935f1846873b`.
It retains comparison rows, precise source pins, copy metadata, observation
selection and limitations. Raw world data stays outside source/gameplay trees.

Next: capture independent pre-action and post-normal-save references in a fresh
authorized bounded action trial, then connect action identity/resource evidence.
Full snapshot inventory/sealing, visibility/reach negatives, menu/machine
semantics, scorer controls, isolation and reliable shutdown remain required.
All clients/servers remain stopped; Strata inference remains $0.
