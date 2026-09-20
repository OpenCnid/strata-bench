# Private Windows Java lifetime guard

Operator-only. M0.3b.2c.3a is the standalone foundation; M0.3b.2c.3b now connects
the Forge-aware guardian to the version 2 development worker. Neither is a
gameplay command or campaign-admission certificate. Initial tests used disposable
synthetic JVMs. Subsequent [authentic E9E trials](../verification/2026-09-19-stop-latency.md)
retain partial gameplay evidence and failed timely termination; production
qualification remains open.

`mcbench.process_guard` holds a Windows process handle and checks the exact PID,
100 ns creation FILETIME, canonical executable path and on-disk executable SHA-256
against an explicit private grant. It accepts only `java.exe` or `javaw.exe`.
It does not inspect process arguments, environment, account names or credentials.
FILETIME is a decimal string, avoiding JavaScript number precision loss.

The grant authorizes ownership of a **dedicated client's whole lifetime**.
After successful attachment, stop, timeout, pipe failure and guard exit all
terminate that client. There is no detach/disarm command. Termination is never
reported as confirmed input release or a clean game/agent checkpoint, including
when Windows reports exit code zero. Interrupted actions remain uncertain and
require resynchronization; this component cannot settle their primitive costs.

## Private operator interface

Read-only identity inspection (use a known dedicated process ID):

```powershell
uv run --frozen python -m mcbench.process_guard --inspect <PID>
```

This returns four fields: `pid`, `created_filetime`, `executable_path`, and
`executable_sha256`. Inspection does not attach a Job Object or authorize a kill.
An operator-owned supervisor must construct the following strict grant, stored
outside the source repository and gameplay workspace:

| Field | Contract |
|---|---|
| `schema` | `strata/JavaProcessGuardGrant/1` |
| `purpose` | `dedicated-development-client-lifetime` |
| `campaign_id`, `agent_id`, `epoch` | Intended operator scope; positive epoch |
| `process` | Exact four-field identity from inspection |
| `expires_unix_ms` | Future absolute expiry, at most ten minutes away |
| `max_wall_ms` | Immutable lifetime cap, 1–600000 ms |

Unknown/duplicate fields, expired grants, files over 8 KiB and linked/reparse
paths reject. Scope labels are not authenticated controller grants and are not
proof that this process owns a particular native bridge or avatar.

The supervising process starts:

```text
<pinned Python> -I -m mcbench.process_guard --grant <absolute private grant file>
```

It must use hidden process creation on Windows and dedicated stdin/stdout pipes.
After the guard validates the held identity, obtains exclusive guard ownership,
and attaches a kill-on-close Job Object, it emits `ready` with a process digest
and the grant's scope. A failed attachment does not emit readiness. It then emits
a fresh random `challenge` every 250 ms after the preceding answer. The parent
must answer the exact current `seq` and `nonce` within 1500 ms:

```json
{"kind":"renew","seq":1,"nonce":"<exact current challenge nonce>"}
```

Only one outstanding challenge exists. Stale/replayed answers cannot extend the
lease. `{"kind":"stop"}` ends the dedicated client lifetime. Input lines are
bounded to 1024 bytes and both IO queues are bounded. Separate daemon IO threads
keep blocked pipes from blocking the watchdog loop. Absolute expiry is converted
once to a local monotonic deadline; renewals cannot extend it or the wall cap.

The guard polls at 10 ms and requests job termination once. It requires both the
held root handle to signal, zero active processes in the held Windows Job and
signaled observation handles for every process in its cumulative accounting.
At attachment, each guard poll and immediately before stopping, it retains
read-only handles for the job's current members and verifies their membership.
The inventory is capped at 256 lifetime handles; quota, truncated inventories,
unavailable handles or missed short-lived members prevent a confirmed stop.
These handles never grant termination by PID. Processes created before job
attachment remain outside this proof. The root wait and subsequent checks share 500 ms; descendants
receive no additional allowance. A late zero count, remaining descendants or
query failure cannot confirm stop. OS scheduling can exceed these engineering
targets; exact-profile measurements remain required. `stopped`
events explicitly include `termination_confirmed`, `release_confirmed=false`,
`requires_resync=true`, elapsed time and termination wait. Events on pipes are
best-effort diagnostics, not a durable controller evidence journal. A guard
crash may have no final event; its owner must independently reconcile the exit.

## Remaining integration and qualification

- The Forge-aware route described below adds native session/listener ownership,
  independent client-thread health and worker lifecycle evidence. Qualify it
  against authentic Minecraft and controller-issued authority before admission.
- Integrate process outcomes with complete controller/aggregate budget settlement
  and recovery. A forced exit or incomplete parent journal is not a clean stop.
- Qualify startup containment and all existing descendants. The attached Job
  Object includes children created after attachment, not earlier children.
- Prove authentic Minecraft timing, complete coordinated shutdown/checkpoints,
  resource/archival handling and OS/filesystem/network isolation. Private files,
  named exclusive ownership and Job Objects alone are not a gameplay sandbox.

The process and mutex handles are not inheritable. Unexpected guard exit closes
its last job handle and terminates associated processes according to the Windows
[Job Object contract](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).
Required attachment rights and nested-job behavior follow
[AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject).

## Non-input desktop launch wrapper

The operator [DesktopJava](../../src/mcbench/desktop_client.py) launcher now joins
the non-input-desktop primitive to the independent base Java guardian. It is a
development startup/whole-lifetime tool, not the Forge-aware worker route below.
Only reviewed Java commands are accepted. A new private directory receives the
grant and an exclusive forced-to-disk launch journal capped at 64 KiB. Arguments,
environment and challenge nonces are excluded from that journal.

The caller must pump the challenge protocol regularly; a blocked caller cannot
renew the guardian lease. Startup/readiness validates the held Java identity.
Normal close sends stop and requires terminal confirmation; guardian crash or
missing confirmation fails, while nested kernel jobs still terminate owned
processes. Four disposable real-JVM tests cover ordinary stop, stalled parent,
guardian crash and invalid startup. No successful process stop is a clean game
checkpoint. This wrapper does not perform authentication, join a world, arm the
native lane, expose physical input or certify filesystem/network isolation.

Base-guardian failures retain a bounded uppercase fault code; unexpected
exceptions use PROCESS_GUARD_FAILURE without exception text. DesktopJava accepts
only the exact failure-event fields and journals the failure separately from a
confirmed stop. A later observation that the PID is absent cannot retroactively
turn that failure into a passed termination deadline. Failure retention and
rejection of extra private fields have two additional synthetic tests; authentic
world-client results and remaining timing gaps are recorded in the
[native startup report](../verification/2026-09-19-desktop-world.md).

## Forge-aware worker route

`strata/ForgeDevelopmentWorker/2` requires `process_guard_file` and `guard_python`.
The parent invokes `python -I -m mcbench.forge_guard --grant <private file>`
with hidden Windows process creation and a minimal environment. The selected
Python must be 3.12.14, with the exact operator implementation loaded. Eight
guardian/dependency source hashes are included in the broker capability identity
and checked against the guardian's own readiness digest. Old version 1 Forge
worker configs reject; the vanilla worker schema is unchanged.

The Forge-specific grant has schema `strata/ForgeProcessGuardGrant/1`, all base
grant fields above, and these additional required fields:

| Field | Contract |
|---|---|
| `connection_file` | Protected absolute native game descriptor path outside source/gameplay trees |
| `connection_digest` | SHA-256 of the descriptor's RFC 8785 canonical JSON, including its actual private bearer value; never serialize a redacted SecretStr for this hash |
| `native_fingerprint`, `body_fingerprint` | Exact source/profile and avatar identity pins |
| `capability_digest` | Current compiled broker capability digest, also loaded in native action authority |
| `primitive_limit` | Same immutable native/worker local limit, 2–100000 |

This remains an operator development grant, not an authenticated production
controller capability. Native authority must already name the same campaign,
avatar, body, capability and primitive limit. The native lane must be healthy,
fenced, have no active action and have an older epoch. Failed preflight does not
attach or arm the JVM; the worker cannot publish a public grant without guardian
readiness. The worker rechecks the same connection digest and body generation
before its ordinary native arm request.

Windows TCP ownership inspection accepts only the exact IPv4 loopback listener
or its IPv4-mapped IPv6 representation, owned by the granted PID. Wildcard binds,
another JVM's listener and changed connection files reject. The held creation
identity still protects against PID replacement at attachment. Native reads use
the descriptor's session and bearer; no game mutation or settings operation is
issued by the guardian. See Microsoft's
[GetExtendedTcpTable](https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable)
and [owner-PID row](https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid)
contracts.

An independent thread samples `identity` and `lane_status` once per second after
the preceding sample, each with a 500 ms request timeout. Changed listener/body/
generation/epoch, unhealthy native journal or read failure ends the dedicated
client lifetime. Even if HTTP reads stall, the guard loop rejects a sample older
than 1500 ms. Parent challenge renewal also requires a worker heartbeat no older
than 200 ms. The parent holds one unanswered challenge during worker startup;
it may answer it when a fresh heartbeat arrives, without extending its deadline.

The guardian's remaining wall/authority lifetime must cover the worker's entire
requested wall limit **plus 2250 ms** at readiness. Normal worker exit waits for
lane release/journal close, then stops the guardian and dedicated JVM. Unexpected
guardian/native failure fences and terminates the worker. A failed guardian stop
or missing termination confirmation prevents a successful worker exit status.

`supervisor-EPOCH.jsonl` is an exclusive, forced-to-disk, hash-chained private
log capped at 1 MiB. Versioned frames include a source clock ID, UTC/monotonic
timestamps, guard intent/readiness, worker PID/exit, and terminal guardian
evidence. Raw grants, native tokens and challenge nonces are excluded. The parent
must record readiness before sending the worker its configuration. A parent
crash can leave an incomplete journal; it must not be inferred to have a clean
checkpoint from a Java exit code. Complete archival, disk-fault recovery and
controller reconciliation remain .3c/.2c.2 work.

The current Forge route also retains `guard_stop_requested` before pipe dispatch
and `guard_termination_timing` from the guardian's `job-call-wait-tree-qpc/2` policy.
The latter records the QPC start as a decimal string, clock resolution and relative
nanosecond job/wait/tree-check boundaries, the existing 500 ms wait bound,
active/total/held/signaled process counts and separate job/wait/tree outcomes. A root failure leaves
the tree check unstarted. A root success still needs `tree_result: empty` and a
timely zero active count with total = held = signaled > 0. Zero accounting alone
was observed before a child's process handle signaled; it is insufficient.
An incomplete lifetime inventory is an explicit failure. On timeout the tree timestamp can mark the deadline check
after the last accounting query; retain the last count as such, not a new query.
The guardian queues it only after closing its owned handles.
Node rejects duplicate/malformed/contradictory records and still requires a
separate confirmed-stop receipt plus timely empty-job evidence. Diagnostics alone cannot prove successful stop,
input release or a clean checkpoint. Missing terminal evidence remains missing.
Process-local call timing includes scheduling/wrapper overhead; UTC and the time
another observer sees a record do not identify the kernel call's exact start.
The base guardian does not emit this extra record. See the
[direct timing report](../verification/2026-09-19-stop-boundaries.md) for actual
checks and unresolved authentic failures. No deadline or gameplay capability is
extended by this diagnostic. Historical policy-1 records remain evidence for
their original candidates; they cannot pass the current supervisor contract.
See the [owned-job report](../verification/2026-09-20-guardian-tree.md) for the
new fixture checks and retained authentic stop failures.
