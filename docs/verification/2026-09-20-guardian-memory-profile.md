# Guardian shutdown and retained JVM heap

M0/G0 reliability diagnostic; F09/F11, N02/N03/N05/N06/N07;
partial T07/T08/T12. This is a changed resource profile, not a reliability pass.

Both phases of the latest [Forge restart pair](2026-09-20-forge-reconnect.md)
missed the unchanged 500-ms stop bound. The independent held-process observer
still saw the roots alive more than 670 ms after termination started. Phase 01
ended with 5,925,367,808 resident bytes and 6,828,437,504 private bytes. The
earlier passing client-role trial ended with 1,850,347,520 resident bytes and
5,876,748,288 private bytes. This correlation does not establish causation.

The exact installed Temurin 17.0.20.1+1 JVM reports G1 enabled, periodic G1
collection disabled (interval zero), and default free-heap ratios 40/70.
The [Java 17 G1 guide](https://docs.oracle.com/en/java/javase/17/gctuning/garbage-first-g1-garbage-collector1.html)
documents periodic collection and resizing unused heap with the free-space
ratios. The [Java command reference](https://docs.oracle.com/en/java/javase/17/docs/specs/man/java.html)
also notes that lowering these ratios can reduce footprint with a possible
performance cost. Neither source guarantees a process termination deadline.

Candidate resource policy `g1-periodic-heap-return/1` adds:

```text
-XX:G1PeriodicGCInterval=10000
-XX:MinHeapFreeRatio=10
-XX:MaxHeapFreeRatio=20
```

Concurrent periodic collection remains at its JVM default. Bounded private
GC/heap logs retain the actual collection evidence. The heap remains 512–4096
MiB; client mods, game options, server and saved resources remain unchanged.
Client/worker/action/guardian bounds remain 480 s/90 s/5 s/500 ms. No pre-kill
cleanup allowance or delayed start of the guardian clock is introduced.
This resource identity is recorded in the private preparation and pinned JVM
argument template; it must not inherit prior capacity or scientific claims.

The actual JVM accepts these flags in a local `-version` invocation. The complete
new private preparation and cached-session checks pass. A single authentic
read-only diagnostic completed under
`C:\Users\Darian\.strata\evidence\2026-09-20-guardian-g1-profile-01`.
The paired runner failed before the bridge or worker became ready. Its automatic
audit retained a missing-public-report error; a separate startup-failure audit
completes the applicable checks without overwriting that failure.
No inference or shared-desktop input; raw failures and the prior profile remain.

The diagnostic uses the existing craft-witness world and the read-only client-role
procedure. The failed restart pair used the original cancellation-reference world
and different actions. These are different workloads: a passing diagnostic cannot
by itself establish a remedy for the failed restart profile. Retain that scope
distinction when comparing memory or deciding the next resolving action.

Actual outcome: `GAME_BRIDGE_STARTUP_TIMEOUT` at the unchanged270-s bootstrap
bound; client procedure277.906 s, paired runner469.891 s. No native bootstrap,
authority, journal or worker database was created; no scoped action was possible.
Guardian500-ms conformance was not run. Outer cleanup confirms the root terminal,
arguments retired, input desktop unchanged and normal server stop; zero Java
processes were independently checked. Full saved Inventory/EnderItems and position
are unchanged, while Attributes and warden_spawn_tracker differ and are retained.

The complete private server spool has265 records,5403 sampled ticks/272.5801656 s
and final tick5416. GC logs retain631 pause lines and27 concurrent-mark lines;
no periodic collection is observed. The last logged heap is1901/2114 MiB. The
frequent collections and startup failure disqualify this candidate; they do not
prove an underlying cause of the original shutdown failures. No unchanged retry
is planned. All prior profile failures remain.

Observed native inputs are zero because authority and the worker were never
created; the full native/worker cost join is not_run because those sources do
not exist. Linked references now retain744 primitives/8879.972 s, plus witness
setups266.907 s, the prior15.760-s interphase gap and other historical scopes.
No inference. Initial audit hashad9e48865385ea46b24a4c8709f9b61a11fafb09ecb7dfa1ce170fb8da1651b0;
completed startup-failure audit2503e68f579208eee3463cf9f3dbb4ff5f3eb9b0412bde3863f34a4cd39ccae2.
The latter passes its eight applicable failure/cleanup checks while the trial
and profile remain failed. Original audits, GC logs, client/server logs, exact
source pins and saved-player bytes remain private.
