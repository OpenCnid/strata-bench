# M1.5b.8a — prior telemetry capacity and spool reservation

The capacity dependency exposed by
[operation09](2026-09-26-m1-furnace-interval-native.md) is implemented_unverified.
Source checks pass; a new native reference has not run. Operation09 remains
failed, UNCERTAIN/consumed, and cannot be resumed or promoted from its prefix.

Scope: M1.5b.8a/M1.5b.8, F10/F16, N01/N05/N06/N08, C12/C18/C24 and T01/T10,
with the private-package T06 dependency. Baseline790ef45. Unrelated M2–M7 and
the complete G1 acceptance criteria remain unchanged.

`PrivateReferenceLaunch/8` and `ProtectedReferencePlan/3` add required
`private-reference-telemetry-capacity/1` to the existing protected online
reference. Declare finite authenticated-wire byte and event ceilings before
launch:65,536–1,073,741,824bytes and1–1,000,000events. These are contract bounds,
not a claim that every value can complete every producer profile. The operator
must choose sufficient capacity for the intended bounded verification before
launch. Old launch profiles retain exactly8,388,608bytes/2,000events and their
original wire shapes; existing failed references gain no new capacity.

The nested launch, protected plan, outer pair pins and abort digest all bind
the declared limits. Missing/unknown fields, invalid values, old/new profile
mixing and mismatched nested limits fail admission. The launcher passes the
limits to the existing native producer/broker protocol; the broker independently
requires exact agreement with the prior launch. Encoded signed records count
against its byte ceiling. Exhaustion preserves the durable prefix, emits no
acknowledgment for an unwritten event, and retains uncertainty.

A private SQLite table reserves the complete maximum spool size in the same
transaction as dispatch intent, before native server launch. The check sums
other RESERVED spool capacity for the same volume in this reference database
and requires free disk for that sum, the new hold and64 MiB margin. Duplicate
instance reservations are refused. Competing database connections serialize
through the existing immediate transaction. No expiry or restart automatically
releases a hold, and uncertain/failed work retains its entire reservation.

This is a logical reservation among cooperating launches sharing this private
database. It does not reserve OS disk extents, coordinate separate databases,
or cover unrelated database/log/fixture storage. External writers can still
exhaust disk; failed writes remain failures. It is not full N08 storage or G2
recovery qualification. The already consumed one-use launch preflight is not
refunded if a later capacity reservation fails.

Only complete successful stream/process closure can settle the spool hold.
Require broker STOPPED, matching positive record count, bounded actual bytes,
the original launch/capacity digests, normal server stop and complete terminal
parent history. Capacity consumption and dispatch STOPPED commit atomically;
the actual bytes remain accounted as retained data and only unused capacity
ceases to be held. A missing dispatch, failed journal commit or mismatched
terminal proof rolls back settlement. Failed final settlement records
uncertainty. A consumed instance cannot be rearmed.

Verification executed:

- 163 distinct Python cases pass;62 existing native opt-in cases are skipped.
  The first related-suite selection passed158; three subsequent pair-binding
  cases, one missing-dispatch case and the gameplay-package check add five
  distinct passes. Overlapping runs are counted once.
- The34 new capacity cases cover strict/versioned plans and legacy round trips,
  exact nested pair/abort binding, insufficient space, real concurrent SQLite
  reservations, uncertainty/reopen, missing parent or forced cleanup, wrong
  counts/digests, overspend, transaction rollback, one-use settlement, broker
  mismatch and byte/event exhaustion without another record or acknowledgment.
- Related launch, protected reference, online pair, abort, client registration
  and telemetry-pipe checks pass. The gameplay bundle remains exactly its
  permitted four files; private capacity and evaluator code are absent.
- The original operation08 and operation09 seals verify. Current parsing
  preserves both prior protected-plan wire shapes. Operation08's329-record
  authenticated inspection reconstructs unchanged; operation09 still raises
  `TELEMETRY_CLEAN_STOP_MISSING`. Neither native run is replayed.
- The initial two Ruff findings (unused import and fixture-name shadowing)
  are retained; the corrected focused check passes. No Java producer changes,
  artifact build or unchanged broad/native suite rerun was needed.

Private source/test archive: `2026-09-26-m1-telemetry-capacity-source-01`.
No game/model dispatch, installed-artifact change or inference authorization
change occurred. All40 durable accounting tables remain unchanged at
4,887,796microUSD; D18/D19 remain M0-only.

Next bind a fresh launch8/protected3 reference with declared finite capacity
and the unchanged interval criteria, checker, client, producer and time bounds.
Verify the actual reservation before native launch, encoded byte/event usage,
full retirement/clean-stop evidence and atomic settlement. Retain operation09's
failure and original8 MiB cap. Full interval/replacement, registered scoring
windows, setup/team/loaded-code, controls/parity/isolation and all other G1
contracts remain required. M1 remains in_progress; G1 not_run.

Final integrity audit passes815 source pins,452 unique/preserved milestone IDs
and1,898 local links, with unchanged40 authority tables, installed client/server
artifacts and no owned runtime. The34-file/2,613,388byte private archive verifies
under seal `8d5e7a3166fe7774f5274a256e64677ff10010a2ad64e84407f4679d5a0f39d0`.
This pointer follows the archived document snapshot; the archive is unchanged.
Authentic launch8 integration remains not_run and the M1/G1 goal remains active.
