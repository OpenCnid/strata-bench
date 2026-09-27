package io.github.opencnid.strata.telemetry;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipFile;
import org.junit.jupiter.api.Test;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.objectweb.asm.tree.FieldInsnNode;
import org.spongepowered.asm.mixin.injection.Inject;
import static org.junit.jupiter.api.Assertions.*;

class FurnaceIntervalBytecodeTest {
    private ClassNode installed(String variable,String pin,String name) throws Exception {
        String value=System.getenv(variable);
        org.junit.jupiter.api.Assumptions.assumeTrue(value!=null,"requires private installed artifact");
        var path=Path.of(value);assertEquals(pin,HexFormat.of().formatHex(
            MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))));
        var node=new ClassNode();try(var jar=new ZipFile(path.toFile());var stream=jar.getInputStream(jar.getEntry(name+".class"))) {
            new ClassReader(stream).accept(node,0);
        }
        return node;
    }
    @Test void serverTickHasEverySelectedCallSiteAndOnlyOneActivationWrite() throws Exception {
        var node=installed("STRATA_THERMAL_CORE_JAR",FurnaceCapture.PINS.get("thermal"),FurnaceCapture.MACHINE.replace('.','/'));
        var method=node.methods.stream().filter(m->m.name.equals("tickServer")&&m.desc.equals("()V")).findFirst().orElseThrow();
        var instructions=Arrays.asList(method.instructions.toArray());
        for(var entry:Map.of("transferInput",2,"transferOutput",2,"chargeEnergy",1,"processOff",2).entrySet()) {
            var calls=instructions.stream().filter(i->i instanceof MethodInsnNode m&&m.name.equals(entry.getKey())).toList();
            assertEquals(entry.getValue().longValue(),calls.size());
            for(var call:calls) {
                var m=(MethodInsnNode)call;assertEquals(FurnaceCapture.MACHINE.replace('.','/'),m.owner);
                assertEquals("()V",m.desc);
            }
        }
        assertEquals(1,instructions.stream().filter(i->i instanceof FieldInsnNode f&&f.name.equals("isActive")&&f.getOpcode()==Opcodes.PUTFIELD).count());
        var field=(FieldInsnNode)instructions.stream().filter(i->i instanceof FieldInsnNode f&&f.name.equals("isActive")&&f.getOpcode()==Opcodes.PUTFIELD).findFirst().orElseThrow();
        assertEquals(FurnaceCapture.MACHINE.replace('.','/'),field.owner);
        assertEquals(1,instructions.stream().filter(i->i.getOpcode()==Opcodes.RETURN).count());
    }
    @Test void pinnedLifetimeMethodsAndSuperChainsReachTheSelectedHooks() throws Exception {
        var base=installed("STRATA_FORGE_SRG_JAR","b33801d8996d5579c7e5fe98224d05483c165f8d45a97d3e1d67e13bbe5d367b",
            "net/minecraft/world/level/block/entity/BlockEntity");
        for(String method:List.of("m_7651_","m_6339_","onChunkUnloaded")) {
            assertEquals(1,base.methods.stream().filter(m->m.name.equals(method)&&m.desc.equals("()V")).count());
        }
        for(String name:List.of("MachineBlockEntity","Reconfigurable4WayBlockEntity","AugmentableBlockEntity")) {
            var node=installed("STRATA_THERMAL_CORE_JAR",FurnaceCapture.PINS.get("thermal"),"cofh/thermal/lib/block/entity/"+name);
            assertTrue(node.methods.stream().noneMatch(m->m.name.equals("m_6339_")||m.name.equals("onChunkUnloaded")));
            for(var m:node.methods) if(m.name.equals("m_7651_")) assertTrue(Arrays.stream(m.instructions.toArray())
                .anyMatch(i->i instanceof MethodInsnNode c&&c.getOpcode()==Opcodes.INVOKESPECIAL&&c.owner.equals(node.superName)&&c.name.equals("m_7651_")&&c.desc.equals("()V")));
        }
        var core=installed("STRATA_COFH_CORE_JAR",FurnaceCapture.PINS.get("cofh_core"),"cofh/core/block/entity/TileCoFH");
        assertTrue(core.methods.stream().noneMatch(m->m.name.equals("m_6339_")||m.name.equals("onChunkUnloaded")));
        var remove=core.methods.stream().filter(m->m.name.equals("m_7651_")).findFirst().orElseThrow();
        assertTrue(Arrays.stream(remove.instructions.toArray()).anyMatch(i->i instanceof MethodInsnNode c&&c.owner.equals(core.superName)&&c.name.equals("m_7651_")&&c.getOpcode()==Opcodes.INVOKESPECIAL));
        var furnace=installed("STRATA_THERMAL_EXPANSION_JAR",FurnaceCapture.PINS.get("thermal_expansion"),FurnaceCapture.FURNACE.replace('.','/'));
        assertTrue(furnace.methods.stream().noneMatch(m->List.of("m_6339_","m_7651_","onChunkUnloaded").contains(m.name)));
    }
    @Test void compiledIntervalAndRetirementHooksAreNoncancellingAndStrict() throws Exception {
        int total=0;
        for(String name:List.of("FurnaceIntervalMixin","FurnaceLifetimeMixin")) {
            var type=Class.forName("io.github.opencnid.strata.telemetry.mixin."+name);int count=0;
            for(var method:type.getDeclaredMethods()) {
                var hook=method.getAnnotation(Inject.class);if(hook==null) continue;
                count++;assertFalse(hook.cancellable());assertFalse(hook.remap());
                int expected=(method.getName().contains("transfer_")||method.getName().contains("off"))?2:1;
                assertEquals(expected,hook.require());assertEquals(expected,hook.expect());assertEquals(expected,hook.allow());
                if(name.equals("FurnaceIntervalMixin")) assertArrayEquals(new String[]{"tickServer()V"},hook.method());
            }
            assertEquals(name.equals("FurnaceIntervalMixin")?12:3,count);total+=count;
        }
        assertEquals(15,total);
    }
}
