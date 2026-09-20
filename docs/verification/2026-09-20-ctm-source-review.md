# Exact CTM startup failure and bounded executor diagnostic

2026-09-20. Operator-only. B10 / M0.3b.2c.3c.2a.1; supports diagnosis,
not a startup, concurrency-correctness or gameplay gate pass.

The [new native fault trial](2026-09-20-settings-crash-startup.md) and earlier
quest trial fail with the same CTM metadata-cache signature. Read-only `javap`
of installed CTM SHA256
`4a44e793ec6fb015dbfc02258b6bdb14151e1c42e9968990f1b322b864d381cd`
confirms a static plain HashMap with unsynchronized contains/get/put/clear.
The failing negative-cache lambda inserts null. A replacement must preserve that
distinction between absent entries and cached missing metadata; merely changing
map implementations without checking null semantics is not a qualified repair.

The pinned upstream [ResourceUtil](https://github.com/Chisel-Team/ConnectedTexturesMod/blob/401c21b6f10bfc576403d1fbc1d0cbd4db9b2163/src/main/java/team/chisel/ctm/client/util/ResourceUtil.java)
and [TextureMetadataHandler](https://github.com/Chisel-Team/ConnectedTexturesMod/blob/401c21b6f10bfc576403d1fbc1d0cbd4db9b2163/src/main/java/team/chisel/ctm/client/util/TextureMetadataHandler.java)
have matching cache operations and texture-stitch call sites at lines 64 and 54.
This revision precedes the installed artifact's build timestamp. It is supporting
source evidence, not a verified exact upstream build revision. The later branch
head changes texture APIs and is not treated as this installed source. Upstream
[issue #176](https://github.com/Chisel-Team/ConnectedTexturesMod/issues/176)
describes the same concurrency failure. An exact failing interleaving was not
captured in Strata; the cache-race explanation remains a supported diagnosis.

Both the mapped build input and exact installed Minecraft SRG runtime bytecode
read `max.bg.threads`, accept integer 1–255, and use it as the upper clamp for
ForkJoinPool target parallelism in separate Bootstrap and Main executors.
The exact runtime JAR SHA256 is
`844f5333e261c3bf6a4b99c9fa3872e7beb913d087d0d759c08b3a6d236e0179`.
The I/O executor is separate. Target parallelism does not prove a fixed total
thread count or serialization of every CTM access: the pool may compensate for
blocked tasks. [Java 17 ForkJoinPool contract](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ForkJoinPool.html).

The fresh `ctm-startup-bg1-diagnostic/1` profile therefore records an explicit
`-Dmax.bg.threads=1` hypothesis test. No mod is removed/replaced; the settings
crash candidate and other inputs stay pinned. Existing 280-second readiness,
480-second lifetime and five-second API bounds remain. All six planned cases
are separately bounded; only dependency-qualified cases may launch. Keep its
results separate from the original failed profile and preserve both samples.
A successful boot or settings recovery cannot close CTM reliability by itself.

This flag is pinned by each exact private argument template and execution plan.
The native settings fingerprint alone covers loaded mod artifacts/Java/OS and
does not distinguish all JVM argument choices. Admission must also match the
complete provisioned execution profile; never use the fingerprint alone to pool
these conditions. No campaign is admitted by this diagnostic.

Source files, both runtime disassemblies, upstream metadata and their hashes stay
outside the repository under
`C:\Users\Darian\.strata\evidence\2026-09-20-ctm-startup-review-01`.
The original failed native sample is immutable under settings-crash-native-01;
the new diagnostic plans/results use a distinct settings-crash-native-02 root.
No live inference expenditure or shared-desktop input is involved. B10 and all
full startup/reliability gates remain open pending authoritative qualification.
