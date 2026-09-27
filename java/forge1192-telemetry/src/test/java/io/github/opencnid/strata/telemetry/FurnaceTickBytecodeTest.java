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
import org.objectweb.asm.tree.FieldInsnNode;
import org.objectweb.asm.tree.MethodInsnNode;
import static org.junit.jupiter.api.Assertions.*;

/** Exact installed bytecode and compiled hooks; not a transformed native run. */
class FurnaceTickBytecodeTest {
    private ClassNode installed(String variable,String pin,String type) throws Exception {
        String configured=System.getenv(variable);
        org.junit.jupiter.api.Assumptions.assumeTrue(configured!=null,"requires private installed artifact");
        var path=Path.of(configured);
        assertEquals(pin,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))));
        var node=new ClassNode();
        try(var jar=new ZipFile(path.toFile());var stream=jar.getInputStream(jar.getEntry(type.replace('.','/')+".class"))) {
            new ClassReader(stream).accept(node,0);
        }
        return node;
    }
    @Test void nativeProcessingDebitsBeforeProgressAndHasTwoReturns() throws Exception {
        var node=installed("STRATA_THERMAL_CORE_JAR",FurnaceCapture.PINS.get("thermal"),FurnaceCapture.MACHINE);
        var method=node.methods.stream().filter(m->m.name.equals("processTick")&&m.desc.equals("()I")).findFirst().orElseThrow();
        var instructions=Arrays.stream(method.instructions.toArray()).filter(i->i.getOpcode()>=0).toList();
        assertEquals(List.of(Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.IFGT,Opcodes.ICONST_0,Opcodes.IRETURN,
            Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.INEG,Opcodes.INVOKEVIRTUAL,
            Opcodes.ALOAD,Opcodes.DUP,Opcodes.GETFIELD,Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.ISUB,
            Opcodes.PUTFIELD,Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.IRETURN),
            instructions.stream().map(i->i.getOpcode()).toList());
        var debit=(MethodInsnNode)instructions.get(10);
        assertEquals("cofh/lib/energy/EnergyStorageCoFH",debit.owner);
        assertEquals("modify(I)V",debit.name+debit.desc);
        assertEquals(List.of("process","energyStorage","processTick","process","processTick","process","processTick"),
            instructions.stream().filter(i->i instanceof FieldInsnNode).map(i->((FieldInsnNode)i).name).toList());
    }
    @Test void nativeStorageRetainsCreativeBypassAndClampsNegativeEnergy() throws Exception {
        var node=installed("STRATA_COFH_CORE_JAR",FurnaceCapture.PINS.get("cofh_core"),"cofh.lib.energy.EnergyStorageCoFH");
        var method=node.methods.stream().filter(m->m.name.equals("modify")&&m.desc.equals("(I)V")).findFirst().orElseThrow();
        var instructions=Arrays.stream(method.instructions.toArray()).filter(i->i.getOpcode()>=0).toList();
        assertEquals(List.of("isCreative()Z","max(II)I"),instructions.stream().filter(i->i instanceof MethodInsnNode)
            .map(i->{var m=(MethodInsnNode)i;return m.name+m.desc;}).toList());
        assertEquals(List.of(Opcodes.ALOAD,Opcodes.INVOKEVIRTUAL,Opcodes.IFEQ,Opcodes.ILOAD,Opcodes.ICONST_0,
            Opcodes.INVOKESTATIC,Opcodes.ISTORE,Opcodes.ALOAD,Opcodes.DUP,Opcodes.GETFIELD,Opcodes.ILOAD,Opcodes.IADD,
            Opcodes.PUTFIELD,Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.IF_ICMPLE,
            Opcodes.ALOAD,Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.PUTFIELD,Opcodes.GOTO,Opcodes.ALOAD,
            Opcodes.GETFIELD,Opcodes.IFGE,Opcodes.ALOAD,Opcodes.ICONST_0,Opcodes.PUTFIELD,Opcodes.RETURN),
            instructions.stream().map(i->i.getOpcode()).toList());
    }
    @Test void hooksAreReadOnlyNoncancellingAndRequireExactCounts() throws Exception {
        var type=Class.forName("io.github.opencnid.strata.telemetry.mixin.FurnaceTickMixin");
        assertTrue(FurnaceTickMarker.class.isAssignableFrom(type));
        int count=0;
        for(var method:type.getDeclaredMethods()) {
            var inject=method.getAnnotation(Inject.class);if(inject==null) continue;
            count++;assertArrayEquals(new String[]{"processTick()I"},inject.method());
            assertFalse(inject.cancellable());assertFalse(inject.remap());
            int expected=method.getName().endsWith("Exit")?2:1;
            assertEquals(expected,inject.require());assertEquals(expected,inject.expect());assertEquals(expected,inject.allow());
        }
        assertEquals(2,count);
    }
}
