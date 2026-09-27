package io.github.opencnid.strata.livebody;

import java.io.ByteArrayOutputStream;
import java.io.DataOutput;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.Objects;
import java.util.UUID;

/** Operator-only save-format capture for the pinned official 1.19.2 server.
 * The owning instrumentation must authenticate loaded bytes and the callback.
 * This codec supplies neither producer provenance nor a complete live-state claim.
 */
public final class PlayerNbt {
    public static final int MAX_BYTES = 16 * 1024 * 1024;
    private final Class<?> playerType, compoundType;
    private final Constructor<?> newCompound;
    private final Method save, uuid, server, sameThread, tagUuid, write;

    /** Bind exact inspected descriptors without initializing game classes. */
    public PlayerNbt(ClassLoader loader) throws ReflectiveOperationException, IOException {
        Objects.requireNonNull(loader);
        playerType = Class.forName("agh", false, loader);
        Class<?> entity = Class.forName("bbn", false, loader);
        compoundType = Class.forName("pj", false, loader);
        Class<?> nbtIo = Class.forName("pt", false, loader);
        Class<?> serverType = Class.forName("net.minecraft.server.MinecraftServer", false, loader);
        Class<?> loop = Class.forName("ayz", false, loader);
        if (!entity.isAssignableFrom(playerType) || !loop.isAssignableFrom(serverType))
            throw new IOException("PLAYER_NBT_BINDING");
        newCompound = compoundType.getConstructor();
        save = instance(entity, "f", compoundType, compoundType);
        uuid = instance(entity, "co", UUID.class);
        server = instance(entity, "cD", serverType);
        sameThread = instance(loop, "bm", boolean.class);
        tagUuid = instance(compoundType, "a", UUID.class, String.class);
        write = nbtIo.getDeclaredMethod("a", compoundType, DataOutput.class);
        if (!Modifier.isPublic(write.getModifiers()) || !Modifier.isStatic(write.getModifiers())
                || write.getReturnType() != void.class)
            throw new IOException("PLAYER_NBT_BINDING");
    }

    private static Method instance(Class<?> owner, String name, Class<?> result, Class<?>... args)
            throws ReflectiveOperationException, IOException {
        Method method = owner.getDeclaredMethod(name, args);
        if (!Modifier.isPublic(method.getModifiers()) || Modifier.isStatic(method.getModifiers())
                || method.getReturnType() != result)
            throw new IOException("PLAYER_NBT_BINDING");
        return method;
    }

    private void check(Object player, UUID expected) throws ReflectiveOperationException, IOException {
        if (player == null || player.getClass() != playerType || expected == null)
            throw new IOException("PLAYER_NBT_IDENTITY");
        Object owningServer = server.invoke(player);
        if (owningServer == null || !Boolean.TRUE.equals(sameThread.invoke(owningServer)))
            throw new IOException("PLAYER_NBT_SERVER_THREAD");
        if (!expected.equals(uuid.invoke(player))) throw new IOException("PLAYER_NBT_IDENTITY");
    }

    /** Invoke the real virtual serializer, preserving every emitted field.
     * No save load, world mutation, file/network output or gameplay tool is exposed.
     * The byte cap bounds output, not the game's construction time or object graph.
     */
    public byte[] capture(Object player, UUID expected) throws ReflectiveOperationException, IOException {
        check(player, expected);
        Object tag = newCompound.newInstance();
        if (save.invoke(player, tag) != tag) throw new IOException("PLAYER_NBT_SERIALIZER");
        check(player, expected);
        if (!expected.equals(tagUuid.invoke(tag, "UUID"))) throw new IOException("PLAYER_NBT_IDENTITY");
        return encode(tag);
    }

    // Package-private for direct format conformance; not an agent-facing API.
    byte[] encode(Object tag) throws ReflectiveOperationException, IOException {
        if (tag == null || tag.getClass() != compoundType) throw new IOException("PLAYER_NBT_TYPE");
        BoundedBytes bytes = new BoundedBytes(MAX_BYTES);
        try (DataOutputStream output = new DataOutputStream(bytes)) {
            write.invoke(null, tag, output);
        }
        return bytes.result();
    }

    static final class BoundedBytes extends OutputStream {
        private final int maximum;
        private final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        BoundedBytes(int maximum) {
            if (maximum < 1 || maximum > MAX_BYTES) throw new IllegalArgumentException("PLAYER_NBT_QUOTA");
            this.maximum = maximum;
        }
        private void reserve(int length) throws IOException {
            if (length > maximum - bytes.size()) throw new IOException("PLAYER_NBT_QUOTA");
        }
        @Override public void write(int value) throws IOException {
            reserve(1);
            bytes.write(value);
        }
        @Override public void write(byte[] value, int offset, int length) throws IOException {
            Objects.checkFromIndexSize(offset, length, value.length);
            reserve(length);
            bytes.write(value, offset, length);
        }
        byte[] result() { return bytes.toByteArray(); }
    }
}
