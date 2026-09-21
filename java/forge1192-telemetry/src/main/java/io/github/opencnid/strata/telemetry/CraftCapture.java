package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.inventory.InventoryMenu;
import net.minecraft.world.inventory.ResultContainer;
import net.minecraft.world.inventory.ResultSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.fml.ModList;

/** Private read-only native resource witness. A witness alone grants no score. */
public final class CraftCapture {
    static final String POLICY = "server-result-pickup-fastbench-bound/2";
    static final String FASTBENCH_SHA256 = "a2ac76078734a2506dec112cf9b6ba214528ce91e99ae5553070a88690f61c12";
    private static final String FASTBENCH_SLOT = "shadows.fastbench.util.CraftResultSlotExt";
    private static boolean fastbench;
    interface Sink { void emit(String kind, String schema, JsonObject payload, JsonArray actors); }
    private static volatile Sink sink;
    private static final ThreadLocal<ArrayList<Frame>> frames = ThreadLocal.withInitial(ArrayList::new);
    private static final class Frame {
        final AbstractContainerMenu menu; final ServerPlayer player;
        final String id = UUID.randomUUID().toString();
        int callbacks; boolean nested; JsonObject callback;
        Frame(AbstractContainerMenu menu, ServerPlayer player) { this.menu=menu; this.player=player; }
    }
    static JsonObject support() throws java.io.IOException {
        if (!CraftClickMarker.class.isAssignableFrom(AbstractContainerMenu.class))
            throw new java.io.IOException("CRAFT_CAPTURE_HOOK_MISSING");
        var mod=ModList.get().getModFileById("fastbench"); fastbench=false;
        if(mod!=null) {
            var path=mod.getFile().getFilePath();
            if(!Files.isRegularFile(path) || Files.size(path)>16*1024*1024) throw new java.io.IOException("CRAFT_CAPTURE_ARTIFACT");
            try(var stream=Files.newInputStream(path)) {
                var hash=MessageDigest.getInstance("SHA-256");byte[] bytes=new byte[65536];int n;
                while((n=stream.read(bytes))!=-1) hash.update(bytes,0,n);
                if(!FASTBENCH_SHA256.equals(HexFormat.of().formatHex(hash.digest())))
                    throw new java.io.IOException("CRAFT_CAPTURE_ARTIFACT");
            } catch(java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
            fastbench=true;
        }
        var result=new JsonObject();result.addProperty("hook_verified",true);
        if(fastbench) result.addProperty("fastbench_sha256",FASTBENCH_SHA256);
        else result.add("fastbench_sha256",JsonNull.INSTANCE);
        return result;
    }
    static boolean supportedSlot(String name,boolean pinned) {
        return name.equals("net.minecraft.world.inventory.ResultSlot") || pinned && name.equals(FASTBENCH_SLOT);
    }
    static void activate(Sink value) { if (sink!=null) throw new IllegalStateException("CRAFT_CAPTURE_ACTIVE"); sink=value; }
    static void close() {
        if (!frames.get().isEmpty()) throw new IllegalStateException("CRAFT_CAPTURE_INCOMPLETE");
        frames.remove(); sink=null;
    }
    private static boolean active(Player player) {
        if (sink==null || !(player instanceof ServerPlayer server)) return false;
        if (!server.getServer().isSameThread()) throw new IllegalStateException("CRAFT_CAPTURE_THREAD");
        return true;
    }
    public static void begin(AbstractContainerMenu menu, int slot, int button, ClickType type, Player player) {
        if (!active(player)) return;
        var stack=frames.get();
        if (stack.size()>=16) throw new IllegalStateException("CRAFT_CAPTURE_DEPTH");
        for (var parent:stack) if (parent!=null) parent.nested=true;
        stack.add(null); // Every native click is paired, including unsupported clicks.
        if (slot!=0 || button!=0 || type!=ClickType.PICKUP || player.isCreative() || player.isSpectator()
            || menu!=player.containerMenu || !menu.getCarried().isEmpty()
            || menu.getClass()!=CraftingMenu.class && menu.getClass()!=InventoryMenu.class
            || menu.slots.size()!=46 || !(menu.slots.get(0) instanceof ResultSlot)
            || !supportedSlot(menu.slots.get(0).getClass().getName(),fastbench)
            || !(menu.slots.get(0).container instanceof ResultContainer result)
            || !(result.getRecipeUsed() instanceof ShapedRecipe recipe)
            || recipe.getClass()!=ShapedRecipe.class || menu.slots.get(0).getItem().isEmpty()) return;
        var frame=new Frame(menu,(ServerPlayer)player); frame.nested=stack.size()!=1;
        stack.set(stack.size()-1,frame);
        JsonObject value=base(frame); value.addProperty("recipe_id",recipe.getId().toString());
        value.add("recipe_output",item(recipe.getResultItem()));
        value.addProperty("grid_size",menu instanceof CraftingMenu?9:4);
        value.add("state",state(menu));
        emit(frame,"craft_begin","strata/CraftBegin/1",value);
    }
    public static void end(AbstractContainerMenu menu, Player player) {
        if (!active(player)) return;
        var stack=frames.get();
        if (stack.isEmpty()) throw new IllegalStateException("CRAFT_CAPTURE_UNPAIRED");
        var frame=stack.remove(stack.size()-1); if (frame==null) return;
        if (frame.menu!=menu || frame.player!=player) throw new IllegalStateException("CRAFT_CAPTURE_IDENTITY");
        JsonObject value=base(frame);
        value.addProperty("same_menu",menu==player.containerMenu);
        value.addProperty("nested",frame.nested);
        value.addProperty("callback_count",frame.callbacks);
        value.add("callback",frame.callback==null?JsonNull.INSTANCE:frame.callback);
        value.add("state",state(menu));
        emit(frame,"craft_end","strata/CraftEnd/1",value);
    }
    static void callback(ServerPlayer player, ItemStack output, Container grid) {
        if (!active(player)) return;
        var stack=frames.get();
        // Private bounded type diagnosis for unsupported native menu variants.
        var menu=player.containerMenu;var slot=menu.slots.isEmpty()?null:menu.slots.get(0);
        var recipe=slot!=null && slot.container instanceof ResultContainer r?r.getRecipeUsed():null;
        System.getLogger(CraftCapture.class.getName()).log(System.Logger.Level.INFO,
            "STRATA_CRAFT_CAPTURE menu="+menu.getClass().getName()+" slot="+(slot==null?"none":slot.getClass().getName())
            +" recipe="+(recipe==null?"none":recipe.getClass().getName())+" pending="+(!stack.isEmpty() && stack.get(stack.size()-1)!=null));
        if (stack.isEmpty()) return;
        var frame=stack.get(stack.size()-1); if (frame==null) return;
        if (frame.player!=player) { frame.nested=true; return; }
        frame.callbacks++;
        if (frame.callbacks>1) return;
        if (grid.getContainerSize()>9) throw new IllegalStateException("CRAFT_CAPTURE_GRID");
        var value=new JsonObject(); value.add("output",item(output)); var rows=new JsonArray();
        for(int i=0;i<grid.getContainerSize();i++) rows.add(item(grid.getItem(i)));
        value.add("grid",rows); frame.callback=value;
    }
    private static JsonObject base(Frame frame) {
        var value=new JsonObject(); value.addProperty("transaction_id",frame.id);
        value.addProperty("policy",POLICY); value.addProperty("container_id",frame.menu.containerId);
        value.addProperty("score_eligible",false); return value;
    }
    private static void emit(Frame frame,String kind,String schema,JsonObject value) {
        var actors=new JsonArray(); actors.add(frame.player.getUUID().toString());
        sink.emit("setup_snapshot","strata/NativeSetupSnapshot/1",
            SetupCapture.capture(frame.player.getServer(),frame.player,frame.id,kind),actors);
        sink.emit(kind,schema,value,actors);
    }
    private static JsonObject state(AbstractContainerMenu menu) {
        if (menu.slots.size()!=46) throw new IllegalStateException("CRAFT_CAPTURE_SLOTS");
        var value=new JsonObject(); var slots=new JsonArray();
        for(var slot:menu.slots) slots.add(item(slot.getItem()));
        value.add("slots",slots); value.add("cursor",item(menu.getCarried())); return value;
    }
    private static JsonObject item(ItemStack item) {
        var value=new JsonObject();
        value.addProperty("item_id",item.isEmpty()?"minecraft:air":ForgeRegistries.ITEMS.getKey(item.getItem()).toString());
        value.addProperty("count",item.isEmpty()?0:item.getCount());
        var tag=item.isEmpty()?new CompoundTag():item.save(new CompoundTag()); tag.remove("id"); tag.remove("Count");
        byte[] bytes=tag.toString().getBytes(StandardCharsets.UTF_8);
        if(bytes.length>16384 || item.getCount()>64) throw new IllegalStateException("CRAFT_CAPTURE_STACK");
        try { value.addProperty("components_sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
        catch(java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        value.addProperty("components_empty",tag.isEmpty()); return value;
    }
    private CraftCapture() {}
}
