# Private player NBT codec

`PlayerNbt` binds the inspected official Minecraft 1.19.2 methods without a
compile-time game dependency. It invokes `Entity.saveWithoutId` virtually on an
exact `ServerPlayer` and writes the resulting complete compound using `NbtIo`.
It checks the owning server's actual `isSameThread` predicate and expected UUID
before and after serialization, then checks the serialized UUID. It does not
filter fields, add defaults, load state, or publish gameplay observations.

The 16 MiB limit bounds uncompressed output. It does not bound the game's
temporary object allocations or serialization time. The owned process deadline
and resource boundary remain necessary. Exceptions invalidate the capture; no
partial bytes are returned. Raw output must stay in private evaluator storage.

The codec deliberately supplies no agent, callback registration or launch path.
Before integration, the owner must pin and authenticate the actual loaded game
and codec bytes, server process, callback point, sequence, tick and roster. A
classloader resolving the expected names is not sufficient authentication.

Save-format NBT is not all transient live state. The real serializer also does
not add the saved file's `DataVersion` wrapper. Preserve those distinctions in
comparisons; do not silently discard mismatches. Matching this compound alone
cannot establish all-N readiness, equal clocks/tools or full T11/G1 acceptance.
Actual callback capture, overhead and side-effect checks remain unverified.

The installed NBT reader normalizes floating-point negative zero to positive
zero. A retained first conformance failure discovered this; a dedicated test
records it. Numeric equality alone must not be used to assert bit preservation
or to hide differing raw evidence. The codec writes the compound it receives
without adding its own normalization.

## Distinct callback observer

`player_body_agent.prepare_player_body_agent` builds `BodyAgent`, `BodyObserver`,
`RosterCapture` and the codec with the pinned JDK17/ASM inputs. It does not launch
Minecraft. The resulting private agent has its own hash/profile and must not be
combined with the old clock agent or silently inserted into an old PackLock.

The operator-only properties file contains exactly `campaign_id`, `epoch`,
`run_id`, comma-separated canonical UUID `roster`, absolute `server_jar`, and a
fresh absolute `output` directory. The owner must retain path/runtime/configuration
custody and expose none of these to gameplay. Java path checks alone do not
establish Windows reparse/ACL isolation. The JVM must disable attach and have
exactly one Java agent, without other native or bootstrap agents.

The agent pins the complete official implementation JAR. Every loaded class
listed in that JAR must have the expected code-source path and bytes, with one
game loader and no duplicate definition. Two exact classes receive hooks in
`MinecraftServer.runServer`, `tickServer`, `stopServer`, and
`ServerPlayer.doTick`. Expanded frames retain the receiver even at dead-local
returns. Callbacks verify their actual immediate game caller class, method,
descriptor, loader and receiver; forged calls halt the JVM with exit 126.

The first server tick containing the entire declared roster creates one capture.
Partial rosters are never accumulated across ticks. Before capture, duplicate or
foreign UUIDs, changed player objects, wrong thread/server, invalid order, or an
incomplete stop poison the attempt. After capture, player objects are released
and ordinary respawn cannot trigger recapture or become a body-identity fault.
The observer is an initial-state witness, not ongoing roster admission authority.

Only complete per-player compounds are returned by the codec. Private files are
created once and forced to disk, followed by a capture journal record containing
the tick, capture-start time and each byte count/hash. Failed partial output has
no committed capture record and must be retained as a failure. Limits are 64
declared players, 16 MiB per compound, 64 MiB aggregate NBT, 128 journal records,
1 MiB journal and one million server callbacks. These profile limits must cause
whole-roster capacity refusal, never roster reduction. They are not certificates
of machine capacity. The final loaded-class inventory closes before the stop
record; a late game-class definition invalidates the process.

Owned launch/exit/custody, independent stopped-output inspection, genuine server
capture, timing overhead and side-effect controls remain required. The available
JVM checks load and verify actual transformed methods without initializing
Minecraft. They cannot certify live snapshots, transient state, tool equality,
clocks, disposal, isolation or T11/G1. The complete original gate remains open.
