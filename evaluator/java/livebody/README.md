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
