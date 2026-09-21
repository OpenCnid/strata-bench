# Sealed native broker bootstrap

September 20, 2026. Operator-only. M0.1c.2b.2d; F03/F04/F07/F11/F16,
N01/N03/N04/N06, C06/C20/C36, partial T01/T04/T06/T07/T12 and G0 items 1/6.
Implementation and synthetic integration evidence, not a RuntimeQualification.

## Delivered behavior

[Bundle preparation](../../src/mcbench/native_bootstrap.py) copies the existing
Python runtime, broker source and six required dependency packages into a
dedicated private software directory. It imports no credentials or mutable
controller/world state. The manifest pins that entire directory, the selected
native executable, installed Dovetail tree, static native/marketplace settings,
broker configuration and worker descriptor. No Python installation or package
download was required. Absolute paths and links/reparse points are checked;
Windows extended paths preserve the plugin's long-path fixtures.

[FileLease](../../src/mcbench/launch_integrity.py) opens and hashes the same held
Windows handles before dispatch. Sharing denies writes/deletion/replacement;
ancestor directory handles prevent renames. Exact tree inventories detect added
files. Native supervision holds the lease until process cleanup; failures in
cleanup retain an integrity hold. Source checks precede model admission and
broker operations. Bootstrap rejection before launch posts no budget operation.
Lease ownership and stopped state remain distinct from billing settlement.

[The isolated broker loader](../../src/mcbench/sealed_broker.py) uses a copied
interpreter with `-I -S -B`, an explicit import path and a module-origin allowlist.
It compiles pinned Python source directly: `-B` alone would still read a matching
unlisted bytecode cache. Unknown/sourceless bytecode and module origins are
rejected. The managed process bootstrap also uses isolated startup and, for a
sealed launch, the copied interpreter/source. Native CLI sandbox mode is
explicitly read-only for this sealed profile; agent drafts remain broker objects.

Native launch identity includes the seal digest; legacy identities omit absent
optional fields. Exact broker command, arguments and empty environment must
match the seal. Required executable/configuration files must be inventoried;
private files/import roots must be outside the gameplay workspace. Sealed broker
configuration binds the native job and derives its profile from durable state,
avoiding a circular manifest/profile hash. Live broker profiles require a seal.
This requirement does not supply the other live qualification evidence.

These are integrity and capability controls. File locks do not deny reads by an
arbitrary same-user process and do not themselves authenticate an HTTP caller,
protect OAuth tokens, qualify all OS dependencies or establish a full sandbox.
The native tool restrictions and denied access evidence remain necessary.

## Source verification

Executed with repository `src` on PYTHONPATH and the existing Python runtime:

```text
python -m pytest -q tests/test_launch_integrity.py tests/test_processes.py tests/test_native.py tests/test_native_admission.py tests/test_native_broker.py --tb=short
104 passed in 20.35s

python -m pytest -q tests/test_launch_integrity.py tests/test_native.py::test_changed_bootstrap_rejects_before_budget_or_process --tb=short
14 passed in 0.88s
```

The latter is the focused final check after added source-loader, scope and
pre-reservation rejection guards; it is not a claim that the entire suite was
rerun. Targeted Ruff and whitespace checks pass. Owned-file tests exercise
write/delete/replace/parent-rename denial, long paths, changed bytes, partial
acquisition cleanup, additions before/during a lease, manifest mismatch,
missing pins, altered commands/environment, wrong job/workspace scope, disabled
site/environment initialization, and unlisted source/bytecode rejection.

A separate real-process load of the copied broker/native/admission dependencies
through the final source loader passes in 8.125 s. Its guard source SHA-256 is
`2f7d4cf98d7311e3e158404913530608334f100d509103633917be456d05e8c0`;
private `native-bootstrap-04/final-loader-dependencies.json` records the result.
The final scope/membership guards also pass an offline reacquisition of the
retained canary manifest (3,460 pinned files including its manifest). Neither
check invokes a model or rewrites prior native evidence.

## Native CLI and synthetic-service evidence

Same pinned CLI `0.154.0-alpha.6.2`, binary SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`,
Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361`. The existing fixture gained
`--bootstrap`; it reuses the established dispatch parser/accounting and native
root/helper workflow. All model responses and worker observations are local
deterministic fixtures. Raw evidence remains under private `.strata/evidence/`.

```text
python tools/native_mcp_identity_probe.py --codex '<pinned codex.exe>' --output '<fresh private directory>' --broker --admission --bootstrap
python tools/native_mcp_identity_probe.py --codex '<pinned codex.exe>' --output '<fresh private directory>' --broker --admission --bootstrap --canaries
```

| Directory suffix | Actual result |
|---|---|
| `2026-09-20-native-bootstrap-01` | Failed before native job/provider dispatch: long plugin path reported as a missing/non-file object. Fixed extended-path I/O and added a long-path test. |
| `2026-09-20-native-bootstrap-02` | Failed: one ingress request arrived before independently journaled `thread.started`; zero forwarded requests. Added a bounded two-second identity wait, with timeout/no-reservation and independent-writer tests. |
| `2026-09-20-native-bootstrap-03` | Failed fixture: parent finished after one ten-second helper poll timed out, interrupting pending helper tools. Five calls settled to 70 fixture units. Corrected the driver to keep polling for completion within its existing hard job bound. |
| `2026-09-20-native-bootstrap-04` | Pass: seven admitted/settled calls, 98 fixture units, 35.850 s native job, scoped root/helper artifacts and executor worker call, all envelopes closed. Independent operator write-open challenge against its copied dependency was denied while the durable job was RUNNING; bytes unchanged. |
| `2026-09-20-native-bootstrap-canaries-01` | Pass: nine admitted/settled calls, 126 fixture units, 45.431 s native job, all 14 canary checks plus broker/admission checks pass, finalized budgets. |

The sealed fixture's 90-second hard job bound, 30-second MCP startup and
10-second server-tool timeout were declared before its first run. The polling
repair did not extend those bounds or any action/shutdown acceptance threshold.
The helper startup/lease overhead is observed behavior; full resource/latency
qualification remains open. All failed samples remain evidence.

Passing ordinary fixture: profile
`3652f96ec6ad25026ae17394c9afff01eaaba6602fb75c40559dec49bcf86220`,
result SHA-256
`9beb7622a774c6d8e0089e740a63bb9e1a38be36ceaad38b3d5243f1f2ae0c1d`,
seal `fe9b5ba277f6e63b4da43b0136b6f56b68536249e02ea62adec2bc7eba409456`.
It inventories 3,459 files / 364,301,734 bytes before the manifest itself.

Passing canary fixture: profile
`90729b0311d5895fc71149e8f1e7a1b85650dbd9a5a6abc9f36c15f23258b343`,
result SHA-256
`d584c26bc3444fd509f7561d0e2b9b7ab6aa41c913619e6f86b082a48a713a8a`.
Root/helper catalogs match the permitted set. Both direct shell dispatches
return unsupported; shell/image functions and file/network resource requests
are denied. Outside patching fails, protected bytes remain unchanged, ancestor
and private-file markers never enter provider requests, and an owned loopback
positive control succeeds with zero unauthorized visits. These results apply
to the recorded profile, not the earlier failed unrestricted-loopback profiles.

The final source-loader cache defense and scope tightening were added after
the native snapshots; their additional evidence is the focused tests and actual
copied-dependency/offline seal checks above. No unchanged native trial was rerun
solely to obtain another success count.

## State and next dependency

Across these samples: 21 forwarded requests, 294 synthetic fixture units,
zero OAuth inference or actual model charges. Fresh read-only inspection of
the original project store still shows schema-2 authorization and zero
experimental operations. The original $10 allowance is unchanged. No Minecraft,
evaluator launch or shared-desktop input occurred; owned Python services are
terminal.

Next implement authenticated, job-bound native inference ingress and upstream
credential separation using supported native transport capabilities, then
actual Dovetail skill-body projection/learned-artifact activation/export and
full helper lifecycle. Qualify OAuth usage/exposure before the staged trial of
at most $1 within the original $10. Preserve the selected native runtime and
all required helpers/skills; the sealed broker is not a waiver of executable
artifact requirements. M0 remains in progress, G0 fails and G1–G5 are not run.
Earlier loopback, 500-ms shutdown, effective-file and Mineflayer/E9E failures,
plus scorer/provenance/recovery gaps, remain unresolved.
