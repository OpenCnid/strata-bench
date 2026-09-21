# Native participant and budget admission

September 20, 2026. Operator-only. Source and synthetic integration evidence;
no production qualification or release gate closes.

Coverage: M0.1c.2b.2c with M0.1c.1c.2b and M0.1c.2c.2;
F03/F04/F07/F11/F16, N01/N03/N04/N06, C06/C12/C20/C36,
partial T01/T04/T06/T07/T12, G0 items 1 and 6.

## Implementation

[NativeAdmission](../../src/mcbench/native_admission.py) binds each exact request
and reservation to a running native job, the frozen profile and the root thread
observed independently in native stdout. Only the trusted inference ingress may
call it. Request headers on a public socket are not authentication; protected
ingress/bootstrap remains an explicit qualification dependency.

Initial helpers require an already admitted parent, depth at most two, an
available helper slot, a finite child envelope and the pinned clean request
shape: native developer/tool projections, one restricted environment message
and one addressed task. Inherited user/assistant history, previous response
references, additional task parts and environment smuggling are rejected before
child reservation or upstream forwarding. Native instruction/tool projection
integrity is a separate bootstrap requirement. Subsequent requests preserve
participant identity and lineage. Revocation flows to descendants and never
refunds their consumption or reservations.

[Dispatch](../../src/mcbench/inference_dispatch.py) requires the durable admission
and exact reservation digest before posting per-call intent. Broker enrollment
then requires that intent in DISPATCHING state. [Broker](../../src/mcbench/broker.py)
checks running job, participant, profile, open budget envelope, uncertainty and
exposure quarantine on use. Historical example grants are accepted only in
explicit simulation stores. Expiry cannot exceed the native job deadline;
re-enrollment cannot reset revocation or tool quota.

Each helper envelope is a child of its parent's envelope. Per-call consumption
remains separate and is counted once by the existing accounting engine. After
the process tree and ingress are fenced, [native closure](../../src/mcbench/native.py)
requires the exact request and participant inventories and every settled call.
It closes helper envelopes deepest first and then the root in one transaction.
An unknown request prevents closure. Helper slot reuse/early terminal release
requires further authoritative lifecycle integration; this implementation holds
capacity until revocation or terminal job closure and does not invent a helper
completion receipt.

## Focused source verification

Executed with repository `src` on PYTHONPATH and the existing Python 3.12 runtime:

```text
python -m pytest -q tests/test_native_admission.py tests/test_native_broker.py tests/test_inference_dispatch.py tests/test_native.py --tb=short
102 passed in 10.04s
```

Targeted Ruff and `git diff --check` pass. The new admission cases cover clean
root/child/grandchild enrollment, rejected inherited/smuggled contexts, missing
native identity/budget, depth/capacity, envelope exhaustion, immutable admission,
deadline expiry, ancestor/job/broker revocation, restart and retained unknowns,
exact terminal seals, no double counting and forbidden live example grants.
The initial new test fixture had missing/mismatched usage fields (19 setup
errors); the fixture was corrected before behavior verification. Earlier 77,
22 and 100-test runs are preliminary checks, not additional acceptance scope.

## Actual pinned CLI with local synthetic services

The existing identity/broker fixture gained `--admission` and
`--inherited-helper`; its existing dispatch/transport implementation was reused.
Native CLI `0.154.0-alpha.6.2` SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`,
Dovetail commit `15c306ccfef28eb5f616fadcd5fd8eac0663e361`, Windows,
native tool policy `native-stdio-projected-artifacts-executor-game/1`.
Every output directory contains source fingerprints, private SQLite/CAS/journal,
raw provider requests and structured result evidence.

```text
python tools/native_mcp_identity_probe.py --codex '<pinned codex.exe>' --output '<fresh private directory>' --broker --admission
python tools/native_mcp_identity_probe.py --codex '<pinned codex.exe>' --output '<fresh private directory>' --broker --admission --inherited-helper
```

| Private evidence suffix under `.strata/evidence/` | Result and scope |
|---|---|
| `2026-09-20-native-admission-01` | Pass: six admitted/settled calls, root and clean helper in distinct envelopes, executor worker once, helper result scoped, forbidden calls denied, all envelopes/participants closed; 60 input + 24 output = 84 synthetic fixture units. |
| `2026-09-20-native-admission-inherited-01` | Retained failed fixture: ephemeral native storage cannot produce a full-history child (`collab spawn failed: no thread with id`). Four root calls settle to 56 fixture units. This did not exercise ingress rejection. |
| `2026-09-20-native-admission-inherited-02` | Pass after declaring `private_profile` storage: five ingress requests, only four root requests forwarded/settled, inherited child explicitly rejected with `HELPER_CONTEXT_INHERITED`. No child envelope, grant, artifact or game action. Root closure retains 56 fixture units. |

Result SHA-256, in the same order:

```text
54f1f64438498a9b8d127624d4374a68bd876743158121ac6db37ac6365b7af9
cc998e543fcc131b97a617126505316d8cc185e5484464d49412a7f030f457bb
9f0aacfbc992039a17ce02e23eee0b32130e505e4db1225f3d9195ffc3cbb4ab
```

The passing clean profile digest is
`7698105bf7816fea8e58b973a318fad5203ad2cdcd39bd37fa0277cbb58fe89a`;
the passing inherited-context negative profile is
`54fa90b8863264ba8ba5db833b2ec7dcb02be21572fa94518ea1ce21a0e13310`.
Profile locations/configuration/storage differ; these are separately recorded
profiles. Final deadline and exposure-quarantine tightening has focused source
verification; no unchanged native fixture was rerun merely for that assertion.

## Limits and continuation

All 14 forwarded calls across the three samples used deterministic local
providers: 196 synthetic fixture units, no OAuth inference or actual model
charge. Fresh read-only inspection of the original project store found schema-2
authorization and zero experimental operations; its original allowance was not
reset. No Minecraft, shared-desktop input or private evaluator was launched.
The owned Python/service processes are terminal.

Next: bind protected broker/interpreter/plugin/configuration source and launch
integrity, qualify ingress identity/credential separation, finish actual
Dovetail skill bodies and learned-artifact activation/export, helper lifecycle,
then actual OAuth exposure/receipts and the staged trial of at most $1 within
the original $10. Do not substitute these synthetic services for that evidence.
Earlier loopback failures, 500-ms shutdown failures, five effective-file
failures, Mineflayer/E9E incompatibility and scorer/provenance/recovery gaps
remain. M0 is in progress, G0 fails, and G1–G5 are not run.
