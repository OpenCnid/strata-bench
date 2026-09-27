# Controller joins verified commit to private worker resume

M1.1c.3.4 now connects the controller's confirmed commit and stored verification
to the same worker's private resume endpoint. This is a candidate component,
implemented but unverified in Minecraft. T01/T04/T05/T06/T10/T11 and G1 remain
`not_run`. Campaign completion, public controls, full settlement and the selected
gameplay skill remain unfinished.

`NativeRepairResume.resume_committed` requires the adopted replacement checkpoint,
original and replacement connection digests, matching body, guardian/4, original
worker plan and expiry, confirmed native commit and complete supplied verification.
It rereads actual native continuation identity and the committed settings head
before consuming a resume decision. The original repair ownership, deadline and
reserved, non-uncertain budget must still permit dispatch. Neither this component
nor its tests issues qualification for the supplied verification producer.

One durable intent precedes the worker request. An uncertain reply reconciles by
status using the same stored decision; no second resume or extended lease is
created. The private witness explicitly records campaign permission unpublished
and consumption unsettled. The controller avatar stays suspended and generic
`Reconfigurations.finish` continues to refuse worker-backed completion.

A known resume response followed by failed validation or evidence publication
attempts native stop and controller recovery. A second failure writing the
uncertainty ledger cannot skip that stop attempt. A failed stop transport remains
a failure; this is not a guarantee of termination through a broken transport.

## Executed verification

- Two actual Python → Node worker → Windows guardian → replacement JVM cases
  pass: verified-commit resume and lost worker reply followed by status-only
  recovery. The body, settings qualification and verification producer are
  synthetic. Five adoption-evidence substitutions, a foreign resume binding and
  uncertain accounting are rejected before recording resume intent. The same
  lease is retained; controller campaign permission stays withheld.
- Four synthetic fault cases pass for evidence-store failure combined with
  available/failed recovery-ledger writes and available/failed stop transport.
  All reach the stop attempt and controller recovery path. They do not prove
  actual Minecraft stopping under a storage fault.
- Ruff and `git diff --check` pass for the changed implementation/tests and diff.

Commands: `pytest tests/test_controller_restart_jvm.py -k resume -q --tb=short`
with explicit Windows Node/Java/classpath; then
`pytest tests/test_native_repair_resume.py -q --tb=short`.
The first connected run passed 2 cases; the changed evidence checks passed the
same 2 cases in the second run. These are two unique scenarios, not four.
Four unrelated restart parameters were deselected, not rerun or claimed anew.
The fixture uses pinned Python 3.12.14, Node 24.19.0 and Java 17.0.20.1+1.

## Remaining end-to-end acceptance

Join complete consumption settlement and qualified public keymap/revision
publication to the original lease before permitting campaign completion. Current
worker observations still have structured-action epoch metadata and a null
keymap; they cannot stand in for qualified settings observations. Private worker
resume physically opens its candidate action lane, so withheld controller
permission alone is not a qualified runtime boundary. Keep this path outside
admitted gameplay until those joins are enforced together.

Controller rollback/resume still needs verified restored effects. Complete the
qualification issuer, real launcher, repeated repair lifecycle, selected skill
and full authentic context/failure/isolation matrix. Preserve essential-native04's
unresolved native-health failure; no unchanged real-game retry was performed.
No model call, installed game change or M1 inference spending was made.

Private evidence is retained under `2026-09-27-m1-controller-resume-01`; the final
seal and durable-state audit are appended below after verification.

Private evidence bundle `2026-09-27-m1-controller-resume-01` is sealed:21 files,
2,415,996 bytes, SHA-256
`3f005fef69fdbf0868733a44cfaa98dd2b9bb01dafacbcc66d22df26e33a9f44`.
All40 authority tables and eight retained telemetry holds remain unchanged.
Installed JAR/options are unchanged and no owned runtime remains. All460 ledger
IDs are preserved;2,113 local links in the five reviewed documents resolve.
The bundle contains the source snapshot before this seal pointer was appended.
