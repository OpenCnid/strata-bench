package io.github.opencnid.strata.fixed;

import java.io.*;
import java.lang.instrument.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

/** Freeze two inspected URL constants after the JVM verifies the original JAR. */
public final class Agent implements ClassFileTransformer {
    public static final String PREFIX = "io.github.opencnid.strata.fixed";
    private static final Map<String, String[]> TARGETS = Map.of(
        "com/portingdeadmods/cable_facades/CFConfig", new String[]{
            "601b70c83a14debbb5e4679196a319c1a31eab4d4b008cd33b1feca2551bda0d",
            "https://raw.githubusercontent.com/Porting-Dead-Mods/Cable-Facades/refs/heads/1.21.1/configs/",
            // EventBus 6.0.3 makes the annotated onLoad callback public. Exact
            // vendor-transform reproduction changes only byte 8925 (8 -> 9).
            "1ab0dee01c531ff6a89fd85aee2109f5e8036d342e0c283e76a9101b0aab8092"},
        "blusunrize/immersiveengineering/ImmersiveEngineering$ThreadContributorSpecialsDownloader", new String[]{
            "b47bfd98a885800760e9e7d7c24d60ec2d4e89da6cbc1ed9ad1e82a46283e2fb",
            "https://raw.githubusercontent.com/BluSunrize/ImmersiveEngineering/gh-pages/contributorRevolvers.json"});

    public static void premain(String options, Instrumentation instrumentation) throws Exception {
        if (options != null && !options.isEmpty()) throw new IOException("FIXED_DATA_OPTIONS");
        if (!System.getProperty("java.protocol.handler.pkgs", "").isEmpty())
            throw new IOException("FIXED_DATA_HANDLER_OCCUPIED");
        Data.startJournal();
        Data.verify();
        for (Class<?> loaded : instrumentation.getAllLoadedClasses())
            if (TARGETS.containsKey(loaded.getName().replace('.', '/')))
                throw new IOException("FIXED_DATA_ALREADY_LOADED");
        System.setProperty("java.protocol.handler.pkgs", PREFIX);
        instrumentation.addTransformer(new Agent(), false);
        Data.record("STRATA_FIXED_DATA_READY/1 " + Data.identity());
    }

    @Override public byte[] transform(ClassLoader loader, String name, Class<?> redefined,
                                       ProtectionDomain domain, byte[] input) {
        if (!TARGETS.containsKey(name)) return null;
        try {
            if (redefined != null) throw new IOException("FIXED_DATA_REDEFINITION");
            byte[] result = patch(name, input);
            Data.record("STRATA_FIXED_DATA_BOUND/1 " + name + " " + Data.sha256(input));
            return result;
        } catch (Exception error) {
            // JVM ignores transformer exceptions and otherwise runs the original
            // downloader. A mismatch must terminate this owned JVM instead.
            Data.record("STRATA_FIXED_DATA_REFUSED/1 " + name + " " + Data.sha256(input));
            // Private startup logs retain only these two named class identities.
            // Capture bounded evidence before halting; never admit observed bytes.
            if (input.length <= 65536)
                Data.record("STRATA_FIXED_DATA_CLASS/1 " + name + " "
                    + Data.sha256(input) + " " + Base64.getEncoder().encodeToString(input));
            Runtime.getRuntime().halt(126);
            throw new AssertionError("unreachable");
        }
    }

    public static byte[] patch(String name, byte[] input) throws IOException {
        String[] target = TARGETS.get(name);
        String hash = Data.sha256(input);
        if (target == null || input.length > 1048576
                || !(hash.equals(target[0]) || (target.length == 3 && hash.equals(target[2]))))
            throw new IOException("FIXED_DATA_CLASS_PIN");
        return replaceConstant(input, target[1], target[1].replace("https://", "stratafixed://"));
    }

    // Preserve all bytecode, attributes, constants and ordering except one exact
    // ASCII URL constant. No vendor classes or signatures are rewritten on disk.
    static byte[] replaceConstant(byte[] input, String from, String to) throws IOException {
        DataInputStream in = new DataInputStream(new ByteArrayInputStream(input));
        ByteArrayOutputStream bytes = new ByteArrayOutputStream(input.length + 32);
        DataOutputStream out = new DataOutputStream(bytes);
        if (in.readInt() != 0xcafebabe) throw new IOException("FIXED_DATA_CLASS_FORMAT");
        out.writeInt(0xcafebabe); out.writeShort(in.readUnsignedShort()); out.writeShort(in.readUnsignedShort());
        int count = in.readUnsignedShort(), changed = 0;
        out.writeShort(count);
        for (int i = 1; i < count; i++) {
            int tag = in.readUnsignedByte(); out.writeByte(tag);
            if (tag == 1) {
                int n = in.readUnsignedShort(); byte[] value = in.readNBytes(n);
                if (value.length != n) throw new EOFException();
                if (Arrays.equals(value, from.getBytes(StandardCharsets.US_ASCII))) {
                    value = to.getBytes(StandardCharsets.US_ASCII); changed++;
                }
                out.writeShort(value.length); out.write(value);
            } else {
                int n = switch (tag) {
                    case 3, 4, 9, 10, 11, 12, 17, 18 -> 4;
                    case 5, 6 -> 8;
                    case 7, 8, 16, 19, 20 -> 2;
                    case 15 -> 3;
                    default -> throw new IOException("FIXED_DATA_CLASS_FORMAT");
                };
                byte[] value = in.readNBytes(n);
                if (value.length != n) throw new EOFException();
                out.write(value);
                if (tag == 5 || tag == 6) i++;
            }
        }
        if (changed != 1) throw new IOException("FIXED_DATA_CONSTANT_COUNT");
        out.write(in.readAllBytes());
        return bytes.toByteArray();
    }
}
