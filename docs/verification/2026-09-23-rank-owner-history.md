# Authoritative rank-map ownership

M0.2c.3b.3c.2c advances the connected positive craft/control required by G0
item5, inheriting .2's F04/F09/F10/F13/F16, N01/N02/N04/N06/N08,
C12/C18/C24 and T01/T06/T07/T10/T13 mappings. M0 remains in_progress/G0 fail.

## Failure path and correction

Case04's authenticated terminal history retained one team-map write after the
client joined, before any worker action. That run has no write-site trace and
remains failed; its counter is never reset or retrospectively relabeled.

Read-only inspection of the pinned FTBTeams1902.2.14-build.123 bytecode establishes
a concrete false-positive path. Both authoritative `Team` and detached
`ClientTeam` inherit `TeamBase`. The login synchronization path constructs a
`ClientTeam(Team)` and calls `ranks.putAll` to populate its separate map. The old
constructor hook installs an armed observed map in both kinds. Its write is
therefore counted even though it does not modify authoritative team membership.
This explains a path consistent with the old counter; it does not recover the
missing call-site evidence from that run.

The constructor now resolves the pinned classes without initializing them and
selects by actual owner type. `Team` subclasses receive armed observed maps;
only exact `ClientTeam` instances receive ordinary detached maps. Unknown owner
types, including unknown client subclasses, reject. There is no runtime switch,
counter refund or temporary monitor disable. Server rank aliases, no-op attempts,
restore attempts, manager maps and the lazy name cache remain observed.

This is module0.3.12/startup13/history5. Producer, live pipe, participant startup
admission, offline reconstruction and private candidate inspection consume the
same exact identity. Versions1–4 remain available under their original policies;
older evidence is not repriced or reinterpreted. Complete mutation coverage and
scoring eligibility remain false.

## Source verification

The selected Python suites pass143 cases with two opt-in skips. The original
Java-signer case then passes with its fixture enabled, and two additional actual
Java-signer cases carry the version4/version5 records into private reconstruction.
That is146 distinct passing cases and one unchanged platform-fixture skip.
After strengthening the predecessor-policy test, all26 affected cases pass again.
The broader telemetry/startup/craft consumer selection adds80 passes and four
unchanged opt-in skips:226 distinct Python passes/five remaining fixture skips.
The Java build/reobfuscation and all40 tests pass offline.

The Java ownership regression reproduces the rank-copy operation and verifies
copy equality, detached mutations leaving server ranks unchanged, server aliases
and restored/no-op writes remaining sticky, unknown owner rejection and missing
runtime rejection. Its class hierarchy is synthetic; actual FTB bytecode and the
changed live trial are separate evidence. Python checks preserve strict module,
policy, schema, hook, counter, rollback, candidate and pipe-ACK rules.

New module SHA-256:
`26c4c3b9528dfbe5e68c3d597e4ac7a62408636d9d25e8c7edf29bcc869d8436`.
Private source preparation `2026-09-23-rank-owner-source-01` records8,609 files /
563,328,208 bytes, preserving the original unplayed fixture and replacing only
the telemetry JAR in a fresh runtime source directory. The original source is
unchanged. Pinned bytecode excerpts are retained outside the public repository.

## Changed connected trial

Fresh case05 is dispatched with the new module/history policy and a declared
45-second worker window. All seven public operations and the1000-primitive cap
remain; retained prior evidence completes those operations in11.269s. Startup270s,
client335s, participant360s, server600s, terminal reserve10s, CPU4/512–6144MiB,
D13 and the native permission policy are unchanged. The change removes idle
worker lifetime that previously prevented admission after a260-second startup;
it does not extend a threshold or drop a check.

Case05 completes successfully. The independent audit passes46/46 checks:

- The client joins after183.422s and all seven public operations pass. It consumes
  five andesite and three polished andesite and crafts one furnace. The saved
  player has exactly one additional furnace, the supplied chest is empty and
  there is no dropped-item escape.
- All239 signed records authenticate to the held module/server identity. Startup,
  both craft points and terminal history agree with the registered actor/team
  and expert mode. Team-map attempts stay0; all other disqualifying routes stay0.
  The sole command is the authorized native stop. The server rank-map hook remains
  verified, with no off-thread attempts or overflow.
- All75 native/worker primitives reconcile. Client lifetime is229.797s; pair
  lifetime515.531s; server dispatch393.578s. The D13 client tree check passes in
  523.0584ms against1000ms. The server exits0 after its normal stop command.
- All29 server outer,120 client outer and14 nested custody processes are terminal
  without forced outer/custody cleanup. Nested counts overlap; the intentional
  D13 guardian termination is separately recorded. The client exits before outer
  cleanup, the session arguments retire and shared desktop input remains unchanged.
- Exact private candidate import succeeds but remains unscorable. Reinspection
  produces no new event; consumed-grant and relaunch attempts reject before dispatch.
  All original39 accounting tables, source fixture and held software remain unchanged.

Sampled telemetry contains4,595 server ticks and232.444540400 callback seconds;
the last health sample records1,461 avatar ticks. These are retained measurements,
not a full active-time/save-authority claim. All471 held inputs were rechecked;
no paid model request occurred. Exposure remains$1.795559 under the original$10.

The positive result verifies .2's history-required connected craft, .2a's declared
startup/worker profile and .2c's narrow owner discrimination. It does not close
the parent setup-authority/scorer gate. Derived wrong-team/mode/operator/command
checks remain labeled derived controls, not separate authentic trajectories.
Native/mod field instructions, method handles, pre-activation authority, mechanical
parity and complete scoring still require evidence. D14 full isolation remains
deferred to M1/G1; M0/G0 remains open. Do not repeat this successful trial unchanged.

## Retained evidence

| Private bundle | Seal / audit SHA-256 | Inventory |
|---|---|---|
| `2026-09-23-rank-owner-source-01` | `a8b118065584f3984f052a9507e0153a61eeba434775b56aa3a230cb3c93044d` / `d78847e4bf5440b6ea904db8cf3cc97cd89f2ca681b025768f6be64481c3277c` | 16 files /310,077 bytes |
| `2026-09-23-protected-craft-heap6-05` | `e26f01bec4a9cd2f20bdb4ea3662865ab9384126ab83dc8e6cd251ad53cb9fde` / `ad235890c07af99130f7c42bbeb640d2ddc2f6ade25aabe045023fb91baf6c79` | 603 files /111,919,063 bytes |

Both inventories rehash through EvidenceBundle. SQLite connections were explicitly
closed after stopped checkpointing; receipts remain outside the sealed roots.
The raw world, credentials, account identifiers, bytecode excerpts and private
evaluations remain outside the public repository. Earlier failures remain intact.
