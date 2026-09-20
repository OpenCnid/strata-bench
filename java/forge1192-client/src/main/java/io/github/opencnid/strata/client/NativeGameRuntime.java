package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Set;
import java.util.TreeMap;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.Connection;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.inventory.FurnaceMenu;
import net.minecraft.world.inventory.InventoryMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.client.ForgeHooksClient;
import net.minecraftforge.client.event.InputEvent;
import net.minecraftforge.registries.ForgeRegistries;

/** Reads registered objects on the client thread; no raw NBT, seed or block-entity exports. */
final class NativeGameRuntime implements NativeGameProtocol.RuntimePort, GameActionLane.RuntimePort {
    private static final Set<Class<?>> MENUS = Set.of(InventoryMenu.class, ChestMenu.class, FurnaceMenu.class, CraftingMenu.class);
    private final Minecraft client;
    private final GamePages pages = new GamePages();
    private final GameObservedMap<net.minecraft.world.level.block.state.BlockState> observed = new GameObservedMap<>();
    private Object levelIdentity, playerIdentity;
    private final String fingerprint;
    private final java.util.Map<String, String> loadedArtifacts;
    private String windowDigest;
    private Object windowIdentity;
    private long windowRevision;
    private long generation, lastCapturedRevision;
    private String activeRequest;
    private String entitySalt = UUID.randomUUID().toString();
    private boolean ownedUse, permittedUseEvent;
    private boolean ownedMovement, expectedForward;
    private Connection menuConnection;
    private NativeWindowSync windowSync;
    private final NativeRecipes recipes;
    private final NativeQuests quests;

    NativeGameRuntime(Minecraft client) throws IOException {
        this.client = client;
        this.recipes = new NativeRecipes(client);
        this.quests = new NativeQuests(client);
        requireClientThread();
        var artifacts = new TreeMap<String, String>();
        for (var file : ModList.get().getModFiles()) {
            var path = file.getFile().getFilePath();
            if (artifacts.put(path.getFileName().toString(), NativeSettingsRuntime.fileHash(path)) != null) {
                throw new IOException("GAME_ARTIFACT_AMBIGUOUS");
            }
        }
        JsonObject identity = new JsonObject();
        loadedArtifacts = java.util.Map.copyOf(artifacts);
        identity.add("loaded_mod_artifacts", SettingsJson.strings(artifacts));
        identity.addProperty("artifact_hash_policy", ArtifactFiles.POLICY);
        identity.addProperty("java_runtime", System.getProperty("java.runtime.version"));
        identity.addProperty("os", System.getProperty("os.name") + ":" + System.getProperty("os.arch"));
        identity.add("capabilities", NativeGameProtocol.capabilities());
        fingerprint = KeyOptions.sha256(identity.toString());
    }
    String fingerprint() { return fingerprint; }
    public void requireClientThread() throws IOException {
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
    }

    /** Also called between requests so reconnect/respawn invalidates captured pages. */
    void tick() throws IOException {
        requireClientThread();
        quests.tick();
        Connection connection = client.getConnection() == null ? null : client.getConnection().getConnection();
        boolean connectionChanged = connection != menuConnection;
        if (connectionChanged) {
            if (windowSync != null) windowSync.close();
            windowSync = null; menuConnection = connection;
            if (connection != null) windowSync = new NativeWindowSync(client, connection);
        }
        if (connectionChanged || levelIdentity != client.level || playerIdentity != client.player) {
            resetObservations(); windowIdentity = null; windowDigest = null;
            levelIdentity = client.level; playerIdentity = client.player;
            generation++;
        }
    }

    public JsonObject observe(String cursor) throws IOException {
        tick();
        bodyFingerprint();
        String dimension = name(client.level.dimension().location());
        if (cursor != null) return pages.page(cursor, dimension);
        long captureStarted = pages.beginCapture();
        var player = client.player;
        var eye = point(player.getEyePosition());
        String capturedAt = GamePages.utc(Instant.now());
        JsonObject state = coreState();
        JsonArray blocks = new JsonArray();
        var capturedCells = new java.util.LinkedHashMap<GameObservedMap.Position,
            GameObservedMap.Cell<net.minecraft.world.level.block.state.BlockState>>();
        for (var cell : GameVisibility.capture(eye, this::readCell)) {
            JsonObject block = new JsonObject();
            block.add("position", vector(new Vec3(cell.x(), cell.y(), cell.z())));
            block.addProperty("block_id", cell.id()); block.addProperty("observed_at", capturedAt);
            blocks.add(block);
            var position = new BlockPos(cell.x(), cell.y(), cell.z());
            var nativeState = client.level.getBlockState(position);
            if (!cell.id().equals(name(ForgeRegistries.BLOCKS.getKey(nativeState.getBlock())))) {
                throw new IOException("REVISION_CONFLICT");
            }
            capturedCells.put(new GameObservedMap.Position(cell.x(), cell.y(), cell.z()),
                new GameObservedMap.Cell<>(cell.id(), nativeState));
        }
        var visible = new ArrayList<Entity>();
        int inspected = 0;
        for (Entity entity : client.level.entitiesForRendering()) {
            if (++inspected > 16384) throw new IOException("GAME_SCENE_CAPACITY");
            if (entity == player || entity.isRemoved() || entity.isInvisibleTo(player)) continue;
            if (eye.distance(point(entity.position())) > 16) continue;
            Vec3 target = entity.position().add(0, Math.min(entity.getBbHeight() / 2, 1), 0);
            if (GameVisibility.visible(eye, point(target), this::readCell)) visible.add(entity);
        }
        visible.sort(Comparator.comparingDouble((Entity entity) -> entity.distanceToSqr(player)).thenComparingInt(Entity::getId));
        JsonArray entities = new JsonArray();
        for (Entity entity : visible) {
            JsonObject item = new JsonObject();
            item.addProperty("id", entityId(entity));
            item.addProperty("type", name(ForgeRegistries.ENTITY_TYPES.getKey(entity.getType())));
            item.add("position", vector(entity.position())); item.addProperty("observed_at", capturedAt);
            entities.add(item);
        }
        JsonObject result = pages.capture(state, blocks, entities, captureStarted, inputFence());
        observed.remember(SettingsJson.string(result, "snapshot_id"), dimension,
            SettingsJson.integer(result, "captured_elapsed_ms"),
            SettingsJson.integer(result, "state_revision"), capturedCells);
        lastCapturedRevision = SettingsJson.integer(result, "state_revision");
        return result;
    }

    public JsonObject recipes(int after) throws IOException { tick(); return recipes.page(after); }
    public JsonObject quests(GameQuestCatalog.Query query) throws IOException { tick(); return quests.page(query,loadedArtifacts); }
    public JsonObject questText(GameQuestText.Query query) throws IOException { tick(); return quests.text(query,loadedArtifacts); }
    public JsonObject questComponents(GameQuestComponents.Query query) throws IOException {tick();return quests.components(query,loadedArtifacts);}
    public JsonObject questMenu(GameQuestMenu.Query query)throws IOException {tick();return quests.menu(query,loadedArtifacts);}
    public JsonObject questScreen()throws IOException {tick();return quests.screen(loadedArtifacts);}
    public JsonObject recipePage()throws IOException {tick();return quests.recipePage(loadedArtifacts);}
    public JsonObject recipeQuery(GameRecipeQuery.Query query) throws IOException {
        tick();
        if (!net.minecraftforge.fml.ModList.get().isLoaded("jei")) throw new IOException("CAPABILITY_MISSING");
        return JeiRecipePlugin.query(query, loadedArtifacts);
    }

    private JsonObject coreState() throws IOException {
        var player = client.player;
        JsonObject state = new JsonObject();
        state.addProperty("dimension", name(client.level.dimension().location()));
        state.add("position", vector(player.position()));
        // Match the existing Mineflayer radians convention, not Minecraft's degree axes.
        double turn = 2 * Math.PI;
        state.addProperty("yaw", (Math.toRadians(180 - player.getYRot()) % turn + turn) % turn);
        state.addProperty("pitch", ((Math.toRadians(-player.getXRot()) + Math.PI) % turn + turn) % turn - Math.PI);
        state.addProperty("health", player.getHealth());
        state.addProperty("food", player.getFoodData().getFoodLevel());
        if (player.inventoryMenu.getClass() != InventoryMenu.class || player.inventoryMenu.slots.size() != 46) {
            throw new IOException("GAME_INVENTORY_UNSUPPORTED");
        }
        state.add("inventory", slots(player.inventoryMenu));
        state.add("window", window(player.containerMenu));
        state.addProperty("active_request_id", activeRequest);
        state.addProperty("connected", true);
        return state;
    }

    public long connectionGeneration() { return generation; }
    public String bodyFingerprint() throws IOException {
        requireClientThread();
        if (client.level == null || client.player == null || client.getConnection() == null) {
            throw new IOException("GAME_NOT_CONNECTED");
        }
        if (!ClientGameBridge.bodyReady(client)) throw new IOException("GAME_INITIAL_SYNC_PENDING");
        // Private binding only: no account ID/address is returned by the gameplay state.
        String endpoint = GameBodyEndpoint.endpoint(client.getCurrentServer() == null ? null : client.getCurrentServer().ip,
            client.getConnection().getConnection().getRemoteAddress());
        return KeyOptions.sha256(endpoint + "\n" + client.player.getStringUUID());
    }
    public void resetObservations() throws IOException {
        requireClientThread(); pages.reset(); observed.reset(); lastCapturedRevision = 0; entitySalt = UUID.randomUUID().toString();
    }
    public void delivered(JsonObject snapshot) throws IOException {
        requireClientThread();
        String dimension = SettingsJson.string(snapshot.getAsJsonObject("state"), "dimension");
        observed.deliver(pages.sceneId(SettingsJson.string(snapshot, "snapshot_id"), dimension), snapshot);
    }
    /** Planning has no raw Level access: only already-delivered states enter the collision view. */
    java.util.List<GameVisibility.Point> planMove(GameVisibility.Point target, double tolerance) throws IOException {
        tick(); movementContext();
        var collision = new NativeCollisionView(observed.snapshot(), pages.elapsed());
        return new GameRoute(collision, client.player.getBbWidth(), client.player.getBbHeight())
            .plan(point(client.player.position()), target, tolerance);
    }
    private void movementContext() throws IOException {
        gameplay(false);
        if (client.player.getPose() != net.minecraft.world.entity.Pose.STANDING || !client.player.isOnGround()
                || client.player.isPassenger() || client.player.isInWater() || client.player.isInLava()
                || client.player.getAbilities().flying || client.player.isSprinting() || client.player.isUsingItem()
                || client.gameMode.isDestroying() || client.player.input.getClass() != net.minecraft.client.player.KeyboardInput.class
                || client.options.keyUp.getClass() != KeyMapping.class) {
            throw new IOException("NAVIGATION_CONTEXT_UNSUPPORTED");
        }
        if (client.options.autoJump().get() || client.options.toggleSprint().get() || client.options.toggleCrouch().get()) {
            throw new IOException("NAVIGATION_SETTINGS_UNSUPPORTED");
        }
        for (KeyMapping mapping : client.options.keyMappings) {
            if (mapping == client.options.keyUp) {
                if (mapping.isDown() != (ownedMovement && expectedForward)) throw new IOException("NAVIGATION_INPUT_CHANGED");
            } else if (mapping.isDown()) throw new IOException("NAVIGATION_INPUT_CHANGED");
        }
    }
    private GameMovement.Port movementPort() {
        final var inputIdentity = client.player.input;
        final float width = client.player.getBbWidth(), height = client.player.getBbHeight();
        return new GameMovement.Port() {
            public GameMovement.Frame read() throws IOException {
                movementContext();
                var input = client.player.input;
                if (input != inputIdentity || client.player.getBbWidth() != width || client.player.getBbHeight() != height
                        || input.up != (ownedMovement && expectedForward) || input.down || input.left || input.right
                        || input.jumping || input.shiftKeyDown || input.leftImpulse != 0
                        || input.forwardImpulse != (ownedMovement && expectedForward ? 1 : 0)) {
                    throw new IOException("NAVIGATION_INPUT_CHANGED");
                }
                JsonObject context = new JsonObject();
                context.add("inventory", slots(client.player.inventoryMenu)); context.add("window", window(client.player.containerMenu));
                context.addProperty("food", client.player.getFoodData().getFoodLevel()); context.addProperty("selected", inputFence());
                return new GameMovement.Frame(client.player.tickCount, point(client.player.position()), point(client.player.getDeltaMovement()),
                    client.player.getHealth(), client.player.getAbsorptionAmount(),
                    client.player.hurtTime > 0 || client.player.horizontalCollision, KeyOptions.sha256(context.toString()));
            }
            public void corridor(GameVisibility.Point from, GameVisibility.Point to) throws IOException {
                new GameRoute(new NativeCollisionView(observed.snapshot(), pages.elapsed()), width, height).requireCorridor(from, to);
            }
            public void controls(double yaw, boolean forward) throws IOException {
                movementContext();
                client.player.setYRot((float) yaw);
                ownedMovement = true; expectedForward = forward; client.options.keyUp.setDown(forward);
            }
        };
    }
    public void activeRequest(String id) { activeRequest = id; }
    public JsonObject snapshot(String id) throws IOException { return observe(id); }
    private String inputFence() { return "selected-slot:" + client.player.getInventory().selected; }
    private String entityId(Entity entity) { return GameGestures.entityId(entity.getId(), entity.getStringUUID(), entitySalt); }

    void onInput(InputEvent.InteractionKeyMappingTriggered event) {
        // The native held-key polling loop may try to start a second use between
        // motor ticks. Only this request's explicit initial trigger is allowed.
        if (ownedUse && !permittedUseEvent && event.isUseItem()) {
            event.setCanceled(true); event.setSwingHand(false);
        }
    }

    private void gameplay(boolean inventory) throws IOException {
        requireClientThread(); bodyFingerprint();
        if (client.gameMode == null || client.gameMode.getPlayerMode() != GameType.SURVIVAL || !client.player.isAlive()) {
            throw new IOException("GAME_SURVIVAL_CONTEXT_REQUIRED");
        }
        if (!inventory && client.screen != null) throw new IOException("GAME_SCREEN_OPEN");
    }
    public void validate(GameBatch batch, JsonObject snapshot) throws IOException {
        gameplay(Set.of("click_slot", "equip", "craft", "close_window", "quest_navigate", "quest_task", "quest_menu", "quest_reward", "recipe_navigate").contains(batch.kind));
        if (windowSync != null && windowSync.uncertain()) throw new IOException("GAME_MENU_RESYNC_REQUIRED");
        if (batch.revision != lastCapturedRevision || SettingsJson.integer(snapshot, "state_revision") != batch.revision) {
            throw new IOException("REVISION_CONFLICT");
        }
        JsonObject expected = snapshot.getAsJsonObject("state"), current = coreState();
        pages.requireInputFence(SettingsJson.string(snapshot, "snapshot_id"),
            SettingsJson.string(current, "dimension"), inputFence());
        for (String field : Set.of("dimension", "position", "yaw", "pitch", "health", "food", "inventory", "window")) {
            boolean same = field.equals("window")
                ? GameMachineMenu.inputWindow(current.getAsJsonObject(field)).equals(GameMachineMenu.inputWindow(expected.getAsJsonObject(field)))
                : current.get(field).equals(expected.get(field));
            if (!same) throw new IOException("REVISION_CONFLICT");
        }
        if (Set.of("dig", "interact_block").contains(batch.kind)) {
            var target = GameBatch.target(batch.action);
            BlockPos pos = new BlockPos(target.x(), target.y(), target.z());
            String expectedId = SettingsJson.string(batch.action, "expected_block_id");
            boolean delivered = false;
            for (var value : expected.getAsJsonArray("nearby_blocks")) {
                JsonObject block = value.getAsJsonObject(), p = block.getAsJsonObject("position");
                if (p.get("x").getAsDouble() == pos.getX() && p.get("y").getAsDouble() == pos.getY()
                        && p.get("z").getAsDouble() == pos.getZ() && expectedId.equals(block.get("block_id").getAsString())) delivered = true;
            }
            if (!delivered) throw new IOException("TARGET_NOT_OBSERVED");
            blockHit(batch);
        } else if (batch.kind.equals("move_to")) {
            movementContext();
        } else if (batch.kind.equals("quest_ui")) {
            GameQuestOpen.validate(questOpenPort(),GameQuestOpen.Request.read(batch.action));
        } else if (batch.kind.equals("quest_navigate")) {
            GameQuestNavigation.validate(quests.navigationPort(loadedArtifacts,this::questInputContext),GameQuestNavigation.Request.read(batch.action));
        } else if (batch.kind.equals("recipe_navigate")) {
            GameRecipeNavigation.validate(quests.recipeNavigationPort(loadedArtifacts,this::questInputContext),GameRecipeNavigation.Request.read(batch.action));
        } else if (batch.kind.equals("quest_menu")) {
            GameQuestMenuAction.validate(quests.menuActionPort(loadedArtifacts,this::questInputContext),GameQuestMenuAction.Request.read(batch.action));
        } else if (batch.kind.equals("quest_reward")) {
            GameQuestRewardOpen.validate(quests.rewardOpenPort(loadedArtifacts,this::questInputContext),GameQuestRewardOpen.Request.read(batch.action));
        } else if (batch.kind.equals("quest_task")) {
            GameQuestTaskOpen.validate(quests.taskOpenPort(loadedArtifacts,this::questInputContext),GameQuestTaskOpen.Request.read(batch.action));
        } else if (batch.kind.equals("place")) {
            placeHit(batch, snapshot);
        } else if (batch.kind.equals("equip")) {
            var port = inventoryPort(true); port.validate();
            int source = Math.toIntExact(SettingsJson.integer(batch.action, "inventory_slot"));
            if (source < 5 || !client.player.containerMenu.getCarried().isEmpty()
                    || !inventoryStack(client.player.inventoryMenu.slots.get(source).getItem()).id()
                        .equals(SettingsJson.string(batch.action, "expected_item_id"))) throw new IOException("PRECONDITION_FAILED");
        } else if (Set.of("attack", "interact_entity").contains(batch.kind)) {
            String id = SettingsJson.string(batch.action, "entity_id");
            entityHit(id, GameGestures.deliveredEntity(snapshot, id), batch.kind.equals("attack"));
        } else if (batch.kind.equals("use_item")) {
            useContext();
            if (client.player.isUsingItem()) throw new IOException("GAME_USE_IN_PROGRESS");
        } else if (Set.of("click_slot", "craft", "close_window").contains(batch.kind)) {
            inventoryPort(false).validate();
            JsonObject window = current.getAsJsonObject("window");
            if (window.get("id").getAsLong() != SettingsJson.integer(batch.action, "window_id")
                    || window.get("revision").getAsLong() != SettingsJson.integer(batch.action, "expected_window_revision")
                    || batch.kind.equals("click_slot") && SettingsJson.integer(batch.action, "slot") >= client.player.containerMenu.slots.size()) throw new IOException("REVISION_CONFLICT");
            if (batch.kind.equals("craft")) craftingPort(batch).validate();
            if (batch.kind.equals("close_window")) closePort().validate();
        }
    }
    private BlockHitResult placeHit(GameBatch batch, JsonObject snapshot) throws IOException {
        var observed = GamePlacement.observed(snapshot, batch.action);
        useContext();
        if (client.player.isUsingItem()) throw new IOException("GAME_USE_IN_PROGRESS");
        ItemStack held = client.player.getMainHandItem();
        if (held.isEmpty() || !(held.getItem() instanceof BlockItem)) throw new IOException("MECHANIC_UNSUPPORTED");
        if (!name(ForgeRegistries.ITEMS.getKey(held.getItem())).equals(SettingsJson.string(batch.action, "expected_item_id"))) {
            throw new IOException("PRECONDITION_FAILED");
        }
        var support = GameBatch.vector(batch.action, "support"); var face = GameBatch.vector(batch.action, "face");
        var pos = new BlockPos(support.x(), support.y(), support.z());
        var direction = Direction.getNearest(face.x(), face.y(), face.z()); var target = pos.relative(direction);
        var supportCell = readCell(pos.getX(), pos.getY(), pos.getZ());
        var targetCell = readCell(target.getX(), target.getY(), target.getZ());
        if (supportCell == null || supportCell.air() || !observed.supportId().equals(supportCell.id()) || targetCell == null
                || !targetCell.air() || !observed.destinationId().equals(targetCell.id())) throw new IOException("PRECONDITION_FAILED");
        if (!client.player.canInteractWith(pos, 0)) throw new IOException("OUT_OF_REACH");
        Vec3 aim = Vec3.atCenterOf(pos).add(face.x() * .4999, face.y() * .4999, face.z() * .4999);
        var hit = client.level.clip(new ClipContext(client.player.getEyePosition(), aim, ClipContext.Block.OUTLINE,
            ClipContext.Fluid.NONE, client.player));
        if (hit.getType() != HitResult.Type.BLOCK || !hit.getBlockPos().equals(pos) || hit.getDirection() != direction) {
            throw new IOException("TARGET_OCCLUDED");
        }
        return hit;
    }
    static int resultSlot(AbstractContainerMenu menu) { return menu instanceof InventoryMenu || menu instanceof CraftingMenu ? 0 : -1; }
    static GameInventory.Stack inventoryStack(ItemStack item) throws IOException {
        if (item.isEmpty()) return GameInventory.Stack.EMPTY;
        var serialized = item.save(new net.minecraft.nbt.CompoundTag());
        serialized.remove("id"); serialized.remove("Count");
        String components = serialized.toString(); // Includes Forge capabilities, privately; never exported.
        if (components.length() > 16384) throw new IOException("GAME_ITEM_COMPONENTS_UNSUPPORTED");
        return new GameInventory.Stack(name(ForgeRegistries.ITEMS.getKey(item.getItem())), item.getCount(), KeyOptions.sha256(components));
    }
    static GameInventory.View inventoryView(AbstractContainerMenu menu) throws IOException {
        return inventoryView(menu, i -> menu.slots.get(i).getItem(), menu.getCarried());
    }
    static GameInventory.View inventoryView(AbstractContainerMenu menu, java.util.List<ItemStack> items, ItemStack cursor) throws IOException {
        if (items.size() != menu.slots.size()) throw new IOException("GAME_CONTAINER_UNSUPPORTED");
        return inventoryView(menu, items::get, cursor);
    }
    private static GameInventory.View inventoryView(AbstractContainerMenu menu, java.util.function.IntFunction<ItemStack> item,
                                                    ItemStack cursor) throws IOException {
        if (menu.slots.size() > 1024) throw new IOException("GAME_CONTAINER_UNSUPPORTED");
        var machine = NativeThermalMenu.known(menu) ? NativeThermalMenu.layout(menu) : null;
        if (machine != null) {
            for (int i = 0; i < machine.total(); i++)
                if (machine.visible(i) && !menu.slots.get(i).isActive()) throw new IOException("GAME_CONTAINER_UNSUPPORTED");
            return GameMachineInventory.project(machine, i -> inventoryStack(item.apply(i)), inventoryStack(cursor));
        }
        var slots = new ArrayList<GameInventory.Stack>();
        for (int i = 0; i < menu.slots.size(); i++) {
            slots.add(inventoryStack(item.apply(i)));
        }
        return new GameInventory.View(slots, inventoryStack(cursor), resultSlot(menu));
    }
    private GameInventory.Port inventoryPort(boolean playerOnly) throws IOException {
        final AbstractContainerMenu menu = client.player.containerMenu;
        final int selected = client.player.getInventory().selected;
        final var machine = NativeThermalMenu.known(menu) ? NativeThermalMenu.layout(menu) : null;
        return new GameInventory.Port() {
            public void validate() throws IOException {
                gameplay(true);
                if (windowSync == null) throw new IOException("GAME_MENU_SYNC_UNAVAILABLE");
                windowSync.requireReady();
                if (client.player.containerMenu != menu || client.player.getInventory().selected != selected
                        || playerOnly && menu != client.player.inventoryMenu) throw new IOException("REVISION_CONFLICT");
                window(menu); // Exact supported native menu class and actually displayed container.
                if (machine != null && !machine.equals(NativeThermalMenu.layout(menu))) throw new IOException("REVISION_CONFLICT");
            }
            public GameInventory.View view() throws IOException {
                validate(); return inventoryView(menu);
            }
            private ItemStack nativeItem(GameInventory.Stack stack) throws IOException {
                if (inventoryStack(menu.getCarried()).equals(stack)) return menu.getCarried();
                for (int i = 0; i < menu.slots.size(); i++) {
                    if (machine != null && !machine.visible(i)) continue;
                    var slot = menu.slots.get(i);
                    if (inventoryStack(slot.getItem()).equals(stack)) return slot.getItem();
                }
                throw new IOException("REVISION_CONFLICT");
            }
            public int capacity(int slot, GameInventory.Stack stack) throws IOException {
                ItemStack item = nativeItem(stack); return Math.min(item.getMaxStackSize(), menu.slots.get(slot).getMaxStackSize(item));
            }
            public boolean mayPickup(int slot) { return menu.slots.get(slot).mayPickup(client.player); }
            public boolean mayPlace(int slot, GameInventory.Stack stack) throws IOException { return menu.slots.get(slot).mayPlace(nativeItem(stack)); }
            public void click(int slot, int button, boolean quick) throws IOException {
                validate(); requireInventoryMotor(menu, slot, quick); windowSync.markDirty(menu); client.gameMode.handleInventoryMouseClick(menu.containerId, slot, button,
                    quick ? ClickType.QUICK_MOVE : ClickType.PICKUP, client.player);
            }
            public long requestSync() throws IOException { validate(); return windowSync.request(menu); }
            public GameInventory.View reply(long ticket) throws IOException { validate(); return windowSync.reply(ticket, menu); }
        };
    }
    private GameMenuClose.Port closePort() throws IOException {
        var base = inventoryPort(false); base.validate();
        var menu = client.player.containerMenu; var inventory = client.player.inventoryMenu;
        var screen = client.screen; int selected = client.player.getInventory().selected;
        var items = new ArrayList<ItemStack>();
        for (var slot : inventory.slots) items.add(slot.getItem().copy());
        // Machine close only returns the carried stack; its contents need not
        // be inspected to establish capacity in the player's own inventory.
        if (!NativeThermalMenu.known(menu)) for (var slot : menu.slots) items.add(slot.getItem().copy());
        items.add(menu.getCarried().copy());
        return new GameMenuClose.Port() {
            boolean closed;
            public void validate() throws IOException {
                gameplay(true);
                if (client.player.inventoryMenu != inventory || client.player.getInventory().selected != selected) throw new IOException("REVISION_CONFLICT");
                if (!closed) {
                    base.validate();
                    if (client.screen != screen || screen != null && (!(screen instanceof AbstractContainerScreen<?> current)
                            || current.getMenu() != menu)) throw new IOException("GAME_CONTAINER_NOT_OPEN");
                } else if (client.player.containerMenu != inventory || client.screen != null) throw new IOException("REVISION_CONFLICT");
                windowSync.requireReady();
            }
            private GameMenuClose.State inventoryState(GameInventory.View view) throws IOException {
                if (view.slots().size() != 46) throw new IOException("GAME_INVENTORY_UNSUPPORTED");
                var returning = new ArrayList<>(view.slots().subList(1, 5)); returning.add(view.cursor());
                return new GameMenuClose.State(view.slots().subList(5, 46), returning);
            }
            public GameMenuClose.State read() throws IOException {
                validate(); var state = inventoryState(inventoryView(inventory));
                if (closed || menu == inventory) return state;
                if (state.returning().stream().anyMatch(item -> !item.empty())) throw new IOException("GAME_INVENTORY_UNSUPPORTED");
                var returning = new ArrayList<GameInventory.Stack>();
                if (menu instanceof CraftingMenu) for (int i = 1; i <= 9; i++) returning.add(inventoryStack(menu.slots.get(i).getItem()));
                returning.add(inventoryStack(menu.getCarried()));
                return new GameMenuClose.State(state.inventory(), returning);
            }
            public int capacity(int slot, GameInventory.Stack stack) throws IOException {
                for (var item : items) if (inventoryStack(item).same(stack)) {
                    var destination = inventory.slots.get(slot + 5);
                    return destination.mayPlace(item) ? Math.min(item.getMaxStackSize(), destination.getMaxStackSize(item)) : 0;
                }
                throw new IOException("REVISION_CONFLICT");
            }
            public void close() throws IOException {
                validate(); windowSync.markDirty(inventory);
                if (screen != null) screen.onClose(); else client.player.closeContainer();
                closed = true; validate();
            }
            public long requestSync() throws IOException { validate(); return windowSync.request(inventory); }
            public GameMenuClose.State reply(long ticket) throws IOException {
                validate(); var view = windowSync.reply(ticket, inventory); return view == null ? null : inventoryState(view);
            }
        };
    }
    private GameCrafting.Port craftingPort(GameBatch batch) throws IOException {
        String id = SettingsJson.string(batch.action,"recipe_id");
        var rawSelection=batch.action.get("recipe_selection");
        final GameRecipeSelection selection=rawSelection == null || rawSelection.isJsonNull() ? null
            : GameRecipeSelection.read(rawSelection.getAsJsonObject());
        var base = inventoryPort(false); base.validate();
        var current = client.player.containerMenu;
        if (current.getClass() != InventoryMenu.class && current.getClass() != CraftingMenu.class) throw new IOException("MECHANIC_UNSUPPORTED");
        var menu = (net.minecraft.world.inventory.RecipeBookMenu<?>) current;
        // Player-visible source must authorize the ID before reading the manager entry.
        final JsonObject visible = selection == null ? null : selection.definition(recipeQuery(selection.query()),id,true);
        var recipe = selection == null ? recipes.resolve(id) : client.getConnection().getRecipeManager()
            .byKey(new net.minecraft.resources.ResourceLocation(id)).orElseThrow(() -> new IOException("GAME_RECIPE_CHANGED"));
        var original = NativeRecipes.definition(recipe);
        if (visible != null && !visible.equals(original)) throw new IOException("GAME_RECIPE_CHANGED");
        if (!recipe.canCraftInDimensions(menu.getGridWidth(), menu.getGridHeight())) throw new IOException("PRECONDITION_FAILED");
        var output = recipe.getResultItem().copy(); var identity = inventoryStack(output);
        var nativeItems = new java.util.HashMap<GameInventory.Stack, ItemStack>(); nativeItems.put(identity, output);
        return new GameCrafting.Port() {
            public void validate() throws IOException {
                base.validate();
                if (selection == null) recipes.validate(recipe, original);
                else if (!selection.definition(recipeQuery(selection.query()),id,false).equals(original)
                        || client.getConnection().getRecipeManager().byKey(recipe.getId()).orElse(null) != recipe
                        || !NativeRecipes.definition(recipe).equals(original)) throw new IOException("GAME_RECIPE_CHANGED");
                if (!inventoryStack(recipe.getResultItem()).equals(identity)) throw new IOException("GAME_RECIPE_CHANGED");
            }
            public int gridWidth() { return menu.getGridWidth(); }
            public int inventoryStart() { return menu instanceof InventoryMenu ? 9 : 10; }
            public int inventoryEnd() { return menu instanceof InventoryMenu ? 45 : 46; }
            public GameInventory.Stack output() { return identity; }
            public GameInventory.View view() throws IOException { return base.view(); }
            public int capacity(int slot, GameInventory.Stack stack) throws IOException {
                var nativeItem = nativeItems.get(stack);
                return nativeItem == null ? base.capacity(slot, stack)
                    : Math.min(nativeItem.getMaxStackSize(), menu.slots.get(slot).getMaxStackSize(nativeItem));
            }
            public boolean mayPlace(int slot, GameInventory.Stack stack) throws IOException {
                var nativeItem = nativeItems.get(stack);
                return nativeItem == null ? base.mayPlace(slot, stack) : menu.slots.get(slot).mayPlace(nativeItem);
            }
            public boolean mayPickup(int slot) throws IOException { return base.mayPickup(slot); }
            public void click(int slot, int button, boolean quick) throws IOException { validate(); base.click(slot, button, quick); }
            public long requestSync() throws IOException { validate(); return base.requestSync(); }
            public GameInventory.View reply(long ticket) throws IOException { validate(); return base.reply(ticket); }
            public void fillRecipe() throws IOException {
                if (selection != null) throw new IOException("MECHANIC_UNSUPPORTED");
                validate(); windowSync.markDirty(menu); client.gameMode.handlePlaceRecipe(menu.containerId, recipe, false);
            }
            public GameActionLane.Motor gridMotor(GameActionLane.Emitter emit) throws IOException {
                return selection == null ? null : GameRecipeGrid.start(this,original,emit);
            }
            public java.util.List<GameInventory.Stack> remainders(GameInventory.View filled) throws IOException {
                validate(); if (!filled.equals(base.view())) throw new IOException("REVISION_CONFLICT");
                var result = new ArrayList<GameInventory.Stack>();
                for (ItemStack item : recipes.remainders(recipe, menu)) {
                    var stack = inventoryStack(item); result.add(stack); if (!stack.empty()) nativeItems.put(stack, item);
                }
                return result;
            }
        };
    }
    private GameActionLane.Motor equip(GameBatch batch, GameActionLane.Emitter emit) throws IOException {
        int source = Math.toIntExact(SettingsJson.integer(batch.action, "inventory_slot"));
        String destination = SettingsJson.string(batch.action, "destination"), expected = SettingsJson.string(batch.action, "expected_item_id");
        if (destination.equals("hand") && source >= 36 && source <= 44) {
            emit.invoke(() -> {
                windowSync.markDirty(client.player.inventoryMenu); client.player.getInventory().selected = source - 36;
            });
            return new GameActionLane.Motor() {
                GameInventory.Port port; long ticket;
                public boolean tick(GameActionLane.Emitter next) throws IOException {
                    if (port == null) {
                        // Minecraft's intervening normal tick sends hotbar selection
                        // before this ordered full-menu refresh.
                        port = inventoryPort(true); port.validate();
                        if (client.player.getInventory().selected != source - 36) throw new IOException("REVISION_CONFLICT");
                        next.invoke(() -> ticket = port.requestSync()); return false;
                    }
                    port.validate(); var reply = port.reply(ticket);
                    if (reply == null) { next.invoke(() -> {}); return false; }
                    if (!reply.equals(port.view()) || !reply.cursor().empty() || !reply.slots().get(source).id().equals(expected)) {
                        throw new IOException("PRECONDITION_FAILED");
                    }
                    return true;
                }
            };
        }
        int target = switch (destination) {
            case "hand" -> 36 + client.player.getInventory().selected;
            case "off_hand" -> 45; case "head" -> 5; case "torso" -> 6; case "legs" -> 7; case "feet" -> 8;
            default -> throw new IOException("GAME_SLOT_INVALID");
        };
        return GameInventory.equip(inventoryPort(true), source, target, expected, emit);
    }
    private EntityHitResult entityHit(String id, String type, boolean attack) throws IOException {
        gameplay(false);
        Entity entity;
        try { entity = client.level.getEntity(Integer.parseInt(id.substring(0, id.indexOf(':')))); }
        catch (IllegalArgumentException | IndexOutOfBoundsException error) { throw new IOException("TARGET_NOT_OBSERVED"); }
        if (entity == null || entity == client.player || entity.isRemoved() || entity.isInvisibleTo(client.player)
                || !id.equals(entityId(entity)) || !type.equals(name(ForgeRegistries.ENTITY_TYPES.getKey(entity.getType())))) {
            throw new IOException("PRECONDITION_FAILED");
        }
        Vec3 eye = client.player.getEyePosition(), target = entity.position().add(0, Math.min(entity.getBbHeight() / 2, 1), 0);
        if (eye.distanceTo(entity.position()) > 16 || !GameVisibility.visible(point(eye), point(target), this::readCell)) {
            throw new IOException("TARGET_OCCLUDED");
        }
        if (attack ? !client.player.canHit(entity, 0) : !client.player.canInteractWith(entity, 0)) throw new IOException("OUT_OF_REACH");
        Vec3 delta = target.subtract(eye);
        EntityHitResult hit = ProjectileUtil.getEntityHitResult(client.player, eye, target,
            client.player.getBoundingBox().expandTowards(delta).inflate(1),
            candidate -> !candidate.isSpectator() && candidate.isPickable(), delta.lengthSqr());
        if (hit == null || hit.getEntity() != entity) throw new IOException("TARGET_OCCLUDED");
        BlockHitResult block = client.level.clip(new ClipContext(eye, hit.getLocation(), ClipContext.Block.OUTLINE,
            ClipContext.Fluid.NONE, client.player));
        if (block.getType() != HitResult.Type.MISS) throw new IOException("TARGET_OCCLUDED");
        return hit;
    }
    private void useContext() throws IOException {
        gameplay(false);
        if (client.gameMode.isDestroying() || client.player.isHandsBusy()) throw new IOException("GAME_HANDS_BUSY");
    }
    private InputEvent.InteractionKeyMappingTriggered inputHook(boolean attack, InteractionHand hand) {
        permittedUseEvent = true;
        try { return ForgeHooksClient.onClickInput(attack ? 0 : 1, attack ? client.options.keyAttack : client.options.keyUse, hand); }
        finally { permittedUseEvent = false; }
    }
    private void triggerEntity(String id, String type, boolean attack) throws IOException {
        useContext();
        var hook = inputHook(attack, InteractionHand.MAIN_HAND);
        if (hook.isCanceled()) {
            if (hook.shouldSwingHand()) client.player.swing(InteractionHand.MAIN_HAND);
            return;
        }
        EntityHitResult hit = entityHit(id, type, attack); // Revalidate after the mod input hook too.
        if (attack) {
            client.gameMode.attack(client.player, hit.getEntity());
            if (hook.shouldSwingHand()) client.player.swing(InteractionHand.MAIN_HAND);
        } else {
            InteractionResult result = client.gameMode.interactAt(client.player, hit.getEntity(), hit, InteractionHand.MAIN_HAND);
            if (result == InteractionResult.PASS) {
                hit = entityHit(id, type, false);
                result = client.gameMode.interact(client.player, hit.getEntity(), InteractionHand.MAIN_HAND);
            }
            if (result.shouldSwing() && hook.shouldSwingHand()) client.player.swing(InteractionHand.MAIN_HAND);
        }
    }
    private GameGestures.UsePort usePort() {
        return new GameGestures.UsePort() {
            private ItemStack started = ItemStack.EMPTY;
            private int selected;
            private InteractionHand hand;
            public void validate() throws IOException { useContext(); }
            public void start(String requested, boolean hold) throws IOException {
                hand = requested.equals("main") ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND;
                selected = client.player.getInventory().selected;
                started = client.player.getItemInHand(hand).copy();
                ownedUse = true;
                var hook = inputHook(false, hand);
                if (hook.isCanceled()) {
                    if (hook.shouldSwingHand()) client.player.swing(hand);
                    return;
                }
                useContext();
                if (selected != client.player.getInventory().selected
                        || !ItemStack.matches(started, client.player.getItemInHand(hand))) throw new IOException("PRECONDITION_FAILED");
                InteractionResult result = client.gameMode.useItem(client.player, hand);
                if (result.shouldSwing() && hook.shouldSwingHand()) client.player.swing(hand);
                boolean keep = hold && stillUsing(requested);
                client.options.keyUse.setDown(keep);
                if (!keep && client.player.isUsingItem()) client.gameMode.releaseUsingItem(client.player);
            }
            public boolean stillUsing(String requested) {
                return client.player.isUsingItem() && client.player.getUsedItemHand() == hand
                    && client.player.getInventory().selected == selected
                    && ItemStack.isSameItemSameTags(started, client.player.getUseItem());
            }
            public void hold() { client.options.keyUse.setDown(true); }
        };
    }
    private BlockHitResult blockHit(GameBatch batch) throws IOException {
        gameplay(false);
        var target = GameBatch.target(batch.action);
        BlockPos pos = new BlockPos(target.x(), target.y(), target.z());
        var cell = readCell(pos.getX(), pos.getY(), pos.getZ());
        if (cell == null || cell.air() || !cell.id().equals(SettingsJson.string(batch.action, "expected_block_id"))) throw new IOException("PRECONDITION_FAILED");
        Vec3 eye = client.player.getEyePosition();
        var boxes = new GameBlockTarget.Builder();
        try {
            client.level.getBlockState(pos).getShape(client.level, pos,
                net.minecraft.world.phys.shapes.CollisionContext.of(client.player)).forAllBoxes(boxes::add);
        } catch (GameBlockTarget.UnsupportedShape error) { throw new IOException("MECHANIC_UNSUPPORTED"); }
        return GameBlockTarget.select(point(eye), new GameVisibility.Point(pos.getX(),pos.getY(),pos.getZ()),
            client.gameMode.getPickRange(), boxes.build(), candidate -> {
                BlockHitResult hit = client.level.clip(new ClipContext(eye,
                    new Vec3(candidate.x(),candidate.y(),candidate.z()), ClipContext.Block.OUTLINE,
                    ClipContext.Fluid.NONE, client.player));
                return hit.getType() == HitResult.Type.BLOCK && hit.getBlockPos().equals(pos) ? hit : null;
            });
    }
    private void look(GameVisibility.Point target) throws IOException {
        Vec3 delta = new Vec3(target.x(), target.y(), target.z()).subtract(client.player.getEyePosition());
        if (delta.lengthSqr() < 1e-12) throw new IOException("GAME_TARGET_INVALID");
        client.player.setYRot((float) Math.toDegrees(Math.atan2(delta.z, delta.x)) - 90);
        client.player.setXRot((float) -Math.toDegrees(Math.atan2(delta.y, Math.sqrt(delta.x * delta.x + delta.z * delta.z))));
    }
    public GameActionLane.Motor begin(GameBatch batch, JsonObject snapshot, GameActionLane.Emitter emitter) throws IOException {
        validate(batch, snapshot);
        switch (batch.kind) {
            case "quest_ui" -> {return GameQuestOpen.start(questOpenPort(),GameQuestOpen.Request.read(batch.action),emitter);}
            case "quest_navigate" -> {return GameQuestNavigation.start(quests.navigationPort(loadedArtifacts,this::questInputContext),GameQuestNavigation.Request.read(batch.action),emitter);}
            case "recipe_navigate" -> {return GameRecipeNavigation.start(quests.recipeNavigationPort(loadedArtifacts,this::questInputContext),GameRecipeNavigation.Request.read(batch.action),emitter);}
            case "quest_menu" -> {return GameQuestMenuAction.start(quests.menuActionPort(loadedArtifacts,this::questInputContext),GameQuestMenuAction.Request.read(batch.action),emitter);}
            case "quest_task" -> {return GameQuestTaskOpen.start(quests.taskOpenPort(loadedArtifacts,this::questInputContext),GameQuestTaskOpen.Request.read(batch.action),emitter);}
            case "quest_reward" -> {return GameQuestRewardOpen.start(quests.rewardOpenPort(loadedArtifacts,this::questInputContext),GameQuestRewardOpen.Request.read(batch.action),emitter);}
            case "move_to" -> {
                var target = GameBatch.target(batch.action); double tolerance = GameBatch.tolerance(batch.action);
                var route = planMove(target, tolerance);
                return GameMovement.start(movementPort(), route, target, tolerance, emitter);
            }
            case "equip" -> { return equip(batch, emitter); }
            case "close_window" -> { return GameMenuClose.start(closePort(), emitter); }
            case "craft" -> { return GameCrafting.start(craftingPort(batch),
                Math.toIntExact(SettingsJson.integer(batch.action, "count")), emitter); }
            case "place" -> {
                BlockHitResult hit = placeHit(batch, snapshot);
                emitter.invoke(() -> look(point(hit.getLocation())));
                emitter.invoke(() -> {
                    var hook = inputHook(false, InteractionHand.MAIN_HAND);
                    if (hook.isCanceled()) { if (hook.shouldSwingHand()) client.player.swing(InteractionHand.MAIN_HAND); return; }
                    var result = client.gameMode.useItemOn(client.player, InteractionHand.MAIN_HAND, placeHit(batch, snapshot));
                    if (result.shouldSwing() && hook.shouldSwingHand()) client.player.swing(InteractionHand.MAIN_HAND);
                });
            }
            case "chat" -> emitter.invoke(() -> client.player.chatSigned(GameGestures.chat(SettingsJson.string(batch.action, "text")), null));
            case "use_item" -> {
                return GameGestures.use(usePort(), SettingsJson.string(batch.action, "hand"),
                    SettingsJson.integer(batch.action, "hold_ms"), () -> System.nanoTime() / 1000000, emitter);
            }
            case "attack", "interact_entity" -> {
                return GameGestures.entity(new GameGestures.EntityPort() {
                    public GameVisibility.Point resolve(String id, String type, boolean attack) throws IOException {
                        return point(entityHit(id, type, attack).getLocation());
                    }
                    public void look(GameVisibility.Point target) throws IOException { NativeGameRuntime.this.look(target); }
                    public void trigger(String id, String type, boolean attack) throws IOException { triggerEntity(id, type, attack); }
                }, snapshot, SettingsJson.string(batch.action, "entity_id"), batch.kind.equals("attack"), emitter);
            }
            case "look_at" -> emitter.invoke(() -> look(GameBatch.target(batch.action)));
            case "click_slot" -> {
                int slot = Math.toIntExact(SettingsJson.integer(batch.action, "slot"));
                boolean right = SettingsJson.string(batch.action, "button").equals("right");
                boolean quick = SettingsJson.string(batch.action, "mode").equals("quick_move");
                var menu = client.player.containerMenu;
                requireInventoryMotor(menu, slot, quick);
                if (NativeThermalMenu.known(menu))
                    return GameMachineInventory.click(inventoryPort(false), NativeThermalMenu.layout(menu), slot, right, quick, emitter);
                return GameInventory.click(inventoryPort(false), slot, right, quick, emitter);
            }
            case "interact_block", "dig" -> {
                BlockHitResult hit = blockHit(batch);
                emitter.invoke(() -> look(point(hit.getLocation())));
                if (batch.kind.equals("interact_block")) {
                    emitter.invoke(() -> client.gameMode.useItemOn(client.player, InteractionHand.MAIN_HAND, hit));
                } else {
                    emitter.invoke(() -> client.gameMode.startDestroyBlock(hit.getBlockPos(), hit.getDirection()));
                    return next -> {
                        gameplay(false);
                        var current = readCell(hit.getBlockPos().getX(), hit.getBlockPos().getY(), hit.getBlockPos().getZ());
                        if (current == null) throw new IOException("PRECONDITION_FAILED");
                        if (!current.id().equals(SettingsJson.string(batch.action, "expected_block_id"))) return true;
                        BlockHitResult fresh = blockHit(batch);
                        next.invoke(() -> client.gameMode.continueDestroyBlock(fresh.getBlockPos(), fresh.getDirection()));
                        return false;
                    };
                }
            }
            default -> throw new IOException("MECHANIC_UNSUPPORTED");
        }
        return ignored -> true; // Input dispatch only; never claim an authoritative gameplay outcome.
    }
    private GameQuestOpen.Port questOpenPort() throws IOException {
        return quests.openPort(loadedArtifacts,this::questInputContext);
    }
    private void questInputContext()throws IOException {
            gameplay(true);
            if (client.player.containerMenu!=client.player.inventoryMenu || !client.player.containerMenu.getCarried().isEmpty()
                    || client.player.isHandsBusy() || client.player.isUsingItem() || client.gameMode.isDestroying())
                throw new IOException("GAME_QUEST_INPUT_BUSY");
            for (KeyMapping mapping:client.options.keyMappings) if(mapping.isDown())throw new IOException("GAME_QUEST_INPUT_BUSY");
            // FTB book close calls the ordinary player container close. Avoid implicit
            // crafting-grid returns/drops until that lifecycle has server confirmation.
            for(int slot=0;slot<=4;slot++)if(!client.player.inventoryMenu.slots.get(slot).getItem().isEmpty())
                throw new IOException("GAME_QUEST_INPUT_BUSY");
    }
    public void releaseInputs() throws IOException {
        requireClientThread(); Throwable primary = null;
        try { releasePlayerInputs(); }
        catch (IOException | RuntimeException | Error failure) { primary = failure; throw failure; }
        finally {
            try { JeiRecipeInput.release(); }
            catch (IOException | RuntimeException | Error cleanup) {
                if (primary != null) primary.addSuppressed(cleanup); else throw cleanup;
            }
        }
    }
    private void releasePlayerInputs() throws IOException {
        requireClientThread(); ownedUse = false; permittedUseEvent = false;
        ownedMovement = false; expectedForward = false; KeyMapping.releaseAll();
        if (client.player != null && client.player.input != null) {
            // Key release also clears the last sampled logical input; physical momentum is retained.
            var input = client.player.input; input.up = false; input.down = false; input.left = false; input.right = false;
            input.jumping = false; input.shiftKeyDown = false; input.forwardImpulse = 0; input.leftImpulse = 0;
        }
        if (windowSync != null) windowSync.cancel();
        if (client.gameMode != null) {
            client.gameMode.stopDestroyBlock();
            if (client.player != null && client.player.isUsingItem()) client.gameMode.releaseUsingItem(client.player);
        }
        for (KeyMapping mapping : client.options.keyMappings) {
            int count = 0;
            while (mapping.consumeClick()) if (++count > 2048) throw new IOException("GAME_INPUT_QUEUE_UNBOUNDED");
            if (mapping.isDown()) throw new IOException("GAME_RELEASE_UNCONFIRMED");
        }
    }

    private GameVisibility.Cell readCell(int x, int y, int z) {
        BlockPos pos = new BlockPos(x, y, z);
        if (!client.level.hasChunkAt(pos) || client.level.isOutsideBuildHeight(pos)) return null;
        var block = client.level.getBlockState(pos);
        ResourceLocation id = ForgeRegistries.BLOCKS.getKey(block.getBlock());
        if (id == null) return null;
        // Only these three IDs are transparent to this policy. Modded air-like blocks
        // remain opaque until their observation semantics are qualified.
        boolean air = id.toString().equals("minecraft:air") || id.toString().equals("minecraft:cave_air")
            || id.toString().equals("minecraft:void_air");
        return new GameVisibility.Cell(x, y, z, id.toString(), air);
    }

    private JsonObject window(AbstractContainerMenu menu) throws IOException {
        if (menu != client.player.inventoryMenu && (!(client.screen instanceof AbstractContainerScreen<?> screen)
                || screen.getMenu() != menu)) throw new IOException("GAME_CONTAINER_NOT_OPEN");
        if (menu.slots.size() > 1024) throw new IOException("GAME_CONTAINER_UNSUPPORTED");
        var thermal = MENUS.contains(menu.getClass()) ? null : NativeThermalMenu.read(client, menu, loadedArtifacts);
        JsonObject window = new JsonObject();
        window.addProperty("id", menu.containerId);
        window.addProperty("type", menu instanceof InventoryMenu ? "minecraft:inventory"
            : name(ForgeRegistries.MENU_TYPES.getKey(menu.getType())));
        if (thermal == null) window.add("slots", slots(menu));
        else {
            var visible = new JsonArray();
            for (int i : thermal.slots()) {
                // Read only current visible slots; never read augment-panel contents.
                var slot = menu.slots.get(i);
                if (!slot.isActive()) continue;
                var value = item(slot.getItem()); value.addProperty("slot", i); visible.add(value);
            }
            window.add("slots", visible); window.add("machine", thermal.machine());
        }
        JsonObject carried = item(menu.getCarried());
        window.add("cursor_item", menu.getCarried().isEmpty() ? JsonNull.INSTANCE : carried);
        String digest = KeyOptions.sha256(GameMachineMenu.inputWindow(window).toString());
        if (menu != windowIdentity || !digest.equals(windowDigest)) {
            windowRevision++; windowIdentity = menu; windowDigest = digest;
        }
        window.addProperty("revision", windowRevision);
        return window;
    }
    private void requireInventoryMotor(AbstractContainerMenu menu, int slot, boolean quick) throws IOException {
        if (MENUS.contains(menu.getClass())) return;
        NativeThermalMenu.read(client, menu, loadedArtifacts);
        var layout = NativeThermalMenu.layout(menu);
        if (!layout.visible(slot) || !menu.slots.get(slot).isActive() || quick && layout.player(slot))
            throw new IOException("MECHANIC_UNSUPPORTED");
    }
    private static JsonArray slots(AbstractContainerMenu menu) throws IOException {
        JsonArray items = new JsonArray();
        for (int i = 0; i < menu.slots.size(); i++) {
            JsonObject value = item(menu.slots.get(i).getItem()); value.addProperty("slot", i); items.add(value);
        }
        return items;
    }
    private static JsonObject item(ItemStack item) throws IOException {
        JsonObject value = new JsonObject();
        value.addProperty("item_id", item.isEmpty() ? null : name(ForgeRegistries.ITEMS.getKey(item.getItem())));
        value.addProperty("count", item.isEmpty() ? 0 : item.getCount());
        value.add("component_summary", new JsonObject());
        return value;
    }
    private static String name(ResourceLocation id) throws IOException {
        if (id == null || id.toString().length() > 256) throw new IOException("GAME_REGISTRY_UNSUPPORTED");
        return id.toString();
    }
    private static GameVisibility.Point point(Vec3 value) { return new GameVisibility.Point(value.x, value.y, value.z); }
    private static JsonObject vector(Vec3 value) {
        JsonObject result = new JsonObject(); result.addProperty("x", value.x); result.addProperty("y", value.y);
        result.addProperty("z", value.z); return result;
    }
}
