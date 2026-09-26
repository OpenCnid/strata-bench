package io.github.opencnid.strata.telemetry;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.zip.ZipFile;
import org.junit.jupiter.api.Test;
import org.spongepowered.asm.mixin.injection.Inject;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.JumpInsnNode;
import org.objectweb.asm.tree.MethodInsnNode;
import static org.junit.jupiter.api.Assertions.*;

/** Installed bytecode/call-site inspection, not a running transformed Forge test. */
class FurnaceCaptureBytecodeTest {
    @Test void pinnedProcessFinishValidatesThenResolvesOutputAndInput() throws Exception {
        String configured=System.getenv("STRATA_THERMAL_CORE_JAR");
        org.junit.jupiter.api.Assumptions.assumeTrue(configured!=null,"requires private installed artifact");
        var path=Path.of(configured);
        assertEquals(FurnaceCapture.PINS.get("thermal"),HexFormat.of().formatHex(
            MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))));
        var node=new ClassNode();
        try(var jar=new ZipFile(path.toFile());var stream=jar.getInputStream(jar.getEntry(FurnaceCapture.MACHINE.replace('.','/')+".class"))) {
            new ClassReader(stream).accept(node,0);
        }
        var method=node.methods.stream().filter(m->m.name.equals("processFinish") && m.desc.equals("()V")).findFirst().orElseThrow();
        var instructions=Arrays.stream(method.instructions.toArray()).filter(i->i.getOpcode()>=0).toList();
        assertEquals(List.of(Opcodes.ALOAD,Opcodes.INVOKEVIRTUAL,Opcodes.IFNE,Opcodes.ALOAD,Opcodes.INVOKEVIRTUAL,
            Opcodes.RETURN,Opcodes.ALOAD,Opcodes.INVOKEVIRTUAL,Opcodes.ALOAD,Opcodes.INVOKEVIRTUAL,
            Opcodes.ALOAD,Opcodes.INVOKEVIRTUAL,Opcodes.RETURN),instructions.stream().map(i->i.getOpcode()).toList());
        assertEquals(List.of("validateInputs()Z","processOff()V","resolveOutputs()V","resolveInputs()V","markDirtyFast()V"),
            instructions.stream().filter(i->i instanceof MethodInsnNode).map(i->{var m=(MethodInsnNode)i;return m.name+m.desc;}).toList());
        var target=((JumpInsnNode)instructions.get(2)).label.getNext();
        while(target.getOpcode()<0) target=target.getNext();
        assertSame(instructions.get(6),target);
    }
    @Test void compiledMixinRetainsStrictCallSiteCountsAndNoncancellingHooks() throws Exception {
        var type=Class.forName("io.github.opencnid.strata.telemetry.mixin.FurnaceCaptureMixin");
        int hooks=0;
        for(var method:type.getDeclaredMethods()) {
            var inject=method.getAnnotation(Inject.class);if(inject==null) continue;
            hooks++;assertArrayEquals(new String[]{"processFinish()V"},inject.method());
            assertFalse(inject.cancellable());assertFalse(inject.remap());
            int count=method.getName().endsWith("Exit")?2:1;
            assertEquals(count,inject.require());assertEquals(count,inject.expect());assertEquals(count,inject.allow());
        }
        assertEquals(5,hooks);
    }
}
