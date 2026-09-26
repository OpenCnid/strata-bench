package io.github.opencnid.strata.telemetry;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.zip.ZipFile;
import org.junit.jupiter.api.Test;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.spongepowered.asm.mixin.injection.Inject;
import static org.junit.jupiter.api.Assertions.*;

/** Native artifact and compiled call-site checks; no transformed-runtime claim. */
class RecipeRegistrationBytecodeTest {
    @Test void allDeclaredHookCountsMatchPinnedNativeReturnsAndRefreshOrder() throws Exception {
        String configured=System.getenv("STRATA_THERMAL_CORE_JAR");
        org.junit.jupiter.api.Assumptions.assumeTrue(configured!=null,"requires private installed artifact");
        var path=Path.of(configured);
        assertEquals(FurnaceCapture.PINS.get("thermal"),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))));
        try(var jar=new ZipFile(path.toFile())) {
            for(String simple:new String[]{"FurnaceRegistration","RecipeRegistration"}) {
                var type=Class.forName("io.github.opencnid.strata.telemetry.mixin."+simple+"Mixin");
                String target=simple.equals("FurnaceRegistration")?FurnaceRegistration.MANAGER:FurnaceRegistration.SINGLE;
                var node=new ClassNode();try(var stream=jar.getInputStream(jar.getEntry(target.replace('.','/')+".class"))) {new ClassReader(stream).accept(node,0);}
                for(var callback:type.getDeclaredMethods()) {
                    var inject=callback.getAnnotation(Inject.class);if(inject==null) continue;
                    assertFalse(inject.cancellable());assertFalse(inject.remap());
                    var nativeMethod=node.methods.stream().filter(m->(m.name+m.desc).equals(inject.method()[0])).findFirst().orElseThrow();
                    long count=inject.at()[0].value().equals("HEAD")?1:Arrays.stream(nativeMethod.instructions.toArray())
                        .filter(i->i.getOpcode()==Opcodes.RETURN || i.getOpcode()==Opcodes.ARETURN).count();
                    assertEquals(count,inject.require(),callback.getName());assertEquals(count,inject.expect());assertEquals(count,inject.allow());
                }
                if(simple.equals("FurnaceRegistration")) {
                    var refresh=node.methods.stream().filter(m->m.name.equals("refresh")).findFirst().orElseThrow();
                    var calls=Arrays.stream(refresh.instructions.toArray()).filter(i->i instanceof MethodInsnNode).map(i->(MethodInsnNode)i).toList();
                    assertEquals("clear",calls.get(0).name);
                    assertTrue(calls.stream().anyMatch(c->c.name.equals("createConvertedRecipes")));
                    assertEquals(2,calls.stream().filter(c->c.name.equals("addRecipe")).count());
                }
            }
        }
    }
}
