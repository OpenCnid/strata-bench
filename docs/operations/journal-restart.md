# Stopped development journal staging

Operator-only; M0.2k.2a, SPEC 12.3. This command replaces manual copying of the
complete native and worker journals. It starts no process and consumes no inference.

```powershell
$env:PYTHONPATH='evaluator/src'
.\.venv\Scripts\python.exe -m strata_evaluator.journal_restart --plan <absolute-private-plan.json> --destination <new-private-directory>
```

The `strata/DevelopmentJournalRestart/1` plan contains:

- `source`: one complete `DevelopmentCostJoin/1`, or a complete
  `DevelopmentRestartCostJoin/1` lineage. See [cost reconciliation](../verification/2026-09-20-run-costs.md).
- `stopped_source` and `authority`: absolute `path`/`sha256` input pairs.
- `next_epoch`: strictly greater than the last source epoch.
- `minimum_remaining_ms`: a positive, explicitly reserved launch interval up to
  1,200,000 ms. Original authority must retain more than this interval before
  staging and before publication. Its expiration and input cap are never renewed.

The private `strata/StoppedNativeSource/1` attestation binds `evidence_kind`,
`campaign_id`, `agent_id`, `epoch`, `native_journal_sha256`,
`worker_database_sha256`, `server_spool_sha256`, `authority_sha256`, and one to
32 supporting `evidence_sha256` digests. Its `processes_terminal`,
`controls_released` and `saved_state_consistent` flags must be strictly true.
`guardian_result` retains either pass or fail. The operator must establish these
facts from actual stopped-source evidence; this API does not authenticate an
attestation or independently observe its former processes. Failed stop timing
is retained even when eventual termination permits a separate continuation check.

The destination contains exactly `native.jsonl`, `worker.sqlite`,
`authority.json`, and a final `manifest.json`. The database must already be a
frozen complete export with no nonempty WAL or rollback journal. Its exact bytes
are preserved, including all tables, counters, events and unknown receipts.
Source files, authority and history are validated again before publication.

Destination creation is exclusive. The manifest is committed last. A crash or
disk failure during publication can leave an incomplete destination; preserve
it for diagnosis and use a new destination for another staging attempt. An
existing directory is never overwritten. Launchers must reject a missing or
inconsistent manifest, recheck its file digests and enforce fresh body, epoch,
grant, observation and original-authority validity before use. This command does
not implement that launch admission.

Before launch preparation, verify the staged set against the manifest digest
retained from the original staging receipt. Do not read the expected digest
from the directory being verified:

```powershell
.\.venv\Scripts\python.exe -m strata_evaluator.journal_restart --destination <staged-private-directory> --verify-digest <original-manifest-digest> --minimum-remaining-ms <required-launch-interval>
```

This rechecks the manifest, every exact file, absence of extra files/WALs,
authority identity, increasing epoch, input headroom and actual current expiry.
It rejects incomplete publication and tampered counters or receipts. Output
contains only verification status, manifest digest and `launched: false`.
The required interval is explicit; there is no CLI clock override. Verification
does not grant process or gameplay authority.

No old observation grants, credentials, native descriptors, locks, world files
or agent state are copied. Unknown actions remain unknown and no requests are
replayed. This is a journal transfer operation, not the complete checkpoint
required for campaign recovery. Full shutdown, isolation, resource reservation,
world/agent restoration and G0 gates remain separate.
