# M1.6h held protected copies of both probe worlds

D20 continuation; affected F04/F08/F09/F11, N01/N04/N05/N06/N08,
C12/C22/C23/C24 and T01/T06/T07/T11. M1.6h is implemented_unverified
for game/native probe integration. M1.6 remains in_progress and G1 not_run.

The coordinator consumes the complete prepared pair and exact private writer
plans for both arms. Every source path/hash/size comes from the registered
world inventory; no additional file, missing arm, shared identity, overlapping
namespace or excessive copy storage/deadline is admitted. Original world and
native-view handles remain held throughout. The existing native writer copier
creates separate fresh protected destination trees; the coordinator borrows both
together and rechecks exact world bytes while writer namespace/token custody
and the complete pair's evaluation/capacity holds remain live.

The operator continuation cannot outlive the borrowed copies. This version
requires both writers to remain unlaunched and then explicitly discards their
custody. A discarded copy is not a stopped server, successful probe, erased
world or qualified one-way disposal. A consumed launch attempt cannot take the
unlaunched-discard path. The copy pair is single-use, and failure closes nested
writers before original input leases while retaining all capacity and costs.

## Verification

**47 distinct focused source cases pass**, including paired custody, missing or
changed sources, partial arms, identity/path conflicts, deadline/storage refusal,
continuation failure, authorization and explicit unlaunched-discard semantics.
The coordinator unit cases substitute writer execution/token custody; they are
not native evidence. Two changed coordinator cases pass again after adding the
shared executable/companion lease. Ruff and whitespace checks pass.

```text
PYTHONPATH=src;tools;evaluator/src
.venv/Scripts/python.exe -m pytest tests/test_probe_world_copies.py tests/test_writer_custody.py tests/test_writer_preparation.py -q -x -k "not actual_native_pair"
.venv/Scripts/python.exe -m pytest tests/test_probe_world_copies.py -q -x -k "both_exact_worlds or continuation_fault"
# Set STRATA_PROBE_WRITER_RUNTIME to the private, checked existing runtime pins.
.venv/Scripts/python.exe -m pytest tests/test_probe_world_copies.py -q -x -k actual_native_pair
```

The actual native test passes in35.36s on case03. It runs the pinned native
Windows sandbox and Java copier with synthetic N=1 source worlds, existing
sandbox enrollment and no Minecraft/model process. Both protected copies are
live together, match the registered source and deny operator writes; original
source files also deny writes. The actual retained process tokens bind to the
registered online writer identity. Each copier exits0 without force, with
10/10 retained processes signaled, zero active/terminated processes and complete
logs. Both lifetimes finish DISCARDED/unlaunched, and same-pair reacquisition
under new output paths refuses. Source fixture teardown fences its preparation
owner while retaining both synthetic envelopes (200 units) and all capacity.
That is48 distinct passing tests including the native case, not a full G1 pass.

Retain both earlier native failures. The historical app-install executable path
was missing; the preserved private runtime had identical bytes but unsuitable
access for the lower-privilege launcher. Case01 fails with Windows error5 before
Java identity/copy admission;7/7 processes stop, exit1, no force. The existing
[verified runtime-path correction](2026-09-23-pipe-history-integration.md) selects
the same runtime bytes at their already-readable location, plus a fresh protected
workspace under a traversable public parent. No private ancestor ACL changes.
Case02 then reaches Java but rejects WRITER_TOKEN_SCOPE_MISMATCH: an old offline
writer identity was paired with the online profile. All10 processes stop with
forced exit125; no copy is admitted. Case03 uses the recorded online identity
from the existing successful protected-reference preparation. It preserves the
same runtime/home/helper and all token checks; it does not derive authority from
whatever token happens to arrive. Every attempt uses fresh fixture state; failed
stores, holds and paths are retained, never repaired or rearmed.

Read-only reconstruction passes58/58 checks across all three native cases. It
joins complete arm plans and prepared-world digests, original byte hashes,
shared runtime companion pins, actual retained token/process receipts, explicit
discard states, write-denial and replay-refusal observations, failure/forced-stop
history and retained budget/capacity holds. All original databases and bundle
seals are unchanged. Forty real accounting tables match before/after each case;
exposure remains $4.887796/$10 with every hold and consumed decision intact.
No owned runtime remains. D18/D19 stay M0-only; no paid M1 execution occurs.

All private names below use prefix `2026-09-25-m1-probe-world-copies-`:

| Store | Files / bytes | SHA-256 seal |
|---|---|---|
| 01, first source and error5 | 1,991 / 14,205,787 | `5d096cde904800c0821486de03642264e973d9a0b443177353cebeca9f5764bd` |
| 02, companion leases and token refusal | 820 / 7,255,915 | `89975ec9c457079ba485d4b896a44ab2735a8f03c967725fd45a5fb465a83fea` |
| 03, native copy pair pass | 558 / 5,841,130 | `9c3bb63e34bbbd461a4d7b7a3cf866eba6602d86e67a4873829eb7a77a25ecd4` |
| audit-01, read-only reconstruction | 3 / 9,241 | `1be896da1123118e740fb7f06e5a60175573a8fbc8fe326567805e343395ab77` |

The online native writer profile declares direct networking and does not prove
network or sibling-read isolation. The original worlds remain immutable while
the new protected copies admit only the intended native writer. Their paths and
bytes are retained after closure; no deletion or post-probe erasure is claimed.

## Remaining acceptance

Copying exact private world bytes is not observing matched live game/body/keymap
state. Connect reviewed immutable game software, held launch/broker/worker
lifetime, all-N readiness, native probe dispatch, registered controls, stopped
exports and one-way session/artifact disposal. Keep the native launch and
purpose/account gates closed until that complete coordinator exists. N>1
positive preparation, full combined isolation, T05 and scorer acceptance remain
open. Unrelated M2-M7 work and M0-only inference authority remain unchanged.
