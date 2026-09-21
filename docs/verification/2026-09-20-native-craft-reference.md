# Corrected sealed M0 client craft reference

September 20, 2026. Operator-only. M0.2c.3b.3a/.3b/.3b.1/.3b.2;
F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C12/C18/C24,
partial T01/T06/T07/T10/T13 and G0 item 5. M0 remains in progress,
G0 fails and G1–G5 are not run.

## Implementation and preparation

The real `python -m strata_evaluator.reference_launch` entrypoint exposed a
class-identity mismatch between its `__main__` model and the imported client
validator's model. A subprocess regression reproduced rejection of a valid
client binding before launch. Both preflight and held-file checks now pass
serialized wire data across that boundary. The test deliberately omits the
bootstrap pin, proving that the real CLI reaches the expected later rejection
without any process dispatch or consumed reservation. Focused client-binding
checks pass **28/28 in 2.62 s**; the initial failing regression is retained.
Ruff and whitespace checks pass.

The prior actual body-mismatch failure remains preserved. Its cleanly stopped
state supplies the next reference: four furnaces and the eight still-unused
declared inputs. No inventory rollback or new ingredient gift occurred. The
new game copy preserves all 18,227 source-instance files and seals the complete
104-file prelaunch world with 1,540 immutable software pins. The ephemeral
server session lock is excluded from the stopped clone. The new endpoint/body
identity is computed independently from the registered endpoint and actor.

Preparation failures are retained separately from authentic runs:

- Bundle `2026-09-20-craft-reference-live-02` exceeded the existing 1-MiB
  declaration limit by embedding the full source inventory. It never launched
  or consumed a launch reservation. The corrected declaration pins a separate
  inventory file; the limit is unchanged.
- Bundle `2026-09-20-craft-reference-live-03` initially used the flat credential
  cache verifier on an already populated game tree. The same native ACL reader
  then verified its protected root without changing ACLs. Its successful seal
  was superseded before dispatch when the CLI bug was fixed. Its authority,
  files and zero-reservation state remain preserved.
- Bundle `2026-09-20-craft-reference-live-04` pins the corrected source and clean
  typed registration, reusing only the never-launched game copy. The driver
  derives scope/body/exposure from that registration and compares the actual
  native identity before arming gameplay. Credentials/raw data stay private.

The actual reference uses E9E 1.27.0, server telemetry 0.3.5, the existing
minor43 Forge bridge, client diagnostics 0.3.2, Windows x64, Python 3.12.14,
Node 24.19.0 and Temurin 17.0.20.1+1. The client retains its 3-GiB heap profile
and the non-input desktop/API facilities. Registered exposure is participant
380 s, client 365 s, worker 90 s and terminal reserve 15 s; server 600 s,
maximum graceful stop 120 s and guardian 500 ms are unchanged. The longer
client window accommodates measured startup, not a looser shutdown criterion.

## Authentic outcome

**Uncertain; no craft or worker was admitted.** The server passed native/process
binding and published readiness at 196.781 s. The actual client body matched
the independently registered identity; it reached its fenced ready state at
265.641 s of client time. The first private frame was captured. Its durable
request and authority timestamps show only **99,331 ms** remaining before that
frame, less than the unchanged **90,000-ms worker + 10,000-ms margin**. The
registered worker could therefore not be admitted after the frame. This is a
bound derived from retained timestamps; the client's final exception was not
preserved, so it is not represented as an observed terminal error code.

The outer monitor caught a `Fault` at 466.375 s and forced both process trees
down before either inner terminal report was written. It recorded the exception
type but omitted its code. A process-inventory race is a hypothesis, not an
established cause. Both outer Job reports show zero active processes, but held
member signal counts were incomplete and log-drain completion failed. No Java
or owned outer PID remains. After that fresh process check, the temporary
credential argument file was retired; the authentication cache was preserved.

| Preserved evidence | Result and limit |
|---|---|
| Native client identity | Registered endpoint/body match, fenced lane and captured frame; no worker grant or database |
| Native action journal | One profile record; zero epochs, intents, primitives or receipts |
| Server stream | 263 authenticated prefix records through tick 5,312; no craft; complete inspection rejects `TELEMETRY_CLEAN_STOP_MISSING` |
| Saved bytes | Inventory and eight declared inputs remain; copied as explicitly **unclean**, not a qualified checkpoint |
| Source | All 18,227 parent-instance files and pinned implementation files unchanged during the trial |
| Durable dispatch | Last `PARTICIPANT_READY` state retained, then operator recovery appends `UNCERTAIN` with the terminal observation; one consumed reservation remains |
| Import/replay | Incomplete import rejects; launcher rejects its existing evidence path, and direct preflight independently rejects the consumed grant |
| Guardian | `not_run`; no new 500-ms timing sample or qualification |

The final abrupt-stop audit passes **15 checks preserving this uncertainty**.
Its first revision had 14/15 passes because it expected the later consumed-grant
error instead of the launcher's earlier existing-path rejection. Both revisions
and the separate direct-preflight rejection remain preserved. The successful
craft audit was prepared but never executed. There is no resource-consuming
craft witness, native actor/team craft point, complete cost join, clean-stop
claim or protected score. No shared input action was issued; the interrupted
driver did not produce its final unchanged-desktop receipt.

Next implement typed outer-monitor failure reporting and bounded abort/report
coordination that retains uncertainty while allowing the inner client/server
cleanup to report, with hard watchdog fallback. Exercise the process race and
interrupted-cleanup paths using owned synthetic Windows processes before another
game. Register enough finite startup exposure for the measured 265.641 s plus
the full worker window and cleanup margin, still within the existing server
ceiling. Do not reuse the consumed grant or treat this unclean world as a
checkpoint. Preserve it and use a separately declared lineage from the last
qualified stopped source only after the relevant lifecycle change.

## Remaining qualification

The original uncertain 755,400-microUSD hold remains under the same $10 total;
there is no model dispatch, settlement, refund or renewed allowance here.
Shared-desktop input remains paused. Keep every prior 500-ms failure, five
effective-file failures, loopback failures and Mineflayer/E9E incompatibility.
Concurrent mutable-writer exclusion, full setup/mutation history, instrumentation
parity, actual isolation, scorer authority and required joint controls remain
separate obligations. A valid resource witness or native point agreement alone
cannot admit a protected score or close M0.
