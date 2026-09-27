package io.github.opencnid.strata.telemetry;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.zip.ZipFile;
import org.junit.jupiter.api.Test;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.FieldInsnNode;
import org.objectweb.asm.tree.MethodInsnNode;
import static org.junit.jupiter.api.Assertions.*;

/** Pinned installed bytecode and compiled hooks, not transformed runtime evidence. */
class FurnaceTransitionBytecodeTest {
    private ClassNode installed() throws Exception {
        String configured=System.getenv("STRATA_THERMAL_CORE_JAR");
        org.junit.jupiter.api.Assumptions.assumeTrue(configured!=null,"requires private installed artifact");
        var path=Path.of(configured);
        assertEquals(FurnaceCapture.PINS.get("thermal"),HexFormat.of().formatHex(
            MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))));
        var node=new ClassNode();
        try(var jar=new ZipFile(path.toFile());var stream=jar.getInputStream(
                jar.getEntry(FurnaceCapture.MACHINE.replace('.','/')+".class"))) {
            new ClassReader(stream).accept(node,0);
        }
        return node;
    }
    @Test void startCarriesProgressIntoBothCountersAndRestoresBaseStep() throws Exception {
        var method=installed().methods.stream().filter(m->m.name.equals("processStart")&&m.desc.equals("()V"))
            .findFirst().orElseThrow();
        var instructions=Arrays.stream(method.instructions.toArray()).filter(i->i.getOpcode()>=0).toList();
        assertEquals(List.of(Opcodes.ALOAD,Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.PUTFIELD,
            Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.ALOAD,Opcodes.INVOKEINTERFACE,Opcodes.ISTORE,
            Opcodes.ILOAD,Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.IADD,Opcodes.ISTORE,
            Opcodes.ALOAD,Opcodes.ALOAD,Opcodes.ILOAD,Opcodes.DUP_X1,Opcodes.PUTFIELD,
            Opcodes.PUTFIELD,Opcodes.ALOAD,Opcodes.INVOKEVIRTUAL,Opcodes.IFEQ,
            Opcodes.ALOAD,Opcodes.INVOKESTATIC,Opcodes.RETURN),
            instructions.stream().map(i->i.getOpcode()).toList());
        assertEquals(List.of("baseProcessTick","processTick","curRecipe","process","processMax","process"),
            instructions.stream().filter(i->i instanceof FieldInsnNode).map(i->((FieldInsnNode)i).name).toList());
        var call=(MethodInsnNode)instructions.get(7);
        assertEquals("cofh/thermal/lib/util/recipes/internal/IMachineRecipe",call.owner);
        assertEquals("getEnergy(Lcofh/thermal/lib/util/recipes/IMachineInventory;)I",call.name+call.desc);
    }
    @Test void refundIsTheSingleNativeModifyAndPrecedesProcessOff() throws Exception {
        var method=installed().methods.stream().filter(m->m.name.equals("tickServer")&&m.desc.equals("()V"))
            .findFirst().orElseThrow();
        var instructions=Arrays.stream(method.instructions.toArray()).filter(i->i.getOpcode()>=0).toList();
        var refunds=instructions.stream().filter(i->i instanceof MethodInsnNode m && m.owner.equals(
            "cofh/lib/energy/EnergyStorageCoFH")&&m.name.equals("modify")&&m.desc.equals("(I)V")).toList();
        assertEquals(1,refunds.size());int index=instructions.indexOf(refunds.get(0));
        assertEquals(List.of(Opcodes.ALOAD,Opcodes.GETFIELD,Opcodes.ALOAD,Opcodes.GETFIELD,
            Opcodes.INEG,Opcodes.INVOKEVIRTUAL,Opcodes.ALOAD,Opcodes.INVOKEVIRTUAL),
            instructions.subList(index-5,index+3).stream().map(i->i.getOpcode()).toList());
        assertEquals("energyStorage",((FieldInsnNode)instructions.get(index-4)).name);
        assertEquals("process",((FieldInsnNode)instructions.get(index-2)).name);
        assertEquals("processOff",((MethodInsnNode)instructions.get(index+2)).name);
        assertEquals(2,instructions.stream().filter(i->i instanceof MethodInsnNode m&&m.name.equals("processStart")).count());
    }
    @Test void fourReadOnlyHooksHaveExactUnambiguousTargets() throws Exception {
        var type=Class.forName("io.github.opencnid.strata.telemetry.mixin.FurnaceTransitionMixin");
        assertTrue(FurnaceTransitionMarker.class.isAssignableFrom(type));int count=0;
        for(var method:type.getDeclaredMethods()) {
            var inject=method.getAnnotation(Inject.class);if(inject==null) continue;
            count++;assertFalse(inject.cancellable());assertFalse(inject.remap());
            assertEquals(1,inject.require());assertEquals(1,inject.expect());assertEquals(1,inject.allow());
            assertEquals(1,inject.at().length);var at=inject.at()[0];
            if(method.getName().contains("start")) {
                assertArrayEquals(new String[]{"processStart()V"},inject.method());
                assertEquals(method.getName().endsWith("Enter")?"HEAD":"RETURN",at.value());
            } else {
                assertArrayEquals(new String[]{"tickServer()V"},inject.method());
                assertEquals("INVOKE",at.value());
                assertEquals("Lcofh/lib/energy/EnergyStorageCoFH;modify(I)V",at.target());
                assertEquals(method.getName().endsWith("Enter")?At.Shift.BEFORE:At.Shift.AFTER,at.shift());
            }
        }
        assertEquals(4,count);
    }
}
