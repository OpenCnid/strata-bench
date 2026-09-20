# Machine feedback repair and private startup binding

September 20, 2026. Operator-only. M0.3b.3.2.4b.2b/.2c; partial
F03/F06/F09/F11/F16, N01/N03/N04/N06, T01/T03/T04/T06/T07/T12/T13.
Implementation checks pass; authentic repair qualification is pending.

The [actual operation](2026-09-20-machine-crafting.md) produced three ingots and
consumed 12,000 RF, but its deposit acknowledgment became unknown. The source
admits a possible cause: full-menu packets have no request identifier, and the
first arriving packet can occupy a feedback ticket even if it predates the click.
The original sample did not capture private prediction/reply differences, so this
is a supported race hypothesis, not a proven diagnosis of that particular failure.

Machine policy `thermal-visible-slot-owned-transfer-feedback/2` and Forge
capability minor 35 permit **one additional charged fixed full-menu refresh** only
when the first response exactly echoes pre-click owned inventory/cursor, and
current owned state equals either that state or the prediction. The click is never
repeated. The next server reply and current owned state must exactly match every
predicted player slot and cursor. Other gifts/loss/components, second mismatches,
invalid prediction, lost context, budget or deadline exhaustion remain failures.
Processing changes to machine storage are still separate from transfer evidence.
The native private log records when this narrow echo path is used.

A rebuilt JAR also changes the native runtime fingerprint used in broker authority.
The new optional `strata.awaitGameAuthority` barrier publishes a bounded immutable
private identity record, with exact fingerprint bytes, before any transport/action
lane exists. The operator validates runtime/artifact/capability pins and atomically
publishes the existing static authority. It supplies no dynamic gameplay grant and
keeps the original startup and process watchdog bounds. Deployment isolation and
complete artifact sealing remain unqualified.

Executed checks:

- Pinned Forge compilation/reobfuscation succeeds. **55 selected Java tests** pass
  for machine transfer, generic inventory/feedback, the durable action lane and
  bootstrap identity publication. Regressions exercise stale pre-click replies,
  rejection after another stale read, exact fresh confirmation, unsolicited owned
  changes, cancellation, charges, no input replay, bounded identity bytes,
  no-overwrite and malformed authority. Synthetic effects remain labeled.
- TypeScript build and **12 focused Node checks** pass; that initial selected file
  reports 43 JVM opt-outs, not full integration coverage. **Four explicitly enabled
  JVM/broker cases** then pass with zero skips: actual bound observations/charges,
  capability authority rejection, higher-epoch accounting and scoped CLI routing.
- **24 Python-to-pinned-JVM checks** pass; targeted Ruff passes. No broad suite rerun.

Installed client JAR SHA256:
`32e0fb4a097dff95a8dc224990aa6f87cc3ae902676c416bc5f9f033b18f6085`.
Installation occurred only after all Java processes ended. The previous candidate
is retained externally. Source/build logs and install receipt remain in the private
`2026-09-20-machine-conformance-02` evidence directory.

The fresh epoch-2 development continuation ended on the existing world.
It must observe current resources, collect existing output and perform the expert
craft without repeating the prior unknown deposit. This is not a complete campaign
checkpoint restore or a refund of prior exposure. Prior 521.719 s and 27 primitives
remain part of the aggregate development history. Actual identity binding and output collection passed their narrow checks; expert crafting stopped at an empty JEI query. The collection does not establish that the optional pre-click echo branch fixed the original ambiguous deposit. See the [saved-state result](2026-09-20-machine-crafting.md).
