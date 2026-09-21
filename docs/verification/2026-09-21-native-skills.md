# M0 pinned skill support and learned candidate capture

September 21, 2026. Operator-only. M0.1c.2b.2c.5 advances partial
F03/F04/F07/F09/F11/F16, N01/N02/N04/N06/N08,
C06/C07/C08/C12/C14/C16/C17/C19/C20/C23/C36,
T01/T04/T06/T07/T11/T12/T13 and G0 items 1/6.
M0 remains incomplete, G0 fails, G1–G5 remain not_run.

## Implemented

[native_skills.py](../../src/mcbench/native_skills.py) adds the private
NativeSkillCorpus/2 and `dovetail-eight-immutable-text-support/1` profile.
The original body-only profile remains supported. The new profile projects
reviewed supporting text, preserves the eight original skill bodies and
explicit invocation rules, and excludes nested test/fixture/VCS/credential
paths. The complete projected file set must agree with the private source
inventory and sealed bootstrap file hashes. Corpus/instruction changes affect
gateway/native profile identity. Script source remains text; it has no execution
authority and adds no native skills or tools.

[broker.py](../../src/mcbench/broker.py) records each artifact write's path,
content reference, expected reference, namespace and participant in the same
transaction as the file update. The existing call lifecycle determines whether
the result was actually returned. A repeated call label or identical content
still has its own broker event. Stopped exports bind these journals when present;
legacy exports without journals retain their prior identity but cannot invent
write provenance for publication.

[native_revisions.py](../../src/mcbench/native_revisions.py) consumes an explicit
root-written `skills/publish.json` request after a source-bound stopped export.
It checks the complete directory for each named candidate, SKILL.md, separate
inputs/development evidence, successful root write receipts, argument/result
digests, account classification, safe paths, immutable names and the aggregate
256-KiB limit per learned bundle. Helpers' private bytes and evaluation accounts
cannot supply campaign candidates. An explicit root copy of legitimately
supplied advice remains an ordinary root artifact; helper namespaces are never
automatically imported.

Publication copies private evidence first, revalidates it under a writer
transaction, then commits the entire candidate set once. A crash cannot leave
a partly published set. Later source mutation rejects; retry/restart returns
the same committed publication without cost changes. A checkpoint cannot gain
a publication after sealing. Candidate SkillRevision records retain null parent
and activation time; arbitrary parent claims reject. The generating IDs are
broker event IDs, tied to authenticated participant metadata and the complete
exported request/usage history. They are not a fabricated one-to-one attribution
to a particular provider model request.

[native_checkpoint.py](../../src/mcbench/native_checkpoint.py) retains private
candidate publication references through full/no-self-play boundaries and
mid-episode recovery. Frozen-persistence/frozen-skills episode boundaries discard
the learned set. [checkpoints.py](../../src/mcbench/checkpoints.py) materializes
candidate and bundle metadata in the private member directory, with supporting
text in the scoped workspace. Exact file/hash checks cover both. Windows extended
paths preserve deeply nested files without shortening or dropping them; existing
link/ownership checks remain required.

## Evidence

Windows, Python 3.12.14, existing dependencies. **161 affected tests pass in
50.58 seconds** before the final input/evidence distinction and materialization
review. After those changes and the Windows path fix, **69 revision/checkpoint
tests pass in 37.43 seconds**, and **20 storage/controller tests pass in 2.46
seconds**. Final corpus review adds **16 passing tests in 1.46 seconds**, including
typed rejection of an incomplete core source inventory. Focused Ruff and Git
whitespace checks pass. Final publication review preserves existing private CAS
metadata and protects the local initial keybinding skill name; **27 publication
tests pass in 23.24 seconds** after those changes.

```powershell
$env:PYTHONPATH='src;evaluator/src'
.venv/Scripts/python.exe -m pytest tests/test_native_revisions.py tests/test_native_skills.py tests/test_native_checkpoint.py tests/test_native_export.py tests/test_broker_lifecycle.py tests/test_native_broker.py tests/test_native_gateway.py tests/test_checkpoints_artifacts.py -q
.venv/Scripts/python.exe -m pytest tests/test_native_revisions.py tests/test_native_checkpoint.py tests/test_checkpoints_artifacts.py -q
.venv/Scripts/python.exe -m pytest tests/test_storage_controller.py -q
```

The actual installed-source probe uses
[native_skill_inventory_probe.py](../../tools/native_skill_inventory_probe.py).
Pinned Dovetail commit `15c306ccfef28eb5f616fadcd5fd8eac0663e361` has 478 source
files; the projection contains **90 files / 1,582,597 UTF-8 bytes**, with eight
top-level skills. Installed tree digest:
`a5a2155185fd2e5f06750f0821f89c57be9d9a26de47f3b057bfd2074ac5756e`.
Projected files digest:
`c34e8ff84c08c7d2c682e08ca5b6b87932e8217c0c307a4070fd2d258db8c91b`.
This is installed-source metadata verification, without a native process,
runtime file lease, model request or game launch.

A fresh Python process opens a copied synthetic controller/CAS and passes
**9/9 checks**: both candidate records, supporting text, private metadata,
helper exclusion, absent activation/dispatch authority, unchanged accounting
and publication idempotency survive reconstruction and complete materialization.
Audit digest:
`7630af868af8325718bdec5f0144a240a36a6b56efb65a9f189374ed948015a2`.

Retained intermediate failures: a synthetic broker-clock mismatch (14 pass/1
fail); a helper-copy negative that failed earlier at CAS permission enforcement
than the test expected (17 pass/1 fail); and an actual Windows long-path
materialization failure (68 pass/1 fail). The first two test expectations/setup
were corrected; the third required the implementation fix. Its failed JUnit
report and fixture remain separate from the passing long-path run.

Private evidence is `native-skills-01`: installed corpus/inventory, test fixtures
and JUnit reports, copied fresh-process audit, source snapshot and read-only
original-accounting check. The sealed inventory contains 8,845 files / 181,461,802
bytes; manifest SHA-256:
`5e7ce27cf95df1036d06b849235fb80a773c39043ee7454b4f018015b5cb1792`.
Do not mutate that bundle. No live provider or Minecraft trial occurred. Original
schema-2 authorization digest and $10 cap are unchanged; aggregate exposure is
755,400 microUSD once, uncertain, with zero valuations. No refund, replay or
additional allowance.

## Required continuation

M0.1c.2b.2c.6 must implement and qualify native learned-skill loading/atomic
activation, active parent lineage and supporting-file reads at the boundary,
then bind fresh scoped runtime restoration. Candidate publication alone does
not satisfy activation; existing active revisions still reject
NATIVE_REVISION_EXPORT_REQUIRED. Script execution/macros remain a separately
restricted required capability. Changed-profile actual-CLI/synthetic-provider
qualification is justified once the loader is implemented; unchanged accounting
matrix reruns are not needed.

Preserve all failed loopback/sibling-access evidence, 500-ms shutdown failures,
five effective-file failures, Mineflayer/E9E incompatibility and remaining
scorer/provenance/recovery requirements. This source checkpoint changes no gate
result or acceptance threshold.
