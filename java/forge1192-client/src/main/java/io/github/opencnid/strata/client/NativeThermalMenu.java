package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraftforge.fluids.FluidStack;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.registries.ForgeRegistries;

/** Optional exact-pack bridge. Fixed public mod members only; no reflective agent API.
 * The names are mod-owned, not obfuscated Minecraft members. The installed JARs
 * supply them; the enclosing body fingerprint already hashes those JARs.
 */
final class NativeThermalMenu {
    record Display(JsonObject machine, List<Integer> slots) {}
    static boolean known(AbstractContainerMenu menu) {
        for (var kind : GameMachineMenu.Kind.values()) if (kind.menuClass().equals(menu.getClass().getName())) return true;
        return false;
    }
    static GameMachineInventory.Layout layout(AbstractContainerMenu menu) throws IOException {
        var kind = GameMachineMenu.kind(menu.getClass().getName());
        int augments = number(menu, "getNumAugmentSlots");
        GameMachineMenu.visibleSlots(kind, augments, menu.slots.size());
        return new GameMachineInventory.Layout(kind, augments);
    }
    static Display read(Minecraft client, AbstractContainerMenu menu, Map<String, String> loadedArtifacts) throws IOException {
        if (!client.isSameThread()) throw new IOException("GAME_CLIENT_THREAD_REQUIRED");
        var kind = GameMachineMenu.kind(menu.getClass().getName());
        GameMachineMenu.requireArtifacts(loadedArtifacts);
        // mods.toml deliberately omits the build suffix; byte pins retain it.
        requireVersion("thermal_expansion", "10.3.1");
        requireVersion("thermal", "10.3.0");
        requireVersion("cofh_core", "10.3.1");
        var player = client.player; var level = client.level; var screen = client.screen;
        if (player == null || level == null || player.containerMenu != menu
                || screen == null || !screen.getClass().getName().equals(kind.screenClass())
                || !(screen instanceof AbstractContainerScreen<?> container) || container.getMenu() != menu)
            throw new IOException("GAME_CONTAINER_NOT_OPEN");
        var menuId = ForgeRegistries.MENU_TYPES.getKey(menu.getType());
        if (menuId == null || !kind.id.equals(menuId.toString())) throw unsupported();
        final Object tile;
        try { tile = menu.getClass().getField("tile").get(menu); }
        catch (ReflectiveOperationException | SecurityException failure) { throw unsupported(); }
        if (tile == null || !tile.getClass().getName().equals(kind.tileClass()) || !(tile instanceof BlockEntity block)
                || block.getLevel() != level || block.isRemoved()) throw unsupported();
        int augments = number(menu, "getNumAugmentSlots");
        var visible = GameMachineMenu.visibleSlots(kind, augments, menu.slots.size());
        // Check the known base/augment/player layout without reading hidden stacks.
        for (int i = 0; i < menu.slots.size(); i++) {
            var slot = menu.slots.get(i);
            if (kind == GameMachineMenu.Kind.FURNACE && i == 1) {
                if (slot.getClass() != net.minecraft.world.inventory.FurnaceResultSlot.class) throw unsupported();
            } else if (i < kind.baseSlots + augments) {
                if (!slot.getClass().getName().equals("cofh.lib.inventory.container.slot.SlotCoFH")) throw unsupported();
            } else if (slot.getClass() != net.minecraft.world.inventory.Slot.class || slot.container != player.getInventory()) throw unsupported();
        }
        var machine = GameMachineMenu.read(kind, new GameMachineMenu.Source() {
            public void validate() throws IOException {
                if (!client.isSameThread() || client.player != player || client.level != level || client.screen != screen
                        || player.containerMenu != menu || block.isRemoved() || block.getLevel() != level)
                    throw new IOException("REVISION_CONFLICT");
            }
            public GameMachineMenu.Energy energy() throws IOException {
                Object energy = call(tile, "getEnergyStorage");
                exact(energy, "cofh.lib.energy.EnergyStorageCoFH");
                return new GameMachineMenu.Energy(number(energy, "getEnergyStored"), number(energy, "getMaxEnergyStored"));
            }
            public GameMachineMenu.Fluid fluid() throws IOException {
                final Object tank;
                try { tank = tile.getClass().getMethod("getTank", int.class).invoke(tile, 0); }
                catch (ReflectiveOperationException | SecurityException failure) { throw unsupported(); }
                exact(tank, "cofh.lib.fluid.FluidStorageCoFH");
                Object value = call(tank, "getFluidStack");
                if (!(value instanceof FluidStack fluid)) throw unsupported();
                var id = fluid.isEmpty() ? null : ForgeRegistries.FLUIDS.getKey(fluid.getFluid());
                if (!fluid.isEmpty() && id == null) throw unsupported();
                return new GameMachineMenu.Fluid(id == null ? null : id.toString(), fluid.isEmpty() ? 0 : fluid.getAmount(),
                    number(tank, "getCapacity"), fluid.hasTag());
            }
        });
        return new Display(machine, visible);
    }
    private static void requireVersion(String id, String version) throws IOException {
        var mod = ModList.get().getModContainerById(id);
        if (mod.isEmpty() || !version.equals(mod.get().getModInfo().getVersion().toString())) throw unsupported();
    }
    private static void exact(Object value, String type) throws IOException {
        if (value == null || !value.getClass().getName().equals(type)) throw unsupported();
    }
    private static Object call(Object target, String member) throws IOException {
        try { return target.getClass().getMethod(member).invoke(target); }
        catch (ReflectiveOperationException | SecurityException failure) { throw unsupported(); }
    }
    private static int number(Object target, String member) throws IOException {
        Object value = call(target, member);
        if (!(value instanceof Integer number)) throw unsupported();
        return number;
    }
    private static IOException unsupported() { return new IOException("GAME_MACHINE_DISPLAY_UNSUPPORTED"); }
}
