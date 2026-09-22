# Installed Mineflayer dependency provenance

September 22, 2026. Operator-only. M0.3a.2 remains in_progress. This advances
actual worker runtime evidence for the vanilla PackLock; it does not qualify
authenticated gameplay, isolation, licensing or G0.

## Implemented behavior

[Offline verification](../../src/mcbench/npm_runtime.py), exposed through
`mcbench pack inspect-npm-runtime`, joins the manifest, version-3 lock and
installed hidden lock. It verifies retained registry tarball SHA-512 values and
every installed member. Missing/changed/extra files or directories, unsafe paths,
links/hardlinks, collisions, unsupported origins/integrity and quotas reject.
The command downloads, installs and executes nothing.

The lock describes package locations and artifact integrity; the hidden lock
does not independently prove contents. These distinctions follow [npm's lockfile
documentation](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/).
The inspected installed npm/pacote source removes one archive path component
and renames `.gitignore` to `.npmignore`. The verifier applies those exact
transformations, retains member/target hashes and rejects ambiguous collisions.

Windows wrappers must match separate reviewed generator output. Names/targets
derive from locked bin declarations; the verifier does not independently
authenticate the supplied generator material. The actual procedure copied
installed cmd-shim 8.0.0 with its license/source and the 13 declared bin targets
into private evidence. Its 39 generated wrappers match the installation exactly.
No package lifecycle script or generated wrapper executed.

Private `NpmInstalledRuntime/1` retains file hashes, archive/member joins,
versions, origins and license declarations with qualification fields false.
Retaining a declaration is not a legal or package-safety judgment.

## Verification

Twenty-three focused verifier tests and two command cases plus the gameplay
package check pass: **26 distinct source cases**. Full Ruff and whitespace pass.
The CLI/package selection has only two existing Typer/Click warnings.

```powershell
python -m pytest -q tests/test_npm_runtime.py
python -m pytest -q tests/test_npm_runtime.py::test_operator_command_retains_report_or_typed_refusal tests/test_gameplay_package.py
```

Actual installed evidence verifies **111 packages**, **9,336 package members**,
39 wrappers and the hidden lock: **9,376 files / 509,795,129 bytes**.
All tarballs were already cached; no registry download or signature-verification
claim. **9,599 inputs / 642,390,618 bytes** were held against Windows
writes/replacement, including Node, worker, schemas, source pins, retained
archives and generator material. The held verification lasts **51.329 s**.
The real worker's import-only `--check-vanilla-runtime` passes and the complete
source inventory still matches after closure. Capability digest:
`d5efbb355d4f4215006a7032504e1bfb709d53336207b92aa58066472e56057f`.
No avatar, authentication call, game connection, Java or model request occurs.

Independent audit: **10/10** checks joining reported files to held pins, every
retained SHA-512 archive, wrapper counts, exact ignore rename and scope limits.
The first exploratory script incorrectly assumed every archive used `package/`
and failed on five `@types` prefixes; that failure and the preliminary ignore
filename mismatch remain retained. The implementation verifies actual safe
single-prefix layouts and exact byte-preserving normalization.

Read-only verification preserves all 34 authority tables. Explicit publication
then adds **one operator CAS object and one artifact event**, preserving every
previous object/event and all 32 other tables: **39/39** conservation checks.
Report in the original vanilla namespace:

`cas:sha256:e39bf00590824c07e75a6f8daf1818f785273077df0b8f68d4f781ebfc78787c`

Vanilla remains VERIFIED/unsealed. Original accounting stays **$0.7554 held +
$0.001458 settled = $0.756858**, allowance $10, uncertainty present and D12
consumed. Shared-desktop input remains paused. Private evidence:
`C:/Users/Darian/.strata/evidence/2026-09-22-mineflayer-runtime-01`.
The complete sealed set contains **250 files / 139,760,040 bytes**, manifest
SHA-256 `bce2cf7e377afe0e2adbb079416b8efa2385114272c212a3870eacdaed166f39`.
All entries reverify, including retained tarballs, compiled worker inputs,
Node bytes, generator source and initial failures. The documentation audit
preserves all 407 ledger IDs, append-only history, M1–M7 rows and SPEC sections
3/15–19; all 1,238 local links checked resolve.

## Remaining integration

This import-only test does not fully pin or exercise the Python ACL helper.
Bind the complete authenticated worker launch, its helper, server commands,
selected configuration and update policy to the actual pack before sealing.
Complete remaining source/component-declaration review without inferring a
license certificate. D05 account sign-in and explicit EULA acceptance already
have evidence in SPEC §15 and the September 18 record; do not ask again or
label them newly completed here.

The held lease covers this bounded check, not every future worker launch.
Ongoing runtime/custody enforcement, canonical joint recovery, scorer/setup,
clocks and isolation remain required. Preserve five effective-file failures,
Mineflayer/E9E incompatibility, D13 and every legacy 500-ms outcome. No unchanged
game rerun follows from this evidence.

Coverage: F01/F05/F16, N01/N04/N06/N08, C03/C04/C24, partial T01/T02/T06/T13,
G0 item 2. M0 incomplete; G0 fails.
