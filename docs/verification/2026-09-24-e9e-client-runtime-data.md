# E9E client runtime-data loading and restart

M0.3a.4k remains **in_progress**. The journal-capable snapshot agent passes actual
client loading and restart. Corrected reconstruction passes **37/37 checks**;
retain the original **36/37** audit, whose extra read-count assumption was wrong.
No game replay was used to correct that audit. M0 remains in_progress and G0 fail.

Coverage: F01/F05/F06/F16, N01/N04/N06/N08, C03/C04/C24, partial T01/T02/T13,
G0 item 2. This follows the [reviewed Forge transformation](2026-09-24-e9e-class-loading.md)
and preserves D14, D18/D19, original accounting and M1–M7.

## Producer and consumer change

The non-input client launcher deliberately inherits no console handles. An early
stderr message therefore cannot be its sole runtime-data evidence. The existing
agent now creates a unique `logs/strata-fixed-<pid>-<uuid>.log` in the private
operator instance. [Data.java](../../java/runtime-data/src/io/github/opencnid/strata/fixed/Data.java)
serializes and forces each record to disk before also writing stderr. Bounds are
32 records, 128 KiB per record and 1 MiB total. Invalid log paths refuse startup;
write/quota failures halt the owned JVM with exit 126. Prior complete records
remain, and a later launch creates a different file.

The records contain the existing resource-index identity, reviewed class bindings,
body-read hashes and bounded refusal diagnostics. The admitted class hashes,
single-URL transformation, three publisher bodies and vendor JARs/signatures
remain unchanged. This changes the harness artifact, not the downloaded rules.

The shared [runtime-data consumer](../../src/mcbench/runtime_data.py) requires the
expected PID in the journal name, bounded complete records and exactly the known
marker set. Every observed read must use the expected body hash; repeated reads
of those same bodies are permitted. Missing inputs, unknown markers, foreign
hashes, truncation, wrong PID and refusals reject. The server tool uses the same
marker parser. The execution owner still separately binds the real process and
holds the snapshot JAR; matching text alone is not process authority, signed
scoring evidence or isolation qualification.

The prepared 11,084-byte JAR is
`7e6aadaf5db1bf01db427f0adf060dae54c0b5a7b9bb76304f199e19e931943f`.
Its source/resource/compiler/class pins and both installed copies are retained
privately. Older snapshot artifacts and their results remain preserved.

## Authentic connected clients

Fresh `e9e-frozen-client-01` role copies independently verify all original
12,917 client / 8,799 server files and directories, then add only the new agent:
12,918 / 8,800 files. Original VERIFIED roles are unchanged. The client resolver
rehashes all 3,786 software files and checks its credential-free template before
execution. Both roles hold the same agent/receipt alongside their runtime files.

The bounded profile is `e9e1270-frozen-client-config/1`: one server, two sequential
client launches, fresh private plans/session argument files, existing authorized
cached sign-in, no input injection, no gameplay policy and zero inference. The
server retains its 300-second startup/120-second graceful stop bounds; each
client retains its 420-second owned lifetime. The outer server watchdog remains
1,280 seconds. The three independent immutable-file leases remain within their
existing 1 GiB bounds.

| Evidence | Client 1 | Client 2 after restart |
|---|---:|---:|
| Startup/config capture seconds | 160.922 | 156.141 |
| Owned terminal processes | 8 | 8 |
| Journal records | 8 | 6 |
| Whitelist / blacklist / IE reads | 2 / 2 / 1 | 1 / 1 / 1 |

Both clients bind the two exact classes, read all three exact snapshot bodies,
connect and capture the six selected config roles. The snapshots match each
other and the retained pre-snapshot settings. Client-only registrations and
legacy unregistered settings keep their explicit dispositions; Create and
Sophisticated Core COMMON values agree with authenticated server evidence.
Both private argument files are retired, and the input desktop is unchanged.

Clients deliberately terminate their owned Jobs after capture. All eight handles
in each are signaled, with no watchdog trigger. This verifies bounded loading and
restart, **not** clean client saving or D13 conformance. The server stops normally,
exit 0, with all three owned processes terminal. The connected sequence takes
**532.125 seconds** and records **6,652 server ticks**; its expert recipe matches
the earlier authentic reference.

The first audit incorrectly required both clients to have eight records and
exactly two reads of each Cable Facades list. Only the first client did so. The
original 36/37 result remains intact. Both invocations already satisfied the
implemented contract: at least one read of each required body, every read pinned,
and bounded records. Corrected reconstruction checks that contract and passes
37/37 on the unchanged evidence. The vendor callback clears its four maps/lists
before rebuilding them; no claim is made about the cause of the extra first-boot
callback or complete consumer/cache equivalence.

## Source verification and retained limits

Windows/JDK 17, retained Python environment, `-X utf8`, project `src`,
`evaluator/src`, `tools`, `tests` on PYTHONPATH:

- `pytest tests/test_runtime_data.py tests/test_runtime_data_journal.py
  tests/test_e9e_cold_start.py -q`: **47 pass**, 31.07 seconds.
- After adding the repeated-valid-read regression, `pytest
  tests/test_runtime_data_journal.py -q`: **9 pass**, 0.16 seconds.

These overlap: **48 distinct cases** pass. JVM fixtures cover absent console
handles, distinct launches, preserved records after quota halt and invalid log
paths. Python cases cover record/identity rejection. Full Ruff and diff checks
pass. A trailing-blank-line finding and a private driver helper-name collision
were corrected before final verification/execution respectively.

Stopped capture retains all changed files: client **25 files / 5,597,980 bytes**;
server **123 files / 28,530,250 bytes**, with no removals. Existing software,
mods, scripts, assets and agent bytes are unchanged. Existing changes are the
BYG backup ZIP in each role and server.properties; the latter has identical
non-comment lines. Among 7,123 client config files, only the BYG ZIP changes
between client boots. First-boot ZIP bytes were not separately captured, so
this result does not assert timestamp-only equivalence for that client ZIP.

Forge version checking remains enabled in the retained config. Inspection of
the installed VersionChecker classes finds HTTP version/status/changelog
metadata processing, with no automatic installation path found in that inspected
code. This is a bounded review finding, not proof about every mod's runtime
downloads or completion of provisioning's update/input review.

All **39 original authority tables** remain unchanged after the connected run.
Exposure remains **$2.831942/$10**, with every unknown amount reserved. No model
calls or gameplay commands are introduced. E9E stays VERIFIED, not SEALED. The
successor inventory/profile, remaining startup-input dispositions and thirteen
provisioning checks remain open, as do the other G0 outcomes. D14 isolation
deferral is unchanged; no protected-scoring or scientific-validity claim is made.

## Cold server restart with the final artifact

The server-only pair in the preceding report used the artifact before journals
were added. After the connected sequence above stops normally, one cold server
restart qualifies the final journal-capable artifact against that stopped world.
This is a changed-component check; neither prior successful pair is replayed.

Cold-start `/2`, epoch 2, passes in **151.125 seconds** with **18 authenticated
records / 202 ticks**, both class bindings and one read of each snapshot body.
It preserves expert mode and the exact recipe. Its three Create values and
Sophisticated Core COMMON query agree with the corresponding projection of the
first server's broader six-role query. It stops normally with all **3/3** owned
processes terminal. Across the connected sequence and this cold restart, all
**22** owned game-process handles are terminal; no Java process remains.

The first cold reconstruction helper fails on a nested-field lookup
(`KeyError: process_id`), before writing a verdict. Its source/failure record
remains retained. Corrected reconstruction passes **10/10 checks** against the
same recorded run, including distinct boot authority/epoch, exact stopped
journal, unchanged selected setup and all 39 original authority tables. No game
or model replay is used for either audit correction.

Next finish the remaining startup-input/update dispositions and bind these
results to a distinct successor inventory/profile and thirteen provisioning
checks. Reuse the qualified client/server loading evidence; do not repeat these
successful launches unchanged. Whole-pack mechanics, automatic-update admission,
seal/materialization and the remaining G0 outcomes are not promoted by this
bounded result.

Private evidence `2026-09-24-e9e-frozen-client-01` is sealed: **300 files /
88,641,486 bytes**, complete EvidenceBundle readback pass. It includes both
client captures, both server scopes, every journal, source/build pins, original
and corrected audits, and stopped file deltas. The final server cold delta adds
**27 changed/new files / 22,592,091 bytes**, with no removals or software changes.

- Seal: `75cbb308318a46a98415d86f614c591f100a373c8cd38716bc854f3d1721a62e`.
- Original 36/37 audit: `bcd7f162567cf5678d4d476854c46b7d17983eb59e26820d119c84bf1ff6b3c7`.
- Corrected 37/37 audit: `754fe0d0cd5d905cdf04333f1796cac5bc5ef9d88597d77a58882df66a4ac7c4`.
- Corrected cold 10/10 audit: `351e773e4b6862c810a557df5d4ff265e0fd6d55896d890b9b4d4c9137ea95e0`.
