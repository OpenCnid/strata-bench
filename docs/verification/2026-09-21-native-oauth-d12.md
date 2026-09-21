# D12: one distinct bounded OAuth receipt trial

September 21, 2026. M0.1c.1c.2b.3; F03/F11/F16, N01/N02/N04/N06;
partial T01/T04/T07/T12. M0 incomplete, G0 fail, G1–G5 not_run.

The user explicitly approved “Retain the hold and allow one bounded trial”
for one new request capped at $0.7554 while retaining the first request's
$0.7554 reservation. SPEC v0.2.99 §15 records the exception. The original
$10 authority is unchanged; maximum combined exposure is $1.5108.

`metering_trial.py` installs one private, expiring decision bound to the original
authorization, accounting snapshot, retained uncertain rows, native profile,
Luna estimate basis and exact request-only job. Envelope and sole request
consume the exception inside the ordinary reservation transaction. Aggregate
limits remain enforced; changed holds, new uncertainty, helpers, other jobs,
expiry and second requests fail closed. Restart cannot rearm it. Default
unknown-metering admission remains blocked everywhere else.

The receipt runner now uses the sealed no-patch catalog and previously reviewed
root/helper tool projections. Transfer checks pin source bytes, normalized
configuration, exact tool digests and native identity. The target removes the
game grant and permits no helper. Only the new request may be settled from its
own authoritative receipt; the old hold cannot be released by this trial.

Focused verification: 37 accounting/envelope/clock tests passed (1.71 s);
59 dispatch/gateway/conformance tests passed (21.70 s); final one-use policy
and conformance checks passed 36 tests (13.32 s), with Ruff clean. Initial
Windows fixture path errors were fixed before these successful checks.

The changed actual pinned CLI/local synthetic-provider preflight passed all
58 checks in 91.547 s. Eleven distinct fabricated requests settled and finalized;
77 API-estimate micro-units derive solely from synthetic token evidence.
This is no actual OAuth charge or experimental subscription usage. It verifies
the changed native/tool/gateway profile narrowly; previous raw sibling/loopback
failures and full runtime isolation remain unresolved.

Immediately before live preparation the original store was backed up privately
and checked read-only: unchanged authorization digest
`7aca7758f12eb1089f481d5d4bc19de2c6022cf1167b03056c32d41c3e4a819a`,
755400 microUSD reserved once, uncertainty true. Private evidence directories
are `2026-09-21-native-oauth-d12-preflight-01`, `...-audit-01` and
`...-live-01`; credentials, raw requests and runtime profiles stay private.

The one new live request returned HTTP 200 with a media type recorded as
`other`. Its 55,171-byte private capture contains a complete Luna SSE response,
but the then-current parser rejected the media type and unrecognized native
usage fields. Native exit is 1; the initial result is preserved as failed and
UNSETTLED. No second request was made.

`native_usage.py` now checks the observed explicit cache writes, item/content
attribution and exact all-zero image/search usage shape. Unknown/nonzero hosted
usage still rejects. The capture independently parses to 8,830 input tokens,
1,792 cached input, zero cache writes, 12 output and zero reasoning tokens.
Pinned D11 arithmetic yields **1,458 microUSD ($0.001458 API-equivalent)**,
not an OAuth invoice.

`receipt_recovery.py` binds that exact private capture to the stopped request,
HTTP event and closed gateway/ingress seal. A private store-copy rehearsal
preceded durable reconciliation. The new request settled once and its envelope
closed; duplicate reconciliation makes no additional posting. The original
operation rows remain byte-equivalent to their before snapshot. Current total
committed/reserved exposure is **756,858 microUSD ($0.756858)**: the original
$0.7554 unknown hold plus the new measured estimate. D12 is consumed; general
admission remains blocked by the original hold. Recovery proof:
`cas:sha256:aebadd0eb8c0212ad33e1f1eb517a14d76665db726cf90b868f2412298f04425`.
The original failed native result is unchanged; budget FINALIZED does not mean
successful reply delivery. Provider latency is unavailable; recovery explicitly
labels wall time as the observed native lifetime upper bound.

Transport candidate `/2` now withholds unsupported-media HTTP 200 bodies until
the entire bounded SSE response has passed strict usage/scope/framing checks,
then supplies the native runtime with an SSE media type. It never delivers
HTML, error status, partial frames or missing/wrong-model usage. Existing TLS,
credential filtering, limits and no-replay rules remain. Supported media still
streams normally. This changed transport has source/local-HTTP evidence, not a
fresh authentic native/OAuth pass; the original unknown media value was not
retained, so its exact MIME cause is unresolved.

Receipt/parser/accounting suite: 61 pass in 7.82 s. Changed transport/recovery/
gateway/conformance suite: 106 pass and one new fixture construction error;
after correcting the duplicate model keyword, all six targeted media cases
pass in 3.83 s. Ruff and whitespace checks pass. There was no live request
during these fixes or offline reconciliation, and no game/desktop input.

The connected real-game smoke and recovered authentic receipt are separate
pieces of M0 evidence. A live native/game run, full runtime qualification,
scorer/provenance/recovery and retained shutdown/configuration/E9E failures
still prevent M0/G0 closure. No additional model dispatch is authorized by
this consumed exception.

Private bundle seals (SHA-256 of each `seal.json`):

- Preflight: `fe3a15d7dcec760d0468bf2f5e201c9b8c6711657cce453c3d1fb9d1e3f37490`.
- Original live result: `15149f096ef318ebf0d825e08787ff96c424da884bcd90b8634bdf2ffa0cca4b`.
- Before/after stores, preserved rows and reconciliation: `3576a2b84382e538482c2f0d9fc91a8c4a75cae7cf6df07d7c4c5b2627373cf5`.

Executed focused commands use repository Python with `PYTHONPATH=src;tests;tools`:
`pytest -q tests/test_receipt_recovery.py tests/test_inference_transport.py tests/test_estimated_accounting.py`;
`pytest -q tests/test_receipt_recovery.py tests/test_native_oauth.py tests/test_inference_transport.py tests/test_native_gateway.py tests/test_native_conformance.py`;
then `pytest -q tests/test_native_oauth.py -k unknown_media` after the fixture correction.
Final budget/worker boundary check: `pytest -q tests/test_metering_trial.py tests/test_budget_envelopes.py tests/test_budget_clocks.py tests/test_native_worker.py` — 24 pass in 1.36 s. No owned Python/Java process remained at the final process check.
