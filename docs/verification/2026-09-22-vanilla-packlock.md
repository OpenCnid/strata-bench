# Original vanilla PackLock and joint launch sequence

September 22, 2026. Operator-only. M0.3a.2 is verified for the installed vanilla
template/provenance disposition. M0.3a.3 remains implemented_unverified for
authentic joint launch. **M0 is incomplete and G0 fails.** G1–G5 remain not_run.
Coverage: F01/F05/F16, N01/N04/N05/N06/N08, C03/C04/C24, partial
T01/T02/T06/T07/T13 and G0 items 2/4/6. No later milestone advances.

The original `vanilla-1192-20260918` request is now **SEALED**, using its existing
official acquisition receipt and 4,097-file installed inventory. Nine bound
provisioning checks join the retained acquisition, independent role copies,
reviewed bootstrap, transitive sources, compatible roles, frozen settings,
update policy, D05 prerequisites and cold-restart evidence. The checks are
operator attestations over retained evidence, not signed publisher certificates
or a complete game-conformance claim.

The actual PackLock is
`cas:sha256:d85894fca48ae58a95679d713e6d3c30a4cd154ed8a98a00d744ff07afda80a2`.
Its LaunchProfile/2 reference is
`cas:sha256:5ffb76ada9592a4696aebe2eb6db6d921ef9b01b90e66c460ac97fc5df754f8a`.
The receipt and inventory references are unchanged. E9E is unchanged and
unqualified; the five effective-file failures and Mineflayer incompatibility
remain intact.

The final source review accounts for all 2,297 copied Python files: 2,295 match
the exact retained stripped publisher archive and two uv metadata files have
explicit byte/origin dispositions. Node matches the retained publisher checksum;
its complete license text is retained privately. Existing evidence supplies
111 npm package/archive joins, Java and both game roles. Component notices and
absent standalone SPDX/license declarations remain recorded as observed.
Existing D05 account sign-in and explicit EULA acceptance satisfy their user
prerequisites; neither was repeated. No binary redistribution authority or new
blanket legal certificate is asserted.

The [launch implementation](../../src/mcbench/pack_worker.py) fixes a real
ordering defect: starting the server before resolving the worker invalidated the
fresh-instance check as soon as world/log files appeared. Full mode now resolves
both roles first, performs the fixed import preflight, starts its owned server,
waits for readiness and starts the prepared worker. It holds the runtime,
generated configuration and server executable through cleanup. The pinned base
Python runs the process bootstraps, avoiding the venv redirector before Job
Object assignment. The worker stops before one normal server stop request.

Readiness is bounded at 80 seconds; normal development saving retains its
120-second window. An independent watchdog covers readiness, pinned worker
exposure, five-second worker exit allowance and saving, including synchronous
validation time. Failed readiness, startup, logs, process exits, timeout or
watchdog expiry cannot produce a successful receipt. These limits do not change
D13 or establish complete server runtime custody, canonical clean save or clocks.

Executed on Windows, Python 3.12.14:

```text
pytest -q tests/test_pack_worker.py
pytest -q tests/test_pack_worker.py tests/test_pack_launch.py
ruff check src/mcbench/pack_worker.py src/mcbench/pack_commands.py tests/test_pack_worker.py
git diff --check
```

The preliminary selection passed 38 cases. The combined selection passed **69/69
in 56.11 seconds**, including changed-server-tree ordering, preflight/start
ordering, failed worker construction, critical server logs, readiness and normal
stop failures, independent watchdog expiration and owned cleanup. New lifecycle
cases use synthetic processes and real file leases; they are not Minecraft
acceptance. Final review added explicit interruption failure retention; the final
affected selection passes **41/41 in 29.06 seconds**, giving **70 distinct passing
source cases** across these selections. The sealed source snapshot precedes this
interruption-only correction; its evidence is synthetic and does not add an
authentic run. Ruff and whitespace checks pass. Two existing Typer/Click
deprecation warnings remain.

The first **actual sealed materialization and import-only run pass**: the real
11,722-file runtime loads under held bytes, with three total owned processes,
zero active/terminated processes and parent exit zero. Preparation took 80.812
seconds, the import process 1.828 seconds and total run 83.469 seconds. It starts
no server, authenticates no account, dispatches no model and performs no game
action. Full joint launch and its native action/recovery connection remain
unverified. The fresh materialized instance is retained outside this evidence
bundle for that next changed-profile integration.

Original-authority conservation was checked before preparation, publication and
import. Only objects, outbox and the original vanilla provisioning row change:
50 objects and 52 outbox events are added across publication/materialization.
All old object/event rows, the other provisioning row and **31 other tables**
remain unchanged. After sealing, import/materialization adds just one event;
33 tables stay unchanged. The original $10 allowance, **$0.7554 unresolved hold,
$0.001458 settled usage**, uncertainty and consumed D12 state are unchanged.
No new authorization, replay, refund or inference admission occurred.

Retained failures: the initial unstripped Python archive comparison found one
missing and 41 changed files; the exact stripped archive resolves that mismatch.
The first preparation attempt has no final result or captured original stderr;
its retained script incorrectly treats the native checks dictionary as a list.
The corrected second attempt then fails while finding a nonexistent D06 text
delimiter. Both sources/partial outputs and the second traceback remain intact.
The third preparation and actual publication/import succeed. Historical 500-ms
failures, D12 reply failure and all scorer/isolation/recovery gaps are preserved.

Private evidence:
`C:/Users/Darian/.strata/evidence/2026-09-22-vanilla-packlock-01`.
Its complete 84-file, 78,675,269-byte seal verifies through EvidenceBundle:
`9ec032343c1fef8e4e7622389342b445e417ab4989f02096d7313b728ef7afec`.
It includes original-authority backups, exact new proofs/source snapshots,
publisher bytes, retained failures and the actual import receipt. Credentials,
installations and private records remain outside public source/gameplay access.

Next connect the existing native Dovetail/root/helper/action runner to this
sealed launch and inventory-bound capture. Then collect the changed-profile
joint run/recovery evidence while keeping scorer/setup, E9E provenance,
isolation, authoritative clocks and remaining fault cases open. Do not repeat
the unchanged import or old development pair as substitute evidence.
