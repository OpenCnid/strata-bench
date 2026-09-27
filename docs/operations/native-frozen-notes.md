# Native frozen-skills note categories

Operator-only. SPEC13.2 permits notes and handoff in frozen-skills while keeping
initial procedures immutable. This is a packaging intervention: prose may still
encode a procedure. It is not a claim that all implicit learning is removed.

New frozen-skills campaign execution uses `strata/NativeRetentionPolicy/2`,
`native-preregistered-retention-checkpoint/2`, with the exact
`frozen-notes-markdown-no-code/1` classifier. The policy and initial artifact
inventory are registered before execution and bound to campaign/agent identity.
The operator schemas are [v1](../../schemas/v1/operator/NativeRetentionPolicy.json)
and [v2](../../schemas/v1/operator/NativeRetentionPolicyV2.json).
Version1 remains readable and usable in explicitly synthetic conformance;
it cannot authorize frozen-skills campaign execution. It acquires no new
classification evidence. Other arms keep their existing policy identity.

## Write and checkpoint boundaries

The broker rejects new/changed `skills/` packages and publication requests in
the v2 arm. Initial packages may be read, but cannot be rewritten. Root notes
and handoff, and helper result files, must use `.md` or `.txt` prose. Classification
occurs before CAS mutation and is checked again under the final write transaction.
Rejected attempts retain their broker call accounting and cannot replace an
existing accepted file.

Successful classified writes append `broker.note_classified`, binding the
classifier, policy reference, caller, path and content reference to the original
broker call event. The record explicitly says `implicit_procedure_ambiguity=true`.
No agent-provided classifier verdict is trusted. Initial note registration and
both recovery/episode checkpoint reconstruction recheck the same policy. A
checkpoint cannot launder an injected code note or changed procedural package.

## Declared lexical classifier and limits

The [classifier](../../src/mcbench/native_note_policy.py) normalizes Unicode NFKC
for inspection, retaining original accepted bytes. It rejects control/format
characters, fenced/indented code, shebangs, skill frontmatter, executable HTML,
recognized native tool references, common programming declarations/calls,
interpreter command forms and structured tool/procedure payloads. Whole JSON
objects/arrays are outside this prose format. Ordinary headings, bullets,
resource identifiers, observation receipt hashes and natural-language conditional
advice remain permitted. False positives are possible under these declared rules.

This lexical check is not a semantic or general execution-security classifier.
Encoded or unfamiliar representations and procedural meaning in prose remain
ambiguous; do not call this absence of all procedural knowledge. Retain accepted
content references, sample actual produced notes, report ambiguity and investigate
any executable packaging bypass before qualification. No sampled model-produced
native note audit or full category qualification is claimed by source tests.

The native code-mode/tool boundary, initial-skill immutability, no active learned
overlay, fresh conversations/caches and one-way probe disposal are separate
requirements. Full, frozen-persistence and no-self-play are unaffected by this
classifier; their different retention and helper rules remain binding.
