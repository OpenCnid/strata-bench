# Private operator grant/revoke control

Operator-only. M0.2c.3b.3c.3; parent F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24, T01/T06/T07/T10/T13 and G0 item 5.
This is a diagnostic negative control, not a scientific sample or scoring grant.

`PrivateReferenceLaunch/7` adds `private-operator-roundtrip/1` to the existing
one-use headless launcher. It binds the target's agent ID, Minecraft UUID,
strict player name and level 4 to the sealed roster and unexpired sealed profile
cache. The initial operator file must be empty. It accepts no participant,
caller-supplied command text or alternate endpoint; version-6 world-mode control
behavior remains unchanged.

Only after the existing authenticated clear startup/native-identity gate does
the launcher journal and send one fixed grant. It waits for native feedback,
independently preserves the intermediate operator file and requires exactly the
registered identity/level with no player-limit bypass. Only then does it journal
and send one revocation. Neither uncertain write is replayed, including after
restart; failed/partially changed private clones remain consumed evidence.

Normal completion additionally requires the complete authenticated stream,
exactly three command attempts (grant, revoke, stop), one operator add/remove,
one correlated native stop, no other mutations, no avatar ticks and no craft.
Intermediate archive/log-prefix integrity and independently archived final empty
operator state must agree. The terminal signed history remains tainted and all
scoring/full-history flags stay false. Existing public-field/map/KubeJS mutation
gaps, custody/isolation limits and positive craft/history gaps remain open.

The production telemetry module and its current hooks are unchanged. The added
JVM fixture fabricates command effects and files but exercises production signing
and owned launch/cleanup. Offline pinned Gradle compilation and a fresh telemetry
test classpath pass (five tasks, 17 seconds). Final operator/world-mode/owned-launch/
signed-history/gameplay-package selection: **134 passed**, no skips, 36.13 seconds;
Ruff passes. These checks cover target/cache/expiry/command rejection, interrupted
grant/revoke journals and writes, wrong or missing intermediate effect, failed
restoration, foreign scope, missing/reverted/off-thread counters, archive/log
tampering and no replay. The actual owned-JVM fixture includes normal completion,
no grant effect and failed restoration, while preserving old world-mode tests.

## Authentic changed-control reference

One fresh E9E 1.27.0 / Forge 43.4.23 headless reference completed normally using
the existing telemetry 0.3.7 JAR
`ea112c9e2cd9d5573a407a5e7a35cb075425ba7b1408e24ecc5a6c219cd2a93e`,
official ServerStarter 2.4, pinned JRE 17.0.20.101, online loopback port 25591 and
the unchanged 2–5 GiB heap, 300-second run and 120-second cleanup limits.
There was no avatar connection, model request or shared-desktop input.

The independent audit passes **46/46** checks. Intermediate `ops.json` contains
exactly the preregistered UUID/name, level 4 and no player-limit bypass; the final
operator file is empty. Signed terminal counters retain exactly three command
attempts, one operator add, one remove and one correlated native stop, with every
other mutation counter zero. History remains tainted; no craft candidate or score
is produced. Original fixture properties/NBT agree with clear native startup,
and all four durable control stages appear in order. Repeated import adds no
event, and the consumed reference cannot launch again.

All six retained server-process handles are signaled; all ten outer owned
processes exited normally with complete logs and no forced stop. Observed server
and surrounding CLI intervals are 161.281 and 165.359 seconds. The authenticated
stream has 16 records, 207 sampled / 218 final server ticks and no avatar ticks.
All 18,225 original input files and 1,541 immutable runtime files rehash unchanged.
The complete 104-file sealed fixture remains separate. Original accounting's
34 tables, 756,858-microusd combined exposure, uncertainty and consumed D12 are
unchanged.

The private preparation helper ended with an assertion failure because its
local `before` variable was reused for server-property bytes. Its preceding
copy/seal checks had completed. The original failed helper is retained alongside
an AST-based failure review; independent comparison and the separately executed
runner's own prelaunch assertion establish unchanged original accounting before
Java started. No preparation or game case was replayed to conceal this error.

Private evidence: `C:/Users/Darian/.strata/evidence/2026-09-22-operator-control-live-01`.

| Artifact | SHA-256 |
|---|---|
| Independent audit | `e8d7e2122680aa06fbb7447d834b7af56175a83cd53779cfbd04454746b1e48f` |
| Authenticated stream | `f5d9463ba6adb1a795e63e1026c910ad09b5590b13f601e59257f700fcd4fdb6` |
| Complete evidence seal (188 files / 42,924,655 bytes) | `55d1d6104155b505210eb734a7a8eef4faac70373df5b7ff37c09b6088cb8f40` |

M0.2c.3b.3c.3 is **verified for this narrow negative-control contract**. Full
setup/history authority and positive craft/history integration, team/direct-write
routes, protected custody, isolation and scoring remain open. M0/G0 stays
in_progress/fail. Do not rerun this unchanged successful control.
