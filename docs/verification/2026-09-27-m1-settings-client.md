# M1.1b private settings client and interrupted-effect recovery

The Python operator client now exercises the production Java settings coordinator,
transaction store, avatar lane and authenticated HTTP bridge. Apply, bounded effect
observation, query after a lost reply, duplicate refusal and owned-value rollback
work across that interface. Actual JVM process death/reopen also works after fixing
a reproduced journal parser defect. Body/input are synthetic in these tests;
Minecraft key effects, complete T05 and G1 remain unverified.

## Interface and recovery

`src/mcbench/native_settings_effects.py` binds the private game descriptor and
separately pinned settings fingerprint. Strict requests/results include the full
transaction, revision, plan, binding, context and stage identities. Status queries
must match the original effect request. Bounded typed observations remain raw
evidence: neither `verified=true` nor `committed=true` is accepted. A stage label
does not prove a restart. Mutations send one POST; ambiguous outcomes retain IDs
for queries and are never automatically replayed. Descriptor errors hide secrets.

`SettingsEffectsCoordinator` extracts the existing production coordinator so the
cross-language fixture exercises the same transaction/input ownership logic as
Minecraft. The native adapter still supplies actual observations and key input.
The test-only body, input and deterministic process-kill boundary remain outside
the client JAR and the gameplay bundle. No gameplay capability is advertised.

The first process-death test failed on journal reopening with
`SETTINGS_JSON_NUMBER`: the game journal used the settings-only unsigned-integer
reader, which rejected decimal coordinates in effect observations. The game frame
schema now uses the existing bounded signed/finite game-number reader. Settings
frames retain their stricter reader; sequence validation and hash verification
are unchanged. Focused tests cover fractional/signed coordinates, byte-preserving
reopen and append, altered-coordinate hash failure, invalid numeric sequences and
continued settings-number rejection.

The corrected cross-language failure case kills an actual fixture JVM between
complete ticks, then reopens the same authority and journals. Old input stays
fenced, forward replay is refused, explicit rollback restores only owned settings,
and consumed primitive counts are retained and increased by cleanup. This is not
evidence for arbitrary torn writes, native Minecraft effects or full recovery.

## Executed verification

Private evidence: `2026-09-27-m1-settings-client-01` in operator storage.

- Python schema/transport: 42 passing cases. The first changed-file Ruff run
  found five test formatting errors; original output is retained and corrected.
- Initial integration/package run: 45 pass, one process-death recovery failure.
  Logs and the failed fixture's profile/settings/game journals are retained.
- After the parser fix, only the failing cross-language recovery case was rerun:
  pass. Together these establish 46 distinct passing Python cases, including
  three actual JVM/HTTP scenarios and the gameplay-package exclusion check.
- Java: 25 coordinator/effect/protocol cases before the parser fix; four new
  journal tests plus 40 affected settings-store/game-lane regressions after it
  pass. These 69 cases use synthetic game/input ports. Offline JAR build and
  reobfuscation pass; existing Gradle deprecation warnings remain.

Commands use pinned Java 17.0.20, the existing offline Forge dependencies,
`java/gradlew.bat -p java --offline :forge1192-client:test` with the named test
classes, and `:forge1192-client:writeTestClasspath :forge1192-client:jar`.
Python runs set `PYTHONPATH=src;tools;evaluator/src` and the explicit JVM/classpath
fixture variables. No broad unchanged suite or paid/game trial was repeated.

## Remaining acceptance and next action

M1.1b remains in_progress. Next prepare the authentic ordinary-input intended and
competing effects cycle on the changed exact client profile. The capable extension
still needs the complete conflict/context/modifier/hold matrix, essential-control
checks, charged restart/effect/rollback cycle, skill integration and isolation.
T01/T04/T05/T06/T10/T11 and G1 retain their aggregate not_run dispositions.

D20 implementation authority is unchanged; D18/D19 inference authority stays
M0-only. This work uses no model calls or Minecraft launches. Original failures,
consumed decisions and three independent telemetry holds remain in custody.

Final custody audit: 40 durable authority tables unchanged; exposure 4,887,796
microUSD; all three separate 268,435,456-byte holds preserved; zero Java processes.
All 458 milestone IDs and the append-only history remain intact; local links and
changed-file lint pass. Evidence seal: 44 files, 2,545,150 bytes, SHA-256
`2306ebda630eafb66bd99cf68c073ac3e4536f9abfcafe59fd4e9b7139e6cf78`.
Candidate JAR SHA-256:
`da05588764c3c93234a61f98eaaea89fea80a668777dc780ae48f63a96e44ae4`.
The artifact has not been installed or qualified in Minecraft.
