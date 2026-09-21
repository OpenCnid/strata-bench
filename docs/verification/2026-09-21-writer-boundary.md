# M0 protected mutable writer candidate

September 21, 2026. Operator-only. M0.2c.3b.2b/.1; F04/F09/F10/F13,
N01/N04/N06/N08, C12/C24, partial T01/T06/T10/T13 and G0.

## Delivered implementation

`evaluator/src/strata_evaluator/windows_writer.py` creates a fresh Windows
directory with its final protected DACL in the atomic `NtCreateFile` operation.
It never adopts an existing directory. The operator has read access; an explicit
OWNER RIGHTS entry removes implicit owner permission-changing authority. SYSTEM
retains recovery access. File and directory inheritance preserve the policy.

The final candidate grants modification to the existing native sandbox group
and the specific enrolled workspace's restricting SID. It does **not** grant
modification directly to the shared sandbox user. The pinned native process
must satisfy both the normal and restricting checks for writes. The operator
must not be a member of that group. Exact root/child descriptors, identity types,
scope syntax and native fixture token observations are checked. This is the
`windows-scoped-mutable-writer/1` candidate, not a new gameplay capability or a
replacement for the selected native Dovetail runtime.

Retained directory handles request list access and deny deletion sharing. A
metadata-only handle was insufficient: the first negative replacement control
renamed the root successfully. The corrected implementation protects the root
and ancestors while held. Closing does not reset the DACL. After handles are
lost, a writable parent can rename/remove a directory; durable instance identity,
fresh grant admission and recovery checks must therefore precede any future
adoption. No crash recovery or protected setup certificate is issued here.

The primitive is **not yet connected to ReferenceLauncher**. It does not bind a
Java process/token to an instance, create a sealed game copy through that writer,
own the server's complete lifetime, verify setup mutation history or make a score
eligible. Unrestricted processes in the writer group are not covered by the
restricted-token argument. Protecting the controller and admission to the
native launcher remains necessary.

## Actual OS evidence and retained failures

Private evidence is under `C:/Users/Darian/.strata/evidence/`:

- `2026-09-21-writer-boundary-01`: exploratory root creation succeeded; attempted
  controller population failed, correctly, under the final DACL. The first
  native command had incorrect relative paths/PATH assumptions; the corrected
  absolute-path command identified `CodexSandboxOffline` and created a canary.
- `-02` through `-05`: PowerShell `Rename-Item` failed. Adding a workspace SID
  beside the account grant and reducing retained access did not fix it. These
  are failures, not successful PowerShell rename evidence.
- `-06`: a direct Win32 fixture under the intended account successfully opened
  read/write/delete handles and renamed the file while the guard was held;
  WRITE_DAC was denied. This narrows the PowerShell failure without claiming
  its cause was repaired.
- `-07`: intended native operations and ordinary-user file denials passed, but
  the metadata-only root handle permitted root replacement. Retain the moved
  synthetic directory and failing report. List-access handles corrected this.
- `-08` and `-09`: the account-only candidate passed nine narrow controls.
  The initial regression run retained 21 passes, three failures and four
  teardown errors: test cleanup incorrectly assumed retained WRITE_DAC could
  reset the ACL, and root deletion expected ACCESS_DENIED instead of the actual
  sharing violation. Final tests use empty-directory cleanup after close and
  preserve the correct OS failure codes; production does not reset permissions.
- `-10`: the account-only policy failed the separately scoped sibling control:
  the same sandbox user could read, write and delete the fixture. This motivated
  the group-plus-workspace policy rather than a broad account allowance.
- `-11`: changed policy denied sibling write/delete, but sibling read succeeded.
  The fixture then raised an unhandled denied-write exception. That result is
  retained; the final fixture returns a bounded negative result instead.
- **`-12`: final overall isolation result is FAIL.** Twelve of thirteen checks
  pass: intended native read/update/rename, observed token scope, exact inherited
  ACLs, ordinary-user overwrite/create/delete/rename denials, held-root replacement
  denial, unchanged bytes, sibling write/delete denial and persistent write denial
  after close. **Sibling read denial fails.** The sibling fixture exits 4 with
  explicit Win32 read success and write/delete/WRITE_DAC error 5. Its restricting
  SID differs from the writer's. This remains a real read-isolation gap; do not
  infer full protection from the write boundary.

These are actual Windows/pinned-Codex-CLI **synthetic file fixtures**, not model,
Minecraft or authentic evaluator-instance trials. The CLI SHA-256 remains
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`.
The helper uses existing enrollment, named workspace permissions, network
disabled and the native private desktop. It never reads enrollment secrets,
creates accounts, changes firewall policy or sends desktop input. Each command
has a 20-second limit and bounded output in an owned process tree. No network
isolation result is inferred from the configured setting.

Final source files are archived beside `-12`, with the private evidence manifest.
The 19-file manifest SHA-256 is
`0e8103a69293f99d217aabf01fd90b5c850b7b95324753b6194589ee0590be3b`.
Exploratory source variants were not independently snapshotted; their raw results
and failed expectations remain available, without exact-source qualification.
`writer-boundary-build-01` preserves the earlier compiled fixture/source;
`writer-boundary-build-02` contains the final one. No private paths/SIDs or binary
artifacts enter the gameplay package.

## Focused verification

Compile `tests/fixtures/writer_access.cs` with the installed .NET Framework C#
compiler into private storage. Run `tools/writer_boundary_probe.py` with the
pinned `--codex`, existing `--sandbox-home`, explicit `--writer-sid`, fresh private
`--output`, compiled `--access-fixture` and `--sibling-control`. The final run
exits 1 because the read denial fails; do not omit that control to claim isolation.

With `STRATA_WRITER_TEST_SID` and `STRATA_WRITER_TEST_GROUP` set to the existing
test account/group, the executed command was:

```text
.venv/Scripts/python.exe -m pytest tests/test_windows_writer.py tests/test_gameplay_package.py -q
```

**29 passed in 0.45 s**, no skips. The 28 writer checks cover actual ACL/handle
denials, path/identity/scope rejection, no existing-tree adoption, idempotent close
without a permission reset, and handle release on failed initialization. The
separate compiled gameplay-package exclusion check passes. Ruff passes for all
three changed Python files. No broad suite or unchanged game/model trial ran.

Read-only durable accounting at **06:50:27 UTC** still shows schema 2, original
10,000,000-microUSD cap, one migration, **755,400 microUSD held with uncertainty**.
No Java or writer fixture process remained at that check. The receipt request
is not replayed, settled, refunded or given a new allowance.

## Next M0 work and unchanged gates

Bind protected preparation and the exact restricted writer token/workspace to
the owned server launcher, retaining immutable pins, finite exposure, one-use
intent, cleanup and uncertain-state rules. First qualify that path with a small
Java file fixture before a changed authentic game trial. Independently close
the demonstrated same-account read path through the enforced runtime/tool/broker
boundary; a directory ACL or separate desktop alone cannot supply that claim.
Do not request a VM as a prerequisite or repeat the completed craft trajectory.

M0 remains in progress, G0 fails, G1–G5 are not run. Preserve the 500-ms failures,
five effective-file failures, Mineflayer/E9E incompatibility, loopback canary
failures, uncertain inventory trial, original model hold, full scorer controls,
provenance, parity, recovery and all required/conditional scope.

The mechanism uses documented [Windows restricted-token access checks](https://learn.microsoft.com/en-us/windows/win32/secauthz/restricted-tokens)
and [atomic native file/directory creation](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile).
The [Codex Windows sandbox documentation](https://learn.chatgpt.com/docs/windows/windows-sandbox)
describes the dedicated-account mode; the observed canaries, not that description,
determine this candidate's results.
