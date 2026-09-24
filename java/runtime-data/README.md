# Fixed E9E runtime data

Operator-only harness addition for the installed Cable Facades 1.2.2 and
Immersive Engineering 9.2.4-170 consumers. Their startup downloads affect block
cover rules and special-revolver registries; hashing installation files does not
freeze those remote inputs.

`tools/prepare_runtime_data.py` compiles these three Java sources with JDK 17 and
packages three previously acquired, commit-addressed publisher files. The
preparation receipt pins source/compiler/resource/class/JAR bytes. It does not
install the result, fetch network content or qualify a complete pack.

The Java agent checks its resource index before game startup, then changes one
URL constant in each exact hash-pinned class as it loads. Original vendor JARs,
including signatures, remain unchanged. No instructions, parser logic or rule
values are rewritten. A class mismatch terminates the owned JVM with exit 126;
throwing a transformer exception alone would allow the original downloader to
run. The custom `stratafixed` protocol returns HTTP-shaped responses from verified
memory for exactly three routes. It has no network fallback. Other protocols
retain their ordinary JDK behavior. This does not establish network isolation or
prove that every other mod's runtime input has been frozen.

Private `LaunchProfile/4` binds the same snapshot JAR in both role inventories and
injects its exact role-relative Java agent argument. `/3` rejects installations
containing either known remote-data consumer without this binding. A new
snapshot is a changed profile; it cannot retroactively recover historical
download bytes or inherit qualification from an old profile.

JVM fixtures test delivery with all network connections denied, strict routes,
resource corruption and fail-closed class drift. The bounded cold-start `/2`
consumer also requires both class-binding records and all three actual read
records. Agent startup alone cannot pass that check. Authentic Forge loading,
client/server conformance, unchanged mechanics, owned shutdown and all remaining
provisioning checks retain their separate evidence requirements.
