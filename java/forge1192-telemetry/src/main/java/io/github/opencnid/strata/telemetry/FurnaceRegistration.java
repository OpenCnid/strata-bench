package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.item.crafting.AbstractCookingRecipe;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.SmeltingRecipe;
import net.minecraftforge.registries.ForgeRegistries;

/** Private observation of real registration/conversion objects; no output matching. */
public final class FurnaceRegistration {
    static final String POLICY="thermal1192-native-recipe-registration/1";
    static final String MANAGER="cofh.thermal.core.util.managers.machine.FurnaceRecipeManager";
    static final String SINGLE="cofh.thermal.lib.util.managers.SingleItemRecipeManager";
    private static final String MANAGERS="cofh.thermal.lib.common.ThermalRecipeManagers";
    private static final String RECIPE="cofh.thermal.core.util.recipes.machine.FurnaceRecipe";
    private static final boolean ENABLED=System.getenv("STRATA_TELEMETRY_CONFIG")!=null;
    private static final RecipeRegistrationIndex index=new RecipeRegistrationIndex(65536);
    private static RecipeManager registry;
    private static Object manager;
    private static Thread refreshThread;

    static boolean support() throws ReflectiveOperationException {
        return FurnaceRegistrationMarker.class.isAssignableFrom(Class.forName(MANAGER))
            && RecipeRegistrationMarker.class.isAssignableFrom(Class.forName(SINGLE)) && index.idle();
    }
    private static boolean active(Object actual,String owner,String method) {
        if(!ENABLED || actual==null || !actual.getClass().getName().equals(MANAGER)) return false;
        try {
            if(actual.getClass()!=Class.forName(MANAGER)) fail();
            var frames=StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE).walk(s ->
                s.dropWhile(f -> f.getDeclaringClass()==FurnaceRegistration.class).limit(2).toList());
            var expected=Class.forName(owner);
            if(frames.size()!=2 || frames.get(0).getDeclaringClass()!=expected
                    || frames.get(1).getDeclaringClass()!=expected || !frames.get(1).getMethodName().equals(method)) fail();
        } catch(ReflectiveOperationException error) {throw failure("MACHINE_REGISTRATION_CLASS",error);}
        return true;
    }
    public static synchronized void begin(Object actual,RecipeManager source) {
        if(!active(actual,MANAGER,"refresh")) return;
        // Initial resource loading can precede MinecraftServer construction.
        // Bind its real server recipe-manager object now, then require identity
        // with the live server's manager at every completion observation.
        var parent=StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE).walk(s ->
            s.dropWhile(f -> f.getDeclaringClass()==FurnaceRegistration.class).skip(2).findFirst().orElseThrow());
        try {
            if(parent.getDeclaringClass()!=Class.forName(MANAGERS) || !parent.getMethodName().equals("refreshServer")
                    || source!=serverRegistry()) fail();
        } catch(ReflectiveOperationException error) {throw failure("MACHINE_REGISTRATION_SOURCE",error);}
        index.begin(actual,source);manager=actual;registry=source;refreshThread=Thread.currentThread();
    }
    public static synchronized void clear(Object actual) {
        if(!active(actual,MANAGER,"clear")) return;
        index.clear(actual);
    }
    public static synchronized void converted(Object actual,AbstractCookingRecipe source,Object result) {
        if(!active(actual,MANAGER,"convert")) return;
        context(actual);
        try {
            if(source.getClass()!=SmeltingRecipe.class || result==null || result.getClass()!=Class.forName(RECIPE)) fail();
        } catch(ReflectiveOperationException error) {throw failure("MACHINE_REGISTRATION_CONVERSION",error);}
        index.converted(actual,result,source(source));
    }
    public static synchronized void enter(Object actual,Object value) {
        if(!active(actual,SINGLE,"addRecipe")) return;
        context(actual);
        try {
            if(value==null || value.getClass()!=Class.forName(RECIPE) || !(value instanceof Recipe<?>)) fail();
        } catch(ReflectiveOperationException error) {throw failure("MACHINE_REGISTRATION_RECIPE",error);}
        var recipe=(Recipe<?>)value;
        var converted=index.conversion(actual,value);
        index.enter(actual,recipe.getId().toString(),converted==null?source(recipe):converted,
            converted==null?"direct":"converted_cooking");
    }
    public static synchronized void returned(Object actual,Object result) {
        if(!active(actual,SINGLE,"addRecipe")) return;
        context(actual);index.returned(actual,result);
    }
    public static synchronized void leave(Object actual) {
        if(!active(actual,SINGLE,"addRecipe")) return;
        context(actual);index.leave(actual);
    }
    public static synchronized void end(Object actual) {
        if(!active(actual,MANAGER,"refresh")) return;
        context(actual);index.end(actual);refreshThread=null;
    }
    static synchronized JsonObject observe(MinecraftServer server,Object internal) throws ReflectiveOperationException {
        if(!server.isSameThread() || !server.isDedicatedServer()) fail();
        var actual=Class.forName(MANAGER).getMethod("instance").invoke(null);
        var entry=index.lookup(actual,server.getRecipeManager(),internal);
        if(entry==null || registry!=server.getRecipeManager() || registry!=serverRegistry())
            throw new UnsupportedOperationException("MACHINE_REGISTRATION_UNOBSERVED");
        var source=(Recipe<?>)entry.source().recipe();
        if(registry.byKey(source.getId()).orElse(null)!=source
                || !entry.source().equals(source(source)))
            throw new UnsupportedOperationException("MACHINE_REGISTRATION_CHANGED");
        var out=new JsonObject();out.addProperty("policy",POLICY);out.addProperty("generation",entry.generation());
        out.addProperty("origin",entry.origin());out.addProperty("source_recipe_id",entry.source().id());
        out.addProperty("source_recipe_type",entry.source().type());out.addProperty("source_serializer_id",entry.source().serializer());
        out.addProperty("machine_recipe_id",entry.machineId());return out;
    }
    static synchronized void close() {
        if(!index.idle()) fail();
        index.clear(manager);manager=null;registry=null;refreshThread=null;
    }
    private static RecipeRegistrationIndex.Source source(Recipe<?> recipe) {
        if(registry==null || registry.byKey(recipe.getId()).orElse(null)!=recipe) fail();
        var type=ForgeRegistries.RECIPE_TYPES.getKey(recipe.getType());
        var serializer=ForgeRegistries.RECIPE_SERIALIZERS.getKey(recipe.getSerializer());
        if(type==null || serializer==null) fail();
        return new RecipeRegistrationIndex.Source(recipe,recipe.getId().toString(),type.toString(),serializer.toString());
    }
    private static RecipeManager serverRegistry() throws ReflectiveOperationException {
        var type=Class.forName(MANAGERS);var singleton=type.getMethod("instance").invoke(null);
        var field=type.getDeclaredField("serverRecipeManager");field.setAccessible(true);
        return (RecipeManager)field.get(singleton);
    }
    private static void context(Object actual) {
        if(actual!=manager || registry==null || refreshThread!=Thread.currentThread()) fail();
    }
    private static IllegalStateException failure(String code,Exception cause) {index.poison();return new IllegalStateException(code,cause);}
    private static void fail() {index.poison();throw new IllegalStateException("MACHINE_REGISTRATION_LIFETIME");}
    private FurnaceRegistration() {}
}
