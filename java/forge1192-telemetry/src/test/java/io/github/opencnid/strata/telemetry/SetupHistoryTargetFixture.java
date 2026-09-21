package io.github.opencnid.strata.telemetry;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.jar.JarFile;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Type;
import org.objectweb.asm.tree.AnnotationNode;
import org.objectweb.asm.tree.ClassNode;

/** Offline pinned bytecode check. Does not load Minecraft or apply a Mixin. */
public final class SetupHistoryTargetFixture {
    private static Object property(AnnotationNode annotation, String name) {
        for (int i = 0; i < annotation.values.size(); i += 2)
            if (annotation.values.get(i).equals(name)) return annotation.values.get(i + 1);
        return null;
    }
    private static AnnotationNode annotation(List<AnnotationNode> a, List<AnnotationNode> b, String name) {
        var all = new ArrayList<AnnotationNode>();
        if (a != null) all.addAll(a); if (b != null) all.addAll(b);
        return all.stream().filter(v -> v.desc.equals(name)).findFirst().orElseThrow();
    }
    private static ClassNode read(JarFile jar, String name) throws Exception {
        var entry = jar.getJarEntry(name + ".class");
        if (entry == null) return null;
        var node = new ClassNode();
        try (var input = jar.getInputStream(entry)) {
            new ClassReader(input).accept(node, ClassReader.SKIP_CODE | ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
        }
        return node;
    }
    private static String hash(Path path) throws Exception {
        var digest = MessageDigest.getInstance("SHA-256");
        try (var input = Files.newInputStream(path)) {
            byte[] buffer = new byte[65536]; int count;
            while ((count = input.read(buffer)) != -1) digest.update(buffer, 0, count);
        }
        return HexFormat.of().formatHex(digest.digest());
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) throw new IllegalArgumentException("module.jar forge-srg.jar teams.jar new-private-report.json");
        var report = new JsonObject(); report.addProperty("schema", "strata/SetupHistoryTargetAudit/1");
        report.addProperty("module_sha256", hash(Path.of(args[0])));
        report.addProperty("forge_srg_sha256", hash(Path.of(args[1])));
        report.addProperty("teams_sha256", hash(Path.of(args[2])));
        report.addProperty("runtime_hooks_applied", false);
        report.addProperty("scoring_eligible", false);
        var checks = new JsonArray(); boolean pass = true; int mixins = 0;
        try (var module = new JarFile(args[0]); var forge = new JarFile(args[1]); var teams = new JarFile(args[2])) {
            JsonObject config;
            try (var input = module.getInputStream(module.getJarEntry("strata.craft-evidence.mixins.json"))) {
                config = JsonParser.parseString(new String(input.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
            }
            for (var name : config.getAsJsonArray("server")) {
                if (!name.getAsString().endsWith("HistoryMixin")) continue;
                mixins++;
                var mixin = read(module, (config.get("package").getAsString() + "." + name.getAsString()).replace('.', '/'));
                var spec = annotation(mixin.visibleAnnotations, mixin.invisibleAnnotations, "Lorg/spongepowered/asm/mixin/Mixin;");
                var values = (List<?>)property(spec, "value");
                String target = values == null ? ((List<?>)property(spec, "targets")).get(0).toString().replace('.', '/')
                    : ((Type)values.get(0)).getInternalName();
                ClassNode nativeClass = read(target.startsWith("net/minecraft/") ? forge : teams, target);
                for (var method : mixin.methods) {
                    if (!method.name.startsWith("strata$")) continue;
                    var inject = annotation(method.visibleAnnotations, method.invisibleAnnotations,
                        "Lorg/spongepowered/asm/mixin/injection/Inject;");
                    var selectors = (List<?>)property(inject, "method");
                    for (Object selector : selectors) {
                        boolean found = nativeClass != null && nativeClass.methods.stream()
                            .anyMatch(candidate -> (candidate.name + candidate.desc).equals(selector));
                        boolean strict = Integer.valueOf(1).equals(property(inject, "require"))
                            && Integer.valueOf(1).equals(property(inject, "allow"));
                        var check = new JsonObject(); check.addProperty("mixin", name.getAsString());
                        check.addProperty("target", target); check.addProperty("selector", selector.toString());
                        check.addProperty("target_present", found); check.addProperty("strict_injection", strict);
                        checks.add(check); pass &= found && strict;
                    }
                }
            }
        }
        pass &= mixins == 8 && checks.size() == 25;
        report.addProperty("mixins", mixins); report.add("checks", checks);
        report.addProperty("result", pass ? "pass" : "fail");
        Files.writeString(Path.of(args[3]), new Gson().toJson(report) + "\n", StandardOpenOption.CREATE_NEW);
        if (!pass) throw new IllegalStateException("SETUP_HISTORY_TARGET_AUDIT_FAILED");
    }
    private SetupHistoryTargetFixture() {}
}
