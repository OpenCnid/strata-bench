# Installed E9E client configuration and cold restart

M0.3a.4h is **verified for the named selected-config profile**. The installed
client resolves its own software paths and captures the same six live Forge
configuration records across two distinct starts. Independent audit **28/28**
and **41 focused source tests** pass. M0 remains in_progress and G0 fail.

Coverage: F01/F05/F16, N01/N04/N06/N08, C03/C04/C24; partial T01/T02/T07/T13,
G0 item 2. M1–M7 and D14 isolation deferral remain unchanged. These operator
checks do not choose gameplay actions. The earlier actual GPT-6 Luna/Mineflayer
[turn/walk result](2026-09-23-support-coordinate-pilot.md) remains distinct.

## Implementation and authentic procedure

[The client resolver](../../src/mcbench/forge_client.py) consumes the retained
`ForgeClientSoftware/1` receipt, verifies installed software bytes and re-derives
classpath/module ordering from the pinned metadata. Its returned arguments use
the prepared role's libraries, assets, native and game directories, credential
placeholders, four processors and a 512/6144-MiB heap. It never authenticates,
launches Java or exposes a gameplay tool. The private caller uses the existing
protected cached-session preparer and retires its credential argument files.

The new client copy exactly matched all **13,628 files / 1,489 directories** in
the retained initial role. All **93 classpath entries and eight module paths**
matched the retained successful launch order. A separate server copy matched
the [normally stopped second initialization](2026-09-24-e9e-cold-start.md);
only its declared loopback port changed from 25603 to 25604. Original role and
stopped-server sources were not used as working instances.

Profile `e9e1270-installed-client-config/1` uses the already prepared client
0.1.0 and telemetry 0.3.2 JARs, sealed Java 17.0.20.1+1 and server telemetry
0.3.13. No module rebuild, installer or software reacquisition occurred.
Existing noninput-desktop ownership and fresh per-client config plans bound
the exports to retained Java process identities. A fresh authenticated server
stream supplies the shared settings and expert furnace recipe. The server
starts within 300 seconds; each client has 420 seconds, server normal drain
120 seconds and the outer server watchdog 1280 seconds. Server, client
software and client mod/script file leases each retain the existing 1 GiB cap.

| Observation | First client | Cold client restart |
|---|---:|---:|
| Capture and owned termination | 158.328 s | 157.063 s |
| Live config records | 6 | 6 |
| Owned processes, all terminal | 8 | 8 |
| Shared-desktop changes / gameplay actions | 0 / 0 | 0 / 0 |

The complete paired observation took **489.203 seconds**. All three server
processes stopped normally; its authenticated stream ends at **6,623 ticks**.
Each client was deliberately terminated through its owned Job after capture.
That is a cold process restart, **not** a clean-client-save or D13 emergency
shutdown qualification. No Java process remained after the run.

Both captures exactly match each other and the earlier authentic six-role
capture: `bhmenu-client.toml` and `nomoreworldsettings-client.toml` register as
CLIENT; `inventorysorter-server.toml` and `sophisticatedcore-server.toml` remain
unregistered. Sophisticated Core COMMON and Create SERVER snapshots match the
new signed server observations, including all 145 COMMON entries, current
Create values 8/400/10 and the absent legacy keys. This does not establish
legacy-key equivalence or erase any of the five historical file findings.

## Retained differences and failures

The first attempt rejected the combined file lease with `BOOTSTRAP_QUOTA`
before Java or authentication. Its output and one-use marker remain sealed.
A fresh scope used three separately bounded leases and the untouched prepared
instances. No quota was raised and the failed scope was not replayed.

Among **7,123 client config paths**, only
`config/byg/backups/last_working_configs_backup.zip` differs between starts.
The selected CLIENT/COMMON files are byte-stable. Preserve the differing ZIP
hashes: the earlier server ZIP timestamp analysis does not by itself establish
the cause of this client difference. Full client config byte equality is not
claimed, and no broad config exclusion was introduced.

Final private inventories retain every file hash/directory and changed bytes:

- Client: **13,638 files**, **142 new/changed files / 6,399,853 bytes**, 38 removals.
  Removals comprise the same 29 generated Emendatus Enigmatica biome files and
  nine publisher-supplied Crash Assistant transient files. New runtime helper,
  log and generated data remain explicit candidates for final disposition.
- Server: **8,923 files**, **53 new/changed files / 39,141,303 bytes**, no removals
  relative to the retained stopped server. Its played world is private evidence,
  not a new initial template.

All **39 authority tables are unchanged**. E9E stays ACQUIRED; exposure stays
**$2.831942/$10**, with the old hold and full unresolved envelopes reserved.
No model requests, inference charges, player actions or shared-desktop input
were introduced.

## Verification and evidence pins

```text
python -X utf8 -m pytest tests/test_forge_client.py tests/test_client_configs.py -q
# 41 passed in 10.60 seconds
ruff check .
git diff --check
# pass
```

The first source run retained 40 passes/one failure: the new resolver used the
Forge mapping version as the vanilla metadata directory. It was corrected to
`versions/1.19.2/1.19.2.json` before any launch. Synthetic source cases cover
path resolution/order, credential placeholders, changed/missing bytes, duplicate
or escaping entries, absent native directory, invalid port and metadata drift.
They do not substitute for the actual two client boots.

Both bounded private bundles pass complete `EvidenceBundle` readback:

| Private bundle | Files / bytes | Seal SHA-256 |
|---|---|---|
| `2026-09-24-e9e-client-effective-01` — pre-launch refusal | 31 / 15,905,354 | `910be8e3ed1dcd39afc107c1ed12a89f03bf8241e30f239dd9ae1f3aa616ef89` |
| `2026-09-24-e9e-client-effective-02` — changed profile | 274 / 87,723,240 | `7dd2c308fcf89d8e1ba7a6e37876bd0a9224f15d6e8c6fff4ffcd8dcab978ed6` |

Independent audit SHA-256:
`7b9e8b5fc0ac176d801f8d365fc0a1dc5d55aa65d678b19a253689d153cd6c5f`.
Exact executed source, argument templates, process/desktop records, signed
server stream, client snapshots, full inventories, changed bytes, authority
snapshots and retained failure are private. No credentials/game binaries enter Git.

Next join this client evidence, the server cold-start evidence and existing
role/getter controls into final E9E effective-role inventory/profile admission.
Explicitly disposition generated/removal/helper/backup paths; keep all five
historical findings and the new client ZIP difference. Do not repeat these
successful client starts or the model pilot unchanged. Remaining helper,
scorer, recovery and authoritative clock/save/cost joins still prevent G0 closure.
