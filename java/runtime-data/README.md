# Fixed E9E runtime data

Operator-only harness addition for the installed Cable Facades 1.2.2 and
Immersive Engineering 9.2.4-170, Ars Nouveau 3.23.0 and Supplementaries 2.4.20
consumers. Their startup downloads affect block-cover rules, special-revolver
registries, named spawned entities and globe/statue variants; hashing installation
files does not freeze those remote inputs.

`tools/prepare_runtime_data.py` compiles these three Java sources with JDK 17 and
packages five previously acquired, commit-addressed publisher files. The
preparation receipt pins source/compiler/resource/class/JAR bytes. It does not
install the result, fetch network content or qualify a complete pack.

The Java agent checks its resource index before game startup, then changes one
URL constant in each exact hash-pinned class as it loads. Original vendor JARs,
including signatures, remain unchanged. No instructions, parser logic or rule
values are rewritten. Cable Facades admits its raw vendor hash and the reviewed
post-Forge hash: the installed EventBus 6.0.3 transformer makes its annotated
`onLoad` callback public, changing only byte 8925 from 8 to 9. Exact offline
reproduction matches the authentic captured class. Cold-start evidence requires
the post-Forge binding, not just an offline raw-class patch. Other differences
remain refused. A class mismatch terminates the owned JVM with exit 126;
throwing a transformer exception alone would allow the original downloader to
run. For each named target, refusal additionally retains its hash and base64
class bytes in the private startup log when the class is at most 64 KiB. Larger
classes still halt without a byte capture. Captured bytes are diagnostic evidence,
never automatic admission or a replacement for the reviewed vendor pin.
Every startup also creates a fresh `logs/strata-fixed-<pid>-<uuid>.log` in the
operator-owned game instance, so early records survive clients without console
handles. Writes are serialized and forced to disk, bounded to 32 records,
128 KiB per record and 1 MiB per journal. An invalid log path, write failure or
exhausted journal refuses startup or halts the owned JVM; files are never reused.
These records contain only the existing resource/class hashes and bounded class
diagnostics. They are not signed scoring evidence or isolation qualification.
The custom `stratafixed` protocol returns HTTP-shaped responses from verified
memory for exactly five routes. It has no network fallback. Other protocols
retain their ordinary JDK behavior. This does not establish network isolation or
prove that every other mod's runtime input has been frozen.

Private `LaunchProfile/4` binds the same snapshot JAR in both role inventories and
injects its exact role-relative Java agent argument. `/3` rejects installations
containing a known remote-data consumer without this binding. Snapshot `/2`
adds the Ars Nouveau and Supplementaries inputs. Historical `/1` receipts remain
readable, but cannot admit an installed role containing either added consumer. A new
snapshot is a changed profile; it cannot retroactively recover historical
download bytes or inherit qualification from an old profile.

JVM fixtures test delivery with all network connections denied, strict routes,
resource corruption and fail-closed class drift. The bounded cold-start `/2`
consumer requires all class-binding and actual-read records for the declared
snapshot version (four classes/five bodies for `/2`). Agent startup alone cannot pass that check. Authentic Forge loading,
client/server conformance, unchanged mechanics, owned shutdown and all remaining
provisioning checks retain their separate evidence requirements.

`mcbench.runtime_data.inspect_runtime_data_journal` checks the stopped process's
PID in the filename, journal bounds, complete records and exact expected marker
set. The caller must separately hold the snapshot JAR, bind the real process and
archive the stopped output; a matching text file alone cannot qualify a run.
