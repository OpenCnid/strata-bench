# Bounded bundle preparation

September 21, 2026. Operator-only. M0.3b.2c.3c.2b.2b.2.2a.6b;
F09/F16, N01/N03/N04/N06, C14/C18, partial T01/T07/T12/G0.
M0 is incomplete; G0 fails. This work addresses the exposure failures retained
in [the JVM profile report](2026-09-21-jvm-resource-profile.md).

Preparation `/3` stages the same source files into at most three sequential
512-MiB bundles under the original one-GiB aggregate limit. The implementation
is [writer_staging.py](../../evaluator/src/strata_evaluator/writer_staging.py),
connected through [WriterPreparations](../../evaluator/src/strata_evaluator/writer_preparation.py)
to the [pinned Java copier](../../evaluator/java/StrataWriterPreparation.java).
Each original file keeps its destination, size and expected digest. Bundle
hashes are transport pins; they cannot replace source authority. Original
inputs, complete bundles, manifest and helper remain leased. Java consumes
whole files at contiguous offsets, rejects holes/overlap/revisited bundles,
surplus bytes/path escapes/corruption, creates destinations new and forces
contents. The existing complete copied-tree hashes/ACLs, native token/Job
binding, one-use grants and all deadlines remain. Legacy flat plans and
receipt shapes remain supported. Pair admission also requires the new source
module to be pinned.

The fresh flat-file profile in private `2026-09-21-staging-profile-01` copies
8,609 files / 563,288,796 bytes in 8.256 s; its instrumented lease takes
47.258 s. Reopening that staging takes 4.646 s, with native calls separately
timed. The first profile includes cProfile overhead and the later one has warm
inputs; neither certifies production latency or identifies an OS cause.

Source/Java component verification: `test_writer_staging.py`,
`test_online_reference.py`, `test_writer_preparation.py`,
`test_protected_reference.py` and `test_writer_custody.py` pass **98/98 in
5.54 s** with the explicitly pinned installed JDK. An initial run retained
10 failures/88 passes: the manifest used extended Win32 path spelling that
Java rejected. The fix preserves the Java-compatible spelling while keeping
Win32 validation. The gameplay-package exclusion check passes separately.
These are source and operator-account JVM component checks, not native
sandbox or game qualification.

Private `2026-09-21-bundle-staging-01` exercises the complete same 8,609-file
input: two bundles stage in **4.260 s** and acquire their leases in **1.159 s**;
the actual Java copier exits zero in **10.470 s**. All five component checks
pass, including exact destination inventory, every destination digest and
unchanged original sources. The JDK is Temurin 17.0.20.101; helper class SHA-256
is `18fa2b9445df79ab605bef4989a73bb98ece563668fe8124ad5ec70a9f160a89`.
This is an operator-account file-copy component, with no Minecraft/model
dispatch and no writer-isolation or complete-preparation claim.

Fresh integrated `2026-09-21-protected-craft-cpu4-03` uses that helper under
preparation `/3`, the four-processor client profile and the original
600-s server / 120-s cleanup / 900-s outer bounds. It does not reuse failed
scopes 01/02 or their grants. At the observed HELD state, native copier return
is 27.562 s and complete tree verification is **86.531 s**; the staging record
binds two bundles and all 8,609 source files. Final game/client/shutdown and
terminal custody evidence fails as recorded below. The changed native
preparation fits where earlier flat preparation took 196.282 s; this single
comparison does not establish a latency guarantee.

The real client joins and completes all seven declared operations, including
the resource-consuming expert craft. Independent reconciliation accounts for
**79 primitives**, 267 signed records and 5,279 sampled server ticks. The
32-check trajectory audit retains **28 passes/four failures**: paired lifecycle,
500-ms guardian, closed protected custody and sealed candidate. Both original
and copied source inventories remain unchanged. The 22-check CPU-profile
audit passes, including both effective-argument checks, full client exposure,
unchanged original accounting and consumed D12. Neither audit qualifies scoring.

**The CPU profile does not fix shutdown.** The native guardian's wait lasts
**512.8631 ms against 500 ms**, returns timeout and never checks the process
tree. Termination-call start to wait return is 513.4218 ms; the independent
held-handle observer sees exit by 598.6167 ms from that start. Preserve these
different measurements. Pair status is `uncertain` at 573.765 s; client status
is `fail` at 264.438 s, including 173.203 s startup. The server stops normally,
but outer custody remains uncertain after the client failure. All 29 server
and 122 client held process histories are terminal, no Java remains, client
arguments retire and the input desktop stays unchanged. Do not repeat this
unchanged CPU profile or promote the failed reference.

Private evidence seals (SHA-256 of each `manifest.json`):

- `2026-09-21-protected-craft-cpu4-03`: 611 files;
  `2ad596724ebea33e465a5f5f54ed15974e37eca80af980c2faafda450dce0a85`.
- `2026-09-21-bundle-staging-01`: 8,621 files;
  `e892fe807665a453068d670d7f98be6fcbfaf03d0fa6dbd94b866122e692f3c5`.
- `2026-09-21-staging-profile-01`: 8,614 files;
  `fe4cf93dee52496d70bc02809dfe9f152149e29934a97f416f510d1fd90872f8`.

Both earlier CPU-scope manifests and every listed byte verify unchanged.
Preparation `/3` has authentic component evidence; complete writer custody,
setup authority and shutdown remain unqualified. Continue independent M0
acquisition/provenance work while retaining this failed shutdown profile.

Original accounting remains $0.7554 unresolved plus $0.001458 settled, with
D12 consumed. No new model request or shared-desktop input is authorized by
this change. All earlier 500-ms failures, five effective-file failures,
Mineflayer/E9E incompatibility and scorer/setup/isolation/provenance/clock/
recovery gaps remain.
