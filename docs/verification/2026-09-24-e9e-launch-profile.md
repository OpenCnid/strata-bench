# E9E installed launch profile and session resolution

M0.3a.4j is **implemented_unverified** for authentic sealed execution. The new
private profile, sealing validation and fresh-instance resolver work together in
synthetic integration tests. A candidate validates against the actual VERIFIED
E9E inventory. E9E remains VERIFIED, not SEALED; M0 in_progress and G0 fail.

Coverage: F01/F05/F06/F16, N01/N04/N06/N08, C03/C04/C24; partial T01/T02/T13,
G0 item 2. D14, D18/D19, all old failures and M1–M7 remain unchanged.

## Implemented connection

[LaunchProfile/3](../../schemas/v1/operator/E9ELaunchProfile.json) identifies
`forge_client` separately from Mineflayer. The complete Java pin must match the acquisition receipt and PackLock. Both Java executables resolve from
`java/bin/java.exe` inside the selected materialized role. The client software
receipt must match every corresponding inventory file; its classpath/module
order is re-derived from pinned Forge and Minecraft metadata. Both commands,
native bridge module presence, natives directory, server properties, loopback
port, explicit environment and installed Forge server argument bytes are checked
before sealing or launch resolution. No installer is invoked.

The [resolver](../../src/mcbench/pack_forge.py) substitutes only declared role-root
and private bridge-directory slots. Client invocation binds an existing protected
argument file by hash and expected player identity. It checks the complete
canonical quoted argument array, permitting only the three authentication values
in their exact positions. Old installation paths, extra JVM/game arguments,
wrong identity, changed bytes, occupied bridge paths, hardlinks and overlapping
paths reject. Results retain only the argument-file path/hash, never its token.
Existing `/1` and vanilla `/2` semantics remain.

The [seal consumer](../../src/mcbench/provisioning.py) still requires all thirteen
evidence-bound provisioning checks. The [launch consumer](../../src/mcbench/pack_launch.py)
still checks both complete materialized file/directory inventories and the
PackLock/marker. This adds no gameplay choices, model calls or movement script.

This is read-only preflight. Execution still must authenticate/check session
lifetime, protect credentials, hold runtime/argument bytes, bind telemetry and
authority, and enforce owned process lifetime/stop. Empty paths alone are not
isolation or durable invocation admission. The resolver explicitly does not
qualify session authentication, writer custody or campaign admission.

## Executed verification

Windows, retained Python virtual environment; `PYTHONPATH` includes `src`,
`evaluator/src`, `tools`, `tests`; Python uses `-X utf8`.

| Executed selection | Result |
|---|---|
| `pytest tests/test_forge_client.py tests/test_pack_launch.py -q` | 58 pass, 27.46 s |
| `pytest tests/test_provisioning.py tests/test_pack_worker.py tests/test_records.py -q` | 107 pass, 25.14 s |
| `pytest tests/test_pack_forge.py -q` (final) | 29 pass, 47.50 s |

**194 distinct cases pass.** New tests exercise real CAS, seal and two independent
materializations with explicitly synthetic software/auth bytes; no Java starts.
They reject profile drift, stale paths, tampered sessions, body mismatches,
missing bridge modules and missing expert evidence. The initial new suite had
26 fixture-setup errors from omitted nullable FileEntry IDs. Correcting that
yielded 26 pass; the next selection passed 28 before the Java identity case was added. One imported-fixture Ruff F811
finding was resolved with a scoped annotation. Schema export also corrects the
stale RoleInventoryInput export to include the implemented directory field.
Full repository Ruff and `git diff --check` pass.

Private one-use `check.py` validated the candidate against actual inventory
`20cad14f2d8ed7a4675685608e22bfa5e6fdbcb36510c464d6d4d11667fc4c81`
and software receipt
`e139d2465bb84f23b5eae2199f9fc446d944b88db7e290f9f355fffcc962e6c4`.
It rehashed all **3,786 client software files**, compared the relocated template
with the installed argument builder, confirmed acquisition identity and retained
equal snapshots of **all 39 authority tables**. Initial check01 completed in 8.922 s,
but final review found its correct Java hash paired with an inaccurate version
label. The old candidate and source remain sealed. Source now enforces the exact
acquisition/PackLock Java pin. Corrected check02 rejects the old label and passes
with the receipt identity in **11.109 s**.
Candidate profile SHA-256:
`148069295b90f4ee91e470e76cfc4ff449f8505eb558387fbd19dd289a78c3c5`.

Private evidence `2026-09-24-e9e-launch-profile-01` contains 11 files / 117,958
bytes: driver, candidate, authority snapshots, result and source. Complete
EvidenceBundle readback passes. Seal SHA-256:
`4a1d1d8bbe536b0fe16340db4074d548be9eebe741254dc0bf880cbe9de57ede`.
Verification SHA-256:
`82207c1fe1a692374b43e312f8962888eaf577f2301f22f83cd0df308380242e`.
Corrected evidence `2026-09-24-e9e-launch-profile-02` contains 11 files /
119,091 bytes and also passes complete readback. Seal SHA-256:
`73f896e0ce1265a95a0a011d5ce0ae8d213628a467d4d8683a7fc8ad1ba8352a`.
Verification SHA-256:
`e7471c23d61cac926d182012c4b46ff7be4428039bdf59236ea8647d19628744`.
No credentials were prepared, game launched or model called. Exposure stays
**$2.831942/$10**, with every unresolved amount reserved.

## Remaining acceptance

Join retained official acquisition, config-role/legacy dispositions, legal/source
review, update policy, recipe, quest/team and independent-reference evidence into
the thirteen checks bound to this inventory/profile. Then seal/materialize and
connect fresh session, telemetry and process guardian consumers for authentic
execution. Preserve successful cold starts and the LLM/Mineflayer pilot; do not
repeat them unchanged. Remaining scorer, root/helper, recovery and authoritative
clock/save/cost joins continue to prevent aggregate G0 closure.
