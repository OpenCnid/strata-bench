# Native gateway and restricted Dovetail skill reads

September 20, 2026. Operator-only. M0.1c.1c.2b and M0.1c.2b.2g/.2h;
F03/F04/F07/F09/F11/F16, N01/N03/N04/N06, C06/C12/C18/C20/C36,
partial T01/T04/T06/T07/T12 and G0 items 1/6. Implemented but unverified
for production. M0 remains incomplete, G0 fails, G1–G5 are not run.

## Delivered behavior

`native_gateway.py` connects the existing native ingress, participant admission,
finite-exposure reservations, OAuth transport and receipt accounting. Every
actual HTTP request gets a distinct durable operation; the trusted gateway
enrolls broker permissions only after dispatch intent commits. Frozen gateway
limits and pricing/exposure policy are part of native profile identity. The
simulation adapter accepts fabricated credentials and literal owned loopback
only; live mode requires the existing private authorization and qualification.
No allowance is installed or reset by this service.

The service bounds requests, concurrent handlers, body size and read/transport
time. Revocation precedes socket cancellation. The listener keeps its port
until native termination and handler fencing are confirmed; a still-running
native process cannot send its retry credentials to a replacement listener.
Closure seals the exact ingress request/attempt/participant inventory. Unknown
usage keeps its reservation and blocks envelope settlement even after the
gateway closes. A previously registered job cannot reopen this gateway.
Crash recovery still needs an independent process/port fence; this service
does not infer one from a stale database state or replay an ambiguous request.

`native_skills.py` fixes a concrete restricted-profile gap: the native skill
catalog previously pointed at files whose shell read was disabled. Operator
inspection now copies the eight exact pinned Dovetail skill bodies into
immutable broker paths for each admitted participant. The private corpus is
bound to the sealed installed-file hashes and profile. Native discovery and
the two explicit-only invocation rules remain unchanged. Sanitized native
instructions explain the broker paths and unavailable capabilities.
Supporting files, script execution, learned-artifact activation/export and
complete helper lifecycle remain required work; body reads do not satisfy
those contracts.

## Executed verification

- Gateway/OAuth/shared-transport focused tests: **58 passed in 17.08 s**.
- Affected native/ingress/admission/dispatch checks: **102 passed in 8.22 s**.
- Final skill-corpus and gateway checks: **16 passed in 8.57 s**.
- Targeted Ruff passes. Initial gateway tests passed nine cases but had five
  teardown errors when no request had initialized the participant table. Bind
  now initializes admission state even when every client is rejected; the
  subsequent focused runs pass. No game or shutdown threshold changed.

The actual pinned CLI/Dovetail runs below use fabricated OAuth caches,
owned synthetic providers and a synthetic game worker. Both use the real
gateway service and D11 estimate arithmetic. Each makes six admitted, settled
root/helper requests, valued at **42 microUSD of API-equivalent estimates on
synthetic token counts**. These are neither actual charges nor consumption
of the original experimental allowance. Native durations are not shutdown
acceptance measurements.

| Private sample | Actual result |
|---|---|
| `2026-09-20-native-gateway-01` | 22 checks pass; six calls; 26.036 s native duration; seven unauthorized HTTP clients rejected; broker scopes and exact closure pass |
| `2026-09-20-native-skills-broker-01` | Changed profile with real skill projection; 24 checks pass; six calls; 27.778 s; eight immutable bodies per participant and exact prompt-engineering body returned through actual root and helper tool outputs |

Private evidence lives under `C:/Users/Darian/.strata/evidence/`; manifests pin
source/executable bytes and private journals retain accounting. Gateway sample
profile is `bc3fa9cf5f8ff14f720539e2d7984ae70f1d7e0a7b5da0243a206250bad0efd7`,
result SHA-256 `ecdc48f3d5cccf39b33ba63e02d0cc70a6796ee88ca3dc2dc3ece3822d6f645b`.
Skill sample profile is
`7e50bbae402a031c18d030118c582713a28a873b515d9d82bc216a5cde72324f`,
result SHA-256 `4fc4037b091e4f038969a21a115e8c66ea792aefa003e9620bde2341a48e26a7`.
No native-header value-parity claim is made for these new gateway samples;
they observe expected forwarded names, while prior transport evidence and
source tests cover value preservation. All owned native/services terminated.

## Remaining M0 work

Move directly toward the native Dovetail → scoped game action → helper → private
evidence join. The first live conformance entrypoint must distinguish proven
pre-dispatch safeguards from account/TLS/receipt evidence collected during
qualification. The current transport gate asks for account-bound receipt
qualification before a first live call; resolve that bootstrap explicitly,
without manufactured pass artifacts or unreserved traffic. Retain protected
tool/credential boundaries, exact source identity and finite exposure.

The provider-limit reserve is 755400 microUSD per request. A first trial stays
within 1000000 and the existing aggregate 10000000. Concurrent root/helper
reserves and persistent helper envelopes can exceed that first-trial ceiling;
do not silently raise it or invent a smaller bound. A measured initial root
trial, subsequent recorded admission stage and properly fenced helper-envelope
lifecycle need explicit implementation before the complete helper/game join.

Read-only original accounting still has zero experimental operations, one
D11 migration and the original authority. No real OAuth token was copied or
forwarded, no Minecraft/evaluator launched and no shared-desktop input used.
Preserve the earlier loopback, five effective-file, Mineflayer/E9E and 500-ms
shutdown failures, plus scorer/provenance/recovery gaps. This report closes no
acceptance gate.
