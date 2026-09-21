# M0 checkpoint-bound learned skill activation

September 21, 2026. Operator-only. M0.1c.2b.2c.6 is **in_progress**.
Coverage: partial F03/F04/F07/F09/F11/F16, N01/N02/N04/N06/N08,
C06/C07/C08/C12/C14/C16/C17/C19/C20/C23/C36,
T01/T04/T06/T07/T11/T12/T13 and G0 items 1/6.
M0 remains incomplete; G0 fails; G1–G5 remain not_run.

## Implemented scope

[native_skill_activation.py](../../src/mcbench/native_skill_activation.py)
implements `native-checkpoint-learned-overlay/1`. A committed complete checkpoint,
including the game and matching native agent component, is required before
activation. Source-bound candidates become active revisions in one private
transaction, with immutable initial files and the registered retention policy
preserved. Repeated creation returns the same set; a failed transaction publishes
none of it. Activation grants neither dispatch authority nor script execution.

The native view contains the complete retained root workspace, immutable
`active/<name>/` files and a matching `.agents/skills/<name>/` loader tree. Only
the reviewed plain `name`/`description` frontmatter format is accepted. Supporting
references/scripts/assets are text; nested SKILL.md files and native dependency
configuration are rejected. A sanitized `active/revisions.json` exposes only
skill names and revision IDs so authors can name exact parents. Private source,
checkpoint, accounting and provenance records are not projected there.

Materialization stages and verifies every file before publishing the directory.
Its durable registration is required for launch. A crash after rename can leave
an occupied, unregistered target; retries reject it rather than silently granting
authority. A launch must use its own agent/campaign/model, a later nonstale epoch,
the current system identity and the exact bootstrap-held view. Root/helper set
references affect profile identity; absent extension fields preserve legacy
serialized plans and historical source hashes.

[native_admission.py](../../src/mcbench/native_admission.py) checks the actual
native developer catalog before enrolling a participant or reserving a helper
envelope. Missing, foreign, duplicate or disabled learned entries reject. The
native workspace catalog is shared with clean-context helpers, so this candidate
requires explicit supply of the same complete immutable set to helpers. It does
not claim per-helper native catalogs. Helpers receive its read-only active files;
root notes/drafts/handoff and private provenance are excluded. Scoped projection
is one transaction and does not overwrite later mutable writes on another call.
Existing authorization, usage holds and qualification requirements still apply.

[native_revisions.py](../../src/mcbench/native_revisions.py) adds version 2 of the
publication request, bundle and publication records. Replacement candidates
must name their exact active predecessor and a fresh revision ID; unchanged
inherited files retain parent generating-call provenance. Version 1 keeps its
null-parent contract. [Checkpoint retention](../../src/mcbench/native_checkpoint.py)
uses a typed version-3 skill component when it retains an active set, preserving
the activation reference instead of relabeling active files as drafts.
[Exports](../../src/mcbench/native_export.py) verify the exact supplied active
inventory; complete-set materialization copies its metadata privately.

## Verification and limits

- Initial 21 activation tests passed; expanded 29-case activation suite passed.
  These include complete-checkpoint admission, idempotency, crash boundaries,
  scope/model/epoch checks, exact file inventory, metadata restrictions and
  atomic scoped projection. Projection transaction tests isolate the separately
  tested grant authenticator; they are not native helper qualification.
- The affected revision/checkpoint/export/admission/gateway suite passed 120
  tests. An earlier command named nonexistent `test_native_bootstrap.py` and ran
  no tests; the corrected command is the 120-test result.
- The subsequent activation/revision/Windows-integrity/broker suite passed 114
  tests. Windows sharing checks use real owned files. The sanitized revision
  index was added during final review and has a separate final activation run.
- The integrated pre-reservation helper denial test passed: no helper participant,
  child envelope or additional budget consumption appears after rejection.
- Final activation suite: **36 passed in 113.46 s**, including the revision
  index and integrated helper-admission ordering case. Ruff on changed Python
  files and `git diff --check` pass. Test counts above overlap; they are not
  cumulative distinct-case totals.

The actual pinned CLI was used only for `debug prompt-input`, with an isolated
profile, the unchanged pinned Dovetail installation, a local rejecting provider
sink and no credentials. Public documentation identifies the supported
`.agents/skills` loader, while the pinned binary supplies the actual behavior:
[official skill documentation](https://learn.chatgpt.com/docs/build-skills).
This metadata command does not expand an explicitly requested skill body.

Private `native-loader-01` retains the unsupported `debug --strict-config`
failure. `native-loader-02` retains the wrong model-catalog path failure.
`native-loader-03` exits successfully and discovers the catalog but fails its
explicit-body-injection assertion. These are unresolved invocation evidence,
not native execution passes. All three record zero provider requests.

Private `native-activation-01` then checks an actual view produced by the new
source implementation: 16/16 checks pass, including a committed synthetic
checkpoint, reopened state/cost continuity, both native learned catalog entries,
the original implicit Dovetail entries, a disabled-entry rejection and no
supporting-file prefetch. Helper denial applies the source guard to the captured
catalog; no native helper executes. `native-activation-02` repeats only this
changed-view question after adding the readable revision index: 16/16 pass,
zero provider requests. Its set reference is
`cas:sha256:3331bdfde212edaee6873d1f81d1b685ba62aef24f03265a255d3ee86216eeb2`.
Neither report claims loader qualification or dispatch authority.

The synthetic checkpoint setup has four constructed receipt records and 56
fixture units in each independent store; no inference produced those records.
Do not label them actual charges or experimental API-equivalent consumption.
The original private authority was rechecked read-only: same authorization
digest `7aca7758f12eb1089f481d5d4bc19de2c6022cf1167b03056c32d41c3e4a819a`,
same unresolved 755400-microUSD hold, counted once, with no reset/refund/replay.

Private evidence is sealed under `.strata/evidence/`, outside public source and
gameplay access. Final `native-activation-02` includes its source/test snapshot
and executed-check summary: **829 files / 7,814,049 bytes**, manifest SHA-256
`f7caa17e37efea239b993ec9775690e31409879da529ede74144927be2f80500`.
The earlier activation prototype is retained separately (781 files / 7,199,715
bytes), seal `71f9970f1fc05781e404a15ff6eb921542298355b8cfa0e04a696cf4a19f7eec`.
Retained loader-01/02/03 seals, respectively:
`7515a420bc690ef4c71ff8d2ea3580b6cd51120ec94211bd3e7ffdcd0c5478da`,
`90efb36c1e474ae368e37f6bf833e18163d6956dc18be919316564cd1f40dc00`,
`7f4f2a34d4e0edc40adcc056b69f61587b01d9fcb55a97c55807a23c2b93b7d6`.
Do not mutate these sealed stores when continuing integration.

Post-seal source review corrected the checkpoint copier's database attribute
(`self.database`, rather than `self.db`) on the newly retained-active branch.
The 28 existing native checkpoint tests pass in 26.87 s after that correction;
Ruff/whitespace checks pass. The sealed snapshot precedes this one-line repair.
Those tests do not establish second-generation active-state materialization;
that remains part of the integration work below.

## Remaining acceptance evidence

Run the changed actual CLI/local-synthetic-provider profile through the real
activation/admission/enrollment route: root and explicitly supplied clean helper
must load/read unchanged bodies and supporting files, reject writes and foreign
state, then export/checkpoint a subsequent revision with its active lineage.
Verify full and frozen retention on that second generation, fresh process
restoration and interrupted activation. This is not covered by metadata rendering
or the isolated source tests. General native invocation, executable snippets and
bounded macros, complete game/backend restoration and the private evidence join
remain required.

No new OAuth request or Minecraft process was launched; shared desktop input
remains paused. Preserve all native sibling/loopback failures, 500-ms shutdown
failures, five effective-file failures, Mineflayer/E9E incompatibility and remaining
scorer/control/parity/provenance/recovery gates. No threshold or required M0–M6
scope changed; M7 and other extensions retain their activation conditions.
