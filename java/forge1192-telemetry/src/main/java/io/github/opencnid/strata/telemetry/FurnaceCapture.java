package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.registries.ForgeRegistries;

/** Private native facts only. No recipe ID, player attribution, or score is inferred. */
public final class FurnaceCapture {
    static final String TRANSITION_POLICY = "thermal1192-native-furnace-transitions/1";
    static final String TICK_POLICY = "thermal1192-native-furnace-process-tick/1";
    static final String POLICY = "thermal1192-native-furnace-phases/2";
    static final String MACHINE = "cofh.thermal.lib.block.entity.MachineBlockEntity";
    static final String FURNACE = "cofh.thermal.expansion.block.entity.machine.MachineFurnaceTile";
    static final String AUGMENTABLE = "cofh.thermal.lib.block.entity.AugmentableBlockEntity";
    static final String RECIPE = "cofh.thermal.lib.util.recipes.internal.SimpleMachineRecipe";
    static final String INVENTORY = "cofh.thermal.lib.util.recipes.IMachineInventory";
    static final Map<String,String> PINS = Map.of(
        "thermal_expansion", "ddf119c33990e991875968c0e810583af091044a3368c28838646f30ace33f4c",
        "thermal", "20c99f015b9b3d034da1f017a14876bc6f15838d72dc450cfd0c1bdd803c10b5",
        "cofh_core", "1e47ecfa7e3bedb7043854d44c53537aacb4b75807c2f7de5df6ab2fa785203d");
    private static Class<?> machineClass, furnaceClass;
    private static MinecraftServer server;
    private static CraftCapture.Sink sink;
    private static Frame current;
    private static Frame ticking;
    private static JsonObject tickBefore;
    private static String tickRefusal;
    private static Frame transitioning;
    private static JsonObject transitionBefore;
    private static String transitionOperation, transitionRefusal;
    private static int baseProcessTick;

    private static final class Frame {
        final FurnacePhases phases;
        final BlockEntity tile;
        final ServerLevel level;
        final BlockPos position;
        final long tick;
        final JsonObject base = new JsonObject();
        Object recipe;
        JsonObject resolved;
        JsonObject registration;
        Frame(BlockEntity tile) {
            this.tile=tile; level=(ServerLevel)tile.getLevel(); tick=level.getGameTime();
            position=tile.getBlockPos().immutable();
            phases=new FurnacePhases(tile);
            base.addProperty("policy", POLICY);
            base.addProperty("transaction_id", UUID.randomUUID().toString());
            base.addProperty("dimension", level.dimension().location().toString());
            var coordinates=new JsonArray(); var p=position;
            coordinates.add(p.getX());coordinates.add(p.getY());coordinates.add(p.getZ());base.add("position",coordinates);
            base.addProperty("block_id","thermal:machine_furnace");
            base.addProperty("score_eligible",false);
            base.addProperty("recipe_registration_bound",false);
            base.addProperty("loaded_code_authenticated",false);
        }
    }

    static JsonObject support() throws IOException {
        if(sink!=null || current!=null || ticking!=null || transitioning!=null) throw new IOException("MACHINE_CAPTURE_ACTIVE");
        machineClass=null;furnaceClass=null;
        var artifacts=new JsonObject(); boolean matches=true;
        for(var entry:PINS.entrySet()) {
            var mod=ModList.get().getModFileById(entry.getKey());
            if(mod==null) { artifacts.add(entry.getKey(),JsonNull.INSTANCE);matches=false;continue; }
            var path=mod.getFile().getFilePath();
            if(!Files.isRegularFile(path)||Files.size(path)>32*1024*1024) throw new IOException("MACHINE_CAPTURE_ARTIFACT");
            try(var stream=Files.newInputStream(path)) {
                var hash=MessageDigest.getInstance("SHA-256");byte[] bytes=new byte[65536];int n;
                while((n=stream.read(bytes))!=-1) hash.update(bytes,0,n);
                String actual=HexFormat.of().formatHex(hash.digest());
                artifacts.addProperty(entry.getKey(),actual); matches &= entry.getValue().equals(actual);
            } catch(java.security.NoSuchAlgorithmException error) { throw new IOException(error); }
        }
        if(matches) try {
            machineClass=Class.forName(MACHINE);furnaceClass=Class.forName(FURNACE);
            if(!FurnaceCaptureMarker.class.isAssignableFrom(machineClass)) throw new IOException("MACHINE_CAPTURE_HOOK_MISSING");
            if(!FurnaceTickMarker.class.isAssignableFrom(machineClass)) throw new IOException("MACHINE_TICK_HOOK_MISSING");
            if(!FurnaceTransitionMarker.class.isAssignableFrom(machineClass)) throw new IOException("MACHINE_TRANSITION_HOOK_MISSING");
            if(!FurnaceRegistration.support()) throw new IOException("MACHINE_REGISTRATION_HOOK_MISSING");
        } catch(ReflectiveOperationException error) { throw new IOException("MACHINE_CAPTURE_CLASS",error); }
        var value=new JsonObject();value.addProperty("status",matches?"supported":"unsupported");
        value.add("artifacts",artifacts);value.addProperty("loaded_code_authenticated",false);
        value.addProperty("registration_hooks_verified",matches);
        return value;
    }
    static void activate(MinecraftServer value, CraftCapture.Sink destination) {
        if(sink!=null || current!=null || ticking!=null || transitioning!=null || !value.isDedicatedServer() || !value.isSameThread())
            throw new IllegalStateException("MACHINE_CAPTURE_ACTIVATION");
        server=value;sink=destination;
    }
    static void close() {
        if(current!=null || ticking!=null || transitioning!=null) throw new IllegalStateException("MACHINE_CAPTURE_INCOMPLETE");
        FurnaceRegistration.close();
        sink=null;server=null;
    }
    private static boolean active(Object tile, String method) {
        if(sink==null || furnaceClass==null) return false;
        if(!server.isSameThread()) throw new IllegalStateException("MACHINE_CAPTURE_THREAD");
        if(tile.getClass()!=furnaceClass) return false;
        // The first non-collector frame must be the injected native callback,
        // followed by the selected real native method. This is not a transformed
        // bytecode attestation; that separate qualification stays false.
        var callers=StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE).walk(s ->
            s.dropWhile(f -> f.getDeclaringClass()==FurnaceCapture.class).limit(2).toList());
        if(callers.size()!=2 || callers.get(0).getDeclaringClass()!=machineClass
                || callers.get(1).getDeclaringClass()!=machineClass
                || !callers.get(1).getMethodName().equals(method))
            throw new IllegalStateException("MACHINE_CAPTURE_CALLER");
        return true;
    }
    public static void enter(Object value) {
        if(!active(value,"processFinish")) return;
        if(current!=null || ticking!=null || transitioning!=null) throw new IllegalStateException("MACHINE_CAPTURE_NESTED");
        if(!(value instanceof BlockEntity tile) || !(tile.getLevel() instanceof ServerLevel level)
                || level.getServer()!=server || tile.isRemoved()
                || level.getBlockEntity(tile.getBlockPos())!=tile)
            throw new IllegalStateException("MACHINE_CAPTURE_LIFETIME");
        current=new Frame(tile);
    }
    public static void phase(Object value, int phase) {
        if(!active(value,"processFinish")) return;
        var frame=current;
        if(frame==null) throw new IllegalStateException("MACHINE_CAPTURE_UNPAIRED");
        frame.phases.advance(value,phase);lifetime(frame);
        if(frame.phases.refusal!=null) return;
        try {
            Object recipe=field(value,MACHINE,"curRecipe");
            exact(recipe,RECIPE);
            if(phase==1) frame.recipe=recipe;
            if(frame.recipe!=recipe) throw unsupported();
            JsonObject registration=FurnaceRegistration.observe(server,recipe);
            if(phase==1) frame.registration=registration;
            if(!frame.registration.equals(registration)) throw new UnsupportedOperationException("MACHINE_REGISTRATION_CHANGED");
            JsonObject resolved=recipe(recipe,value);
            if(phase==1) frame.resolved=resolved;
            if(!frame.resolved.equals(resolved)) throw unsupported();
            frame.phases.snapshot(state(value));
        } catch(ReflectiveOperationException | UnsupportedOperationException error) {
            frame.phases.refusal=switch(String.valueOf(error.getMessage())) {
                case "MACHINE_REGISTRATION_UNOBSERVED" -> "native_registration_unobserved";
                case "MACHINE_REGISTRATION_CHANGED" -> "native_registration_changed";
                default -> "native_profile_unsupported";
            };
        }
    }
    public static void exit(Object value) {
        if(!active(value,"processFinish")) return;
        var frame=current;
        if(frame==null) throw new IllegalStateException("MACHINE_CAPTURE_UNPAIRED");
        lifetime(frame);
        boolean complete=frame.phases.complete(value);
        if(complete) {
            frame.base.add("resolved_recipe",frame.resolved);
            frame.base.add("registration",frame.registration);
            frame.base.add("states",frame.phases.states);
            sink.emit("machine_completion","strata/NativeFurnaceCompletion/2",frame.base,new JsonArray());
        } else {
            frame.base.addProperty("reason",frame.phases.refusal);
            sink.emit("machine_capture_refused","strata/NativeFurnaceRefusal/2",frame.base,new JsonArray());
        }
        current=null;
    }
    public static void tickEnter(Object value) {
        if(!active(value,"processTick")) return;
        if(ticking!=null || current!=null || transitioning!=null) throw new IllegalStateException("MACHINE_TICK_NESTED");
        if(!(value instanceof BlockEntity tile) || !(tile.getLevel() instanceof ServerLevel level)
                || level.getServer()!=server) throw new IllegalStateException("MACHINE_TICK_LIFETIME");
        ticking=new Frame(tile);tickBefore=null;tickRefusal=null;
        ticking.base.addProperty("policy",TICK_POLICY);lifetime(ticking);
        try {
            tickBefore=state(value,false);
            ticking.recipe=field(value,MACHINE,"curRecipe");exact(ticking.recipe,RECIPE);
            ticking.registration=FurnaceRegistration.observe(server,ticking.recipe);
            ticking.resolved=recipe(ticking.recipe,value);
        } catch(ReflectiveOperationException | UnsupportedOperationException error) {
            tickRefusal=tickReason(error);
        }
    }
    public static void tickExit(Object value,int returned) {
        if(!active(value,"processTick")) return;
        var frame=ticking;
        if(frame==null || frame.tile!=value) throw new IllegalStateException("MACHINE_TICK_UNPAIRED");
        lifetime(frame);JsonObject after=null;
        if(tickRefusal==null) try {
            if(frame.recipe!=field(value,MACHINE,"curRecipe")) throw unsupported();
            if(!frame.registration.equals(FurnaceRegistration.observe(server,frame.recipe)))
                throw new UnsupportedOperationException("MACHINE_REGISTRATION_CHANGED");
            if(!frame.resolved.equals(recipe(frame.recipe,value))) throw unsupported();
            after=state(value,false);
        } catch(ReflectiveOperationException | UnsupportedOperationException error) {
            tickRefusal=tickReason(error);
        }
        if(tickRefusal==null) {
            var states=new JsonArray();states.add(tickBefore);states.add(after);
            frame.base.add("states",states);frame.base.addProperty("returned",returned);
            frame.base.add("registration",frame.registration);frame.base.add("resolved_recipe",frame.resolved);
            sink.emit("machine_process_tick","strata/NativeFurnaceProcessTick/1",frame.base,new JsonArray());
        } else {
            frame.base.addProperty("reason",tickRefusal);
            sink.emit("machine_process_tick_refused","strata/NativeFurnaceProcessTickRefusal/1",frame.base,new JsonArray());
        }
        ticking=null;tickBefore=null;tickRefusal=null;
    }
    public static void transitionEnter(Object value,String operation) {
        if(!"start".equals(operation) && !"refund".equals(operation))
            throw new IllegalStateException("MACHINE_TRANSITION_OPERATION");
        if(!active(value,"start".equals(operation)?"processStart":"tickServer")) return;
        if(transitioning!=null || current!=null || ticking!=null)
            throw new IllegalStateException("MACHINE_TRANSITION_NESTED");
        if(!(value instanceof BlockEntity tile) || !(tile.getLevel() instanceof ServerLevel level)
                || level.getServer()!=server) throw new IllegalStateException("MACHINE_TRANSITION_LIFETIME");
        transitioning=new Frame(tile);transitionBefore=null;transitionRefusal=null;
        transitionOperation=operation;baseProcessTick=0;lifetime(transitioning);
        transitioning.base.addProperty("policy",TRANSITION_POLICY);
        transitioning.base.addProperty("operation",operation);
        try {
            transitionBefore=state(value,false,true);
            if("start".equals(operation)) {
                baseProcessTick=number(field(value,MACHINE,"baseProcessTick"));
                if(baseProcessTick<=0) throw unsupported();
                transitioning.recipe=field(value,MACHINE,"curRecipe");exact(transitioning.recipe,RECIPE);
                transitioning.registration=FurnaceRegistration.observe(server,transitioning.recipe);
                transitioning.resolved=recipe(transitioning.recipe,value);
            }
        } catch(ReflectiveOperationException | UnsupportedOperationException error) {
            transitionRefusal=tickReason(error);
        }
    }
    public static void transitionExit(Object value,String operation) {
        if(!"start".equals(operation) && !"refund".equals(operation))
            throw new IllegalStateException("MACHINE_TRANSITION_OPERATION");
        if(!active(value,"start".equals(operation)?"processStart":"tickServer")) return;
        var frame=transitioning;
        if(frame==null || frame.tile!=value || !operation.equals(transitionOperation))
            throw new IllegalStateException("MACHINE_TRANSITION_UNPAIRED");
        lifetime(frame);JsonObject after=null;
        if(transitionRefusal==null) try {
            if("start".equals(operation)) {
                if(frame.recipe!=field(value,MACHINE,"curRecipe")
                        || baseProcessTick!=number(field(value,MACHINE,"baseProcessTick"))) throw unsupported();
                if(!frame.registration.equals(FurnaceRegistration.observe(server,frame.recipe)))
                    throw new UnsupportedOperationException("MACHINE_REGISTRATION_CHANGED");
                if(!frame.resolved.equals(recipe(frame.recipe,value))) throw unsupported();
            }
            after=state(value,false,true);
        } catch(ReflectiveOperationException | UnsupportedOperationException error) {
            transitionRefusal=tickReason(error);
        }
        if(transitionRefusal==null) {
            var states=new JsonArray();states.add(transitionBefore);states.add(after);frame.base.add("states",states);
            if("start".equals(operation)) {
                frame.base.addProperty("base_process_tick",baseProcessTick);
                frame.base.add("registration",frame.registration);frame.base.add("resolved_recipe",frame.resolved);
            }
            sink.emit("machine_process_transition","strata/NativeFurnaceProcessTransition/1",frame.base,new JsonArray());
        } else {
            frame.base.addProperty("reason",transitionRefusal);
            sink.emit("machine_process_transition_refused","strata/NativeFurnaceProcessTransitionRefusal/1",frame.base,new JsonArray());
        }
        transitioning=null;transitionBefore=null;transitionRefusal=null;transitionOperation=null;baseProcessTick=0;
    }
    private static String tickReason(Exception error) {
        return switch(String.valueOf(error.getMessage())) {
            case "MACHINE_REGISTRATION_UNOBSERVED" -> "native_registration_unobserved";
            case "MACHINE_REGISTRATION_CHANGED" -> "native_registration_changed";
            default -> "native_profile_unsupported";
        };
    }
    private static void lifetime(Frame frame) {
        if(frame.tile.isRemoved() || frame.tile.getLevel()!=frame.level
                || !frame.tile.getBlockPos().equals(frame.position)
                || frame.level.getServer()!=server || frame.level.getGameTime()!=frame.tick
                || frame.level.getBlockEntity(frame.tile.getBlockPos())!=frame.tile
                || !"thermal:machine_furnace".equals(String.valueOf(ForgeRegistries.BLOCKS.getKey(frame.tile.getBlockState().getBlock()))))
            throw new IllegalStateException("MACHINE_CAPTURE_LIFETIME");
    }
    private static JsonObject state(Object tile) throws ReflectiveOperationException { return state(tile,true); }
    private static JsonObject state(Object tile,boolean completed) throws ReflectiveOperationException {
        return state(tile,completed,false);
    }
    private static JsonObject state(Object tile,boolean completed,boolean dormant) throws ReflectiveOperationException {
        int augments=number(call(tile,"augSize"));
        if(augments<0 || augments>16 || number(call(tile,"invSize"))!=3+augments
                || field(tile,MACHINE,"curCatalyst")!=null) throw unsupported();
        var slots=new JsonArray();var aug=new JsonArray();
        for(int i=0;i<3+augments;i++) {
            Object storage=tile.getClass().getMethod("getSlot",int.class).invoke(tile,i);
            exact(storage,"cofh.lib.inventory.ItemStorageCoFH");
            var item=stack((ItemStack)call(storage,"getItemStack"));
            if(i<3) slots.add(item);
            else { if(item.get("count").getAsInt()!=0) throw unsupported();aug.add(item); }
        }
        Object energy=call(tile,"getEnergyStorage");exact(energy,"cofh.lib.energy.EnergyStorageCoFH");
        int rf=number(call(energy,"getEnergyStored")),process=number(field(tile,MACHINE,"process")),
            max=number(field(tile,MACHINE,"processMax")),step=number(field(tile,MACHINE,"processTick"));
        Object active=field(tile,AUGMENTABLE,"isActive");
        if(rf<0 || max<(dormant?0:1) || step<(dormant?0:1) || !(active instanceof Boolean)
                || (completed && (process>0 || !Boolean.TRUE.equals(active)))) throw unsupported();
        var out=new JsonObject();out.add("slots",slots);out.add("augments",aug);
        out.addProperty("energy_rf",rf);out.addProperty("process",process);out.addProperty("process_max",max);
        out.addProperty("process_tick",step);out.addProperty("active",(Boolean)active);
        if(!completed) {
            int capacity=number(call(energy,"getMaxEnergyStored"));
            if(capacity<=0 || rf>capacity || !Boolean.FALSE.equals(call(energy,"isCreative"))) throw unsupported();
            out.addProperty("energy_capacity",capacity);out.addProperty("energy_creative",false);
        }
        return out;
    }
    private static JsonObject recipe(Object recipe,Object tile) throws ReflectiveOperationException {
        var type=Class.forName(INVENTORY);
        var inputs=list(call(recipe,"getInputItems"));
        var outputs=list(recipe.getClass().getMethod("getOutputItems",type).invoke(recipe,tile));
        var chances=list(recipe.getClass().getMethod("getOutputItemChances",type).invoke(recipe,tile));
        var counts=list(field(tile,MACHINE,"itemInputCounts"));
        if(inputs.size()!=1 || outputs.size()!=1 || chances.size()!=1 || counts.size()!=1
                || !(chances.get(0) instanceof Float chance) || chance!=1.0f
                || !list(call(recipe,"getInputFluids")).isEmpty()
                || !list(recipe.getClass().getMethod("getOutputFluids",type).invoke(recipe,tile)).isEmpty()
                || !list(field(tile,MACHINE,"fluidInputCounts")).isEmpty()) throw unsupported();
        int energy=number(recipe.getClass().getMethod("getEnergy",type).invoke(recipe,tile));
        int count=number(counts.get(0));
        if(energy<=0 || count<=0 || count>64) throw unsupported();
        var input=stack((ItemStack)inputs.get(0));var output=stack((ItemStack)outputs.get(0));
        if(input.get("count").getAsInt()<=0 || output.get("count").getAsInt()<=0) throw unsupported();
        var result=new JsonObject();result.addProperty("runtime_class",RECIPE);
        result.add("input",input);result.add("output",output);
        result.addProperty("resolved_input_count",count);result.addProperty("output_chance",1);
        result.addProperty("recipe_energy_rf",energy);return result;
    }
    private static JsonObject stack(ItemStack item) {
        var tag=item.isEmpty()?new CompoundTag():item.save(new CompoundTag());tag.remove("id");tag.remove("Count");
        // This narrow profile keeps every broader recipe/metadata requirement open.
        if(!tag.isEmpty() || item.getCount()<0 || item.getCount()>64) throw unsupported();
        var out=new JsonObject();out.addProperty("item_id",item.isEmpty()?"minecraft:air":String.valueOf(ForgeRegistries.ITEMS.getKey(item.getItem())));
        out.addProperty("count",item.isEmpty()?0:item.getCount());out.addProperty("components_empty",true);
        try { out.addProperty("components_sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(tag.toString().getBytes(StandardCharsets.UTF_8)))); }
        catch(java.security.NoSuchAlgorithmException error) {throw new IllegalStateException(error);}
        return out;
    }
    private static Object field(Object target,String owner,String name) throws ReflectiveOperationException {
        var field=Class.forName(owner).getDeclaredField(name);field.setAccessible(true);return field.get(target);
    }
    private static Object call(Object target,String method) throws ReflectiveOperationException { return target.getClass().getMethod(method).invoke(target); }
    private static List<?> list(Object value) { if(!(value instanceof List<?> result) || result.size()>16) throw unsupported();return result; }
    private static int number(Object value) { if(!(value instanceof Integer result)) throw unsupported();return result; }
    private static void exact(Object value,String name) { if(value==null || !value.getClass().getName().equals(name)) throw unsupported(); }
    private static UnsupportedOperationException unsupported() { return new UnsupportedOperationException("MACHINE_CAPTURE_PROFILE"); }
    private FurnaceCapture() {}
}
