# M1.6c native purpose and account separation

D20 continuation of M1.6. This source boundary is implemented_unverified for
complete native probe integration; M1.6 remains in_progress and G1 not_run.
Affected: F03/F07/F08/F11/F16, N01/N04/N06, C06/C12/C20/C22/C23/C24/C36,
T01/T04/T06/T11/T12. No unrelated M2-M7 work or spending authority changes.

## Change and limits

Campaign startup previously had no explicit prohibition on an evaluation
reservation/account. Later campaign skill-publication rejection did not prevent
the earlier runtime, helper or artifact activity. The shared
[account policy](../../src/mcbench/native_account_policy.py) now requires:

- Campaign purpose: a training or development leaf account.
- Conformance/development-piloting purpose: a development leaf account.
- Matching campaign/agent and reservation category, with consistent classified
  ancestors. Unclassified aggregate accounts may pool classified children; the
  native leaf must be classified. An evaluation ancestor cannot fund a campaign
  through a relabelled child.
- Once running, the leaf category and account also match the original funded
  operation. Switching training to development cannot silently change an
  already admitted job, even though both categories permit new campaign jobs.

Startup checks the reservation and actual account before native intent/process
creation. Request admission checks again before root/helper enrollment or helper
reservation; dispatch checks before forwarding. Existing broker grants check on
use, including after controller restart and before artifact/game/team effects.
This refuses new effects; it does not claim to undo previously admitted work.
All existing reservations and uncertain amounts remain charged. Account labels
are never repaired or changed by this guard.

No probe launch purpose or permit is introduced. A separate disposable native
admission path must bind the prepared pair, matched live state, budget/resources,
fresh context, artifacts and disposal. Within-probe adaptation can use scoped
mutable notes/procedures/scripts; it does not require relaxing the campaign
publisher's evaluation-account rejection. Native catalog/activation and actual
probe execution still need their own integration evidence.

Stopped source/export readers do not apply this live guard retroactively.
Historical source/profile identities remain as recorded. New installed source
and bootstrap inventories must pin the new guard; old native evidence is not
promoted to qualification of changed code.

## Executed verification

With `PYTHONPATH=src;tools;evaluator/src`, the initial selection of
`test_native_account_policy.py`, `test_native.py`, and `test_native_admission.py`
passes83 cases. The next selection passes198 cases; those overlap for230 distinct
cases at that source checkpoint. Review then finds that a training-to-development
reclassification could still pass. Add original-reservation binding and five
cases for that route. The final changed source passes178 live-path cases plus57
stopped-export/revision cases, **235 distinct passes including32 new cases**:

```text
.venv/Scripts/python.exe -m pytest tests/test_native_account_policy.py tests/test_native.py tests/test_native_admission.py tests/test_native_broker.py tests/test_broker_lifecycle.py tests/test_inference_dispatch.py -q
.venv/Scripts/python.exe -m pytest tests/test_native_export.py tests/test_native_revisions.py -q
```

The recorded commands also write private logs/JUnit. A preliminary
regression invocation named nonexistent `test_broker.py`; no tests ran and that
failure is retained. Correcting the selection runs the actual broker suites.

Coverage includes root/helper startup refusal without process/budget intent,
durable purpose/category and ancestry joins, mismatch before enrollment,
prepared-request refusal, existing-grant refusal after reopen, retained costs,
and permitted local root artifacts plus private helper output. Fresh conformance
fixtures now create development accounts/reservations before their source jobs;
no old record is relabelled. Fixtures use synthetic native/provider records and
Python process producers. No new Codex/Minecraft/provider execution occurs.

The first retained-source reader incorrectly required an export row in original
native-game02, whose outer export failure is already retained. Preserve this
reader failure. The corrected read-only check validates that stopped source
directly, plus two committed exports from frozen-note-native01. Both source
seals reverify; database dumps and all source/profile identities are unchanged.
No old job was resumed, rearmed, refunded or rerun.

Ruff and whitespace pass. All40 real authority table hashes match before/after;
exposure remains $4.887796/$10 with every hold and consumed decision. No matching
owned runtime remains. No RuntimeQualification or M1 paid authority is issued.

Private bundle `2026-09-25-m1-native-account-purpose-01`:402 files,
4,655,455 bytes; seal
`f92e172c5c4ca346fbfd950e6b71201611a6399161516b8ccb33d2617c149aa5`.
It retains the source snapshot, executed selections and failed invocation,
both reader scripts/failure, corrected readback, authority and process inventory.
This first source predates original-reservation binding and is retained as such.
Final bundle `2026-09-25-m1-native-account-purpose-02`:398 files,4,647,134 bytes;
seal `cfe8f5e6ff1486031f21b21ce3880d391fc154964fc2b8aa1b192728be0c9a65`.
It pins the final source, both final test selections and repeated unchanged
retained source/export reconstruction, authority and process inventory.

Next: implement the separate native probe bootstrap/artifact admission using a
fresh fully resolved source, keeping campaign activation/publication guards.
Actual paired worlds, resource admission, fresh runtime/caches, N>1 preparation,
development-only practice, one-way canary disposal, combined isolation, T05 and
scorer gates remain open.
