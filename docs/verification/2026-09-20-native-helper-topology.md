# Native helper overlap and nested capability evidence

Date: 2026-09-20. Operator-only. Partial M0.1c.2c.2b/.2c,
F03/F07/F11/F16, N01/N03/N04/N06/N08, C06/C14/C18/C20 and T04/T12.
No aggregate test, gate, helper isolation or production billing qualification.

The [native helper probe](../../tools/native_helper_probe.py) and
[topology controller](../../tools/native_helper_topology.py) exercise the actual
pinned CLI against the existing credential-free, separately metered loopback
provider. They use deterministic tool calls and synthetic usage, no live model,
commands, game, desktop input or credential forwarding. The CLI remains
0.154.0-alpha.6.2, SHA256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`;
Dovetail remains `15c306ccfef28eb5f616fadcd5fd8eac0663e361` / 0.4.1.
Every fixture reserves at most 12 requests and 45 seconds within the unchanged
80,000 synthetic microUSD envelope. This does not increase D04's live allowance.

## Overlap and exact rejection

With `agents.max_concurrent_threads_per_session=2`, two clean-context native
children each begin a response stream. The provider holds both streams until
the root obtains `list_agents`; that result lists root and both children as
running. Only then does the fixture release the streams. Both children finish
with the expected result and distinct thread IDs. Eight ingress requests,
eight upstream calls and eight deduplicated settlements reconcile to 80 input,
32 output tokens and 112 synthetic microUSD. The native root JSONL reports
60 input/24 output, excluding the two children.

With the same overlap procedure and limit one, the second spawn returns the
exact native text `collab spawn failed: agent thread limit reached`. No second
child request reaches the gateway. The listing contains only root and the
first running child. Seven requests/settlements reconcile to 70 input/28 output
and 98 synthetic microUSD; the root again reports 60 input/24 output. The
validator requires that exact rejection, complete expected agent sets,
overlapping running states, final results, lineage, request counts and receipt
deduplication. An arbitrary error, timeout or absent usage cannot earn a pass.

These are actual native scheduler observations for this local fixture. They
do not prove atomic production child admission, child-specific sub-budgets,
filesystem/process/network boundaries or simultaneous Minecraft bodies.

## Nested capability failure

The root has six collaboration tools. Each child's first request advertises
only the `functions` namespace, with no collaboration tools. An explicit
`agents.max_depth=2` does not change this observed result. The corrected nested
fixture checks the child's actual catalog before emitting a child spawn/wait;
when absent, it completes authoritative synthetic usage and reports
`NATIVE_NESTED_TOOLS_MISSING`. Four calls settle, but the nested qualification
remains failed/blocked. No grandchild was launched.

Read-only `codex debug models --bundled` confirms the pinned bundled catalog's
`gpt-5.6-luna` entry has `multi_agent_version: v1`. The captured catalog SHA256 is
`186b78811c26053f576b12f6d6adb362fab74a00588e9ac84a6b0177ff7caec4`.
This is configuration evidence, not an immutable model identity or evidence
of the provider's live capabilities. A possible mismatch between forced root
v2 and child model metadata remains an inference, not a verified root cause.

For supporting source review, the current official
[configuration source](https://github.com/openai/codex/blob/5c5308fc9a9ee789049d646ef11e5400384b9c6f/codex-rs/config/src/config_toml.rs)
describes `max_depth` as a v1 setting ignored by v2. The reviewed
[child configuration implementation](https://github.com/openai/codex/blob/5c5308fc9a9ee789049d646ef11e5400384b9c6f/codex-rs/core/src/agent/child_config.rs)
starts from the parent's effective configuration. That upstream revision is
not asserted to be the pinned binary's source revision; neither source text
nor a configuration change establishes nested conformance here. The existing
separately launched native-job depth/budget guard remains a distinct seam.
Complete actual grandchild accounting and enforced depth two remain required.

## Retained samples and checks

All raw artifacts are under external
`C:\Users\Darian\.strata\evidence\2026-09-20-` prefixes below. Each run records
the exact source hashes, native request bodies, tool outputs, lineage, SQLite
ledger, journal and immutable plugin before/after digest.

| Suffix | Actual result |
|---|---|
| `native-helper-pair-01` | Initial positive overlap pass; eight settled calls. |
| `native-helper-pair-02` | Final positive overlap pass with per-agent catalogs and upstream count; eight settled calls. |
| `native-helper-limit-01` | Initial verdict fail pending observation of the exact native denial; seven calls fully settled. No fabricated expected error was accepted. |
| `native-helper-limit-02` | Exact denial/overlap/accounting pass; seven settled calls. |
| `native-helper-grandchild-01` | Failure: initial probe incorrectly assumes the child has the root's tools. Native returns unsupported calls. Fixture result-delivery assertion then leaves four settled/one unknown; sixth ingress is rejected before forwarding. Full 12-call/80,000 synthetic microUSD hold remains. |
| `native-helper-grandchild-02` | Capability failure with explicit max depth two; four authoritative settlements, no provider errors. |
| `native-helper-grandchild-03` | Final capability failure with recorded per-agent catalogs; four authoritative settlements, no provider errors. No grandchild admission. |
| `native-helper-source-01` | Read-only pinned bundled model catalog and supporting upstream source at the stated revision. |

Fresh `native_dispatch_probe.py --recover-only` on `grandchild-01` reports four
settled/one ambiguous attempt, zero replay, unchanged full hold and denied new
admission. The failed sample is neither refunded nor reused. This reopens an
already classified failure; it is not complete session/game restore evidence.

Executed `python -m pytest -q tests/test_native_helper_topology.py
tests/test_native_helper_probe.py tests/test_native.py
tests/test_inference_dispatch.py tests/test_inference_transport.py
tests/test_gameplay_package.py`: **113 passed, zero skips, 8.22 seconds**.
Full Ruff passes. Synthetic verdict negatives include wrong denial, extra
child call, absent overlap, duplicate agent, wrong final result, timeout and
boolean coercion, unknown usage, missing upstream request, mismatched lineage,
unavailable child tools and ancestor-context leakage. The live fixture uses
`--variant v2 --mode concurrency_pair|concurrency_limit|grandchild`, with a
fresh external `--output` and exact `--codex` pin. The last mode correctly exits
nonzero on this pinned profile. It must remain unsuccessful until real nested
capability evidence satisfies its positive contract.

Next: qualify a supported native nested profile or the explicitly separate
Dovetail-compatible helper seam with complete child admission/permissions and
recursive budget lineage. Continue independent authentic guardian/mechanic
work while production monetary/exposure/isolation inputs remain open. G0 is
still fail; G1–G5 are not_run. No model, threshold or required feature changed.
