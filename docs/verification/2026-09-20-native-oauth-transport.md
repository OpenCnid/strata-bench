# Native OAuth transport candidate

September 20, 2026. Operator-only. M0.1c.2b.2f is **implemented_unverified**.
This is source and actual pinned-CLI evidence with fabricated authentication,
local synthetic providers and a synthetic game worker. No real OAuth model
request, credential refresh, HTTPS exchange with OpenAI or Minecraft run occurred.
M0 remains incomplete, G0 fails and G1–G5 are not run.

Coverage: F03/F04/F07/F11/F16, N01/N03/N04/N06, C06/C12/C20/C36;
partial T01/T04/T06/T07/T12 and G0 items 1/6. It advances the protected upstream
dependency identified by [native ingress](2026-09-20-native-ingress.md), preserving
the completed accounting matrix and its unresolved live evidence requirements.

## Implemented behavior

[native_oauth.py](../../src/mcbench/native_oauth.py) introduces
`native-chatgpt-fixed-https-responses/1`. The trusted native runtime owns login
and refresh; this adapter contains neither a replacement login client nor an
auth-cache parser. Its short-lived private request object captures native bearer
and account headers only after job/profile/route authentication, and binds them
to one operation and body digest. It rejects API-key mode, absent/duplicate
account headers, unsupported headers, malformed/control/oversized metadata and
credential values smuggled into ordinary protocol headers. Its representation
is redacted; references are dropped on completion. Python strings are not claimed
to be zeroized or protected from arbitrary same-user process inspection.

An explicit bounded allowlist preserves the eleven observed native protocol
headers, including session/helper metadata, beta features and Responses-lite
selection. Ingress capability, Host and arbitrary client headers do not reach
the upstream. Native metadata is preserved without being copied into gameplay
feedback or the accounting journal. The native runtime's private credential
cache remains outside the gameplay workspace; its protection still depends on
the qualified tool/bootstrap/process boundary.

The production adapter constructs a verified HTTPS connection to `chatgpt.com:443`
with fixed `/backend-api/codex/responses` and `/responses/compact` paths. It does
not accept a caller-selected URL, consult HTTP proxy environment variables,
follow redirects or retry internally. The base is supported by embedded strings
in the pinned binary; Responses route suffixes are observed in the native local
provider. **That is an implementation inference, not live endpoint qualification.**

Before dispatch, production requires expiring private qualification and individual
private check artifacts bound to the policy, exact profile and account digest.
Synthetic check artifacts cannot satisfy it. No qualification was issued here.
The normal original-authority, native participant, finite exposure and durable
per-call reservation gates still apply. Every distinct retry remains a separate
admission; ambiguous or missing usage retains its reservation without replay.

[inference_transport.py](../../src/mcbench/inference_transport.py) now shares the
existing bounded parser, capture and settlement implementation between adapters.
The original credential-free adapter still rejects live stores. A separate
`SyntheticOAuthTransport` requires a permanently simulated store, literal owned
loopback endpoint and a specifically marked fabricated token/account. It cannot
be selected as a live fallback. Live valuations use provider-reported token
evidence; fixture valuations remain explicitly synthetic.

The OAuth adapter buffers a response suffix to detect literal token/account
reflections across network chunks before those bytes reach native output or CAS.
Only status/content type are returned as response headers. Reflection, redirect,
timeout, truncation and missing receipts leave unresolved holds. This is a
literal-reflection defense, not a claim about malicious encodings or every
possible provider response path.

## Source and native verification

The saved exact CLI schema and [official authentication documentation](https://learn.chatgpt.com/docs/auth)
support native ChatGPT authentication with `requires_openai_auth=true` for custom
providers and private file-backed auth caches. The [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
distinguishes the credential store and provider configuration. Existing account
cache field names/types were inspected without printing values, copying tokens
or invoking authentication. The probes create fresh fabricated caches instead.

```text
python -m pytest -q tests/test_native_oauth.py tests/test_inference_transport.py tests/test_native_ingress.py tests/test_inference_dispatch.py tests/test_estimated_accounting.py --tb=short
python -m pytest -q tests/test_native_oauth.py --tb=short
python -m ruff check src/mcbench/native_oauth.py src/mcbench/inference_transport.py tests/test_native_oauth.py tools/native_dispatch_probe.py tools/native_mcp_identity_probe.py
python tools/native_mcp_identity_probe.py --codex '<pinned codex.exe>' --output '<fresh private directory>' --broker --admission --bootstrap --ingress --oauth
```

The affected suite passed **106 tests in 11.77 s**. After protocol-header and
private-proof and media-negotiation guards were added, the final OAuth file passed **19 tests in
5.96 s**. Targeted Ruff and whitespace checks pass. Source cases cover one
forward per intent, retained unknown costs, wrong request/profile/account,
redirect refusal, split credential reflection, forbidden real-token fixture use,
metadata bounds, private evidence scope/expiry/synthetic rejection, fixed TLS
hostname and certificate verification. The TLS construction test opens no socket.

Actual pinned CLI `0.154.0-alpha.6.2`, binary SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`,
Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361`. Private evidence:

| Sample | Observed result |
|---|---|
| `2026-09-20-native-oauth-01` | Pass for initial credential path: six root/helper requests, 84 synthetic fixture units, all 20 recorded checks, 28.936 s native process. Revealed native protocol headers that the initial adapter did not preserve; this sample cannot establish that preservation. |
| `2026-09-20-native-oauth-02` | Pass after the header-policy change: seven requests, 98 fixture units, all 21 checks, 31.320 s native process. The owned upstream independently compares every allowed native header value with its ingress value. |

Both samples preserve scoped game/helper positive and negative controls, reject
seven unauthorized ingress clients before body capture/reservation, settle each
request once, and close participant/job envelopes to `FINALIZED`. Access token,
refresh token, ID token and ingress capability are absent from captured request
bodies, tool feedback, decoded native stdout/stderr and exported journal. The adapter has no refresh/ID-token cache access and forwards no dedicated
refresh/ID-token headers. These are observations of fabricated
credentials and local protocol behavior, not real-account or complete T06 proof.

Sample 01 profile:
`532e49f0e3a9071cbf59fce655140c6d5ce9005178c1b142c65094049124bd04`;
result SHA-256:
`10713dd050eb64a941f47dc26a10669996224f49495bcccbc0d9ddbaeb18cb42`.
Sample 02 profile:
`54ab98c5cd8beb1039cd82257f02a633ff188902d8cbb7e307e2c936b312212d`;
result SHA-256:
`c98ce10eb44c318212ba81810b9502b6499fec66f17032eb42a592bb3cc831b3`.

The final production-only check-artifact/expiry guards and preservation/validation
of native Accept and JSON Content-Type were added after sample 02 and tested
locally. The media-negotiation change has source evidence only; no subsequent
native execution is claimed. Sample 01 also
predates the transport module's explanatory docstring update. Preserve each
sample's source manifest; do not label either as execution of later guards.

## Current state and next action

Two samples total **182 synthetic fixture units**, zero real experimental-model
operations. Read-only original accounting remains schema 2, one migration,
10,000,000 micro-USD total estimate allowance and 1,000,000 first-trial ceiling.
No allowance was installed/reset. Owned services are terminal; no game launch,
evaluator exposure or shared-desktop input occurred. Fetched origin/main remains
the merged `542a77ac760fb305b26941085e33447f392f8ba8` checkpoint.

Next wire the production inference gateway/lifetime and private qualification
artifacts around this adapter; it is currently exercised through the synthetic
probe service. Finish actual Dovetail skill-body/learned-artifact integration and
helper lifecycle, and qualify real TLS/account/receipt/exposure plus the applicable
game/runtime prerequisites before the staged <=$1 trial. Retain all old loopback,
effective-file, 500-ms shutdown, Mineflayer/E9E and scorer/provenance/recovery gaps.
