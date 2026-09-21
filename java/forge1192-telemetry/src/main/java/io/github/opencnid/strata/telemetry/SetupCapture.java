package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.Collection;
import java.util.HexFormat;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.dedicated.DedicatedServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.fml.ModList;

/** Fixed read-only native observations, not a fixture-validity assertion. */
final class SetupCapture {
    static final String POLICY = "native-e9e-setup-observation/1";
    static final Map<String,String> PINS = Map.of(
        "ftbteams", "2233122cfddfccafd5f4840ae63a556edd7088ad15e177fb1288367adef142f7",
        "kubejs", "d9bc8bcca17fea536462a8471a2880adabc76ef8bdd84a93ad0b682a960ea5c7",
        "rhino", "0dc7db781fa9609d08932533661683a9686608b088a65f6b62bbd48ffd1316f8");
    // Counts observed Forge CommandEvent attempts, including unsuccessful ones.
    // It is not proof that all possible mod/admin mutation routes were observed.
    static final AtomicLong COMMAND_EVENTS = new AtomicLong();
    private static boolean supported;

    static JsonObject support() throws IOException {
        supported=false;
        var pins=new JsonObject(); boolean matches=true;
        for (var entry:PINS.entrySet()) {
            var mod=ModList.get().getModFileById(entry.getKey());
            if(mod==null) {pins.add(entry.getKey(),JsonNull.INSTANCE);matches=false;continue;}
            var path=mod.getFile().getFilePath();
            if(!Files.isRegularFile(path)||Files.size(path)>32*1024*1024) throw new IOException("SETUP_ARTIFACT");
            try(var stream=Files.newInputStream(path)) {
                var hash=MessageDigest.getInstance("SHA-256");byte[] buffer=new byte[65536];int n;
                while((n=stream.read(buffer))!=-1) hash.update(buffer,0,n);
                String actual=HexFormat.of().formatHex(hash.digest());pins.addProperty(entry.getKey(),actual);
                matches &= entry.getValue().equals(actual);
            } catch(java.security.NoSuchAlgorithmException error) {throw new IOException("SETUP_ARTIFACT",error);}
        }
        supported=matches;
        var result=new JsonObject();result.addProperty("status",matches?"supported":"unsupported");
        result.add("artifacts",pins);return result;
    }

    static JsonObject unavailable(String code) {
        var result=new JsonObject();result.addProperty("status","unavailable");
        result.addProperty("error_code",code);return result;
    }

    static JsonObject mode(Map<?,?> global,int startupErrors,int serverErrors) {
        Object mode=global.get("packmode"),expert=global.get("isExpertMode"),normal=global.get("isNormalMode");
        if(!(mode instanceof String text)||!Set.of("normal","expert").contains(text)
            ||!(expert instanceof Boolean)||!(normal instanceof Boolean)) return unavailable("SETUP_MODE_VALUE");
        var result=new JsonObject();result.addProperty("status","observed");result.addProperty("mode",text);
        result.addProperty("is_expert",(Boolean)expert);result.addProperty("is_normal",(Boolean)normal);
        result.addProperty("startup_errors",startupErrors);result.addProperty("server_errors",serverErrors);return result;
    }

    private static JsonObject pack() {
        if(!supported) return unavailable("SETUP_ARTIFACT_UNSUPPORTED");
        try {
            var plugin=Class.forName("dev.latvian.mods.kubejs.BuiltinKubeJSPlugin");
            var global=plugin.getField("GLOBAL").get(null);
            var type=Class.forName("dev.latvian.mods.kubejs.script.ScriptType");
            int startup=((Collection<?>)type.getField("errors").get(type.getField("STARTUP").get(null))).size();
            int server=((Collection<?>)type.getField("errors").get(type.getField("SERVER").get(null))).size();
            return global instanceof Map<?,?> values?mode(values,startup,server):unavailable("SETUP_MODE_VALUE");
        } catch(ReflectiveOperationException|RuntimeException error) {return unavailable("SETUP_MODE_UNAVAILABLE");}
    }

    static JsonObject teamProjection(UUID id,String type,Set<?> members,String rank) {
        if(members.size()>128||members.stream().anyMatch(value->!(value instanceof UUID))) return unavailable("SETUP_TEAM_QUOTA");
        var value=new JsonObject();value.addProperty("status","observed");value.addProperty("team_id",id.toString());
        value.addProperty("team_type",type);value.addProperty("actor_rank",rank);
        var ids=new JsonArray();members.stream().map(Object::toString).sorted().forEach(ids::add);
        value.add("member_ids",ids);return value;
    }

    private static JsonObject team(MinecraftServer server,ServerPlayer player) {
        if(!supported) return unavailable("SETUP_ARTIFACT_UNSUPPORTED");
        try {
            var managerType=Class.forName("dev.ftb.mods.ftbteams.data.TeamManager");
            var manager=managerType.getField("INSTANCE").get(null);
            if(manager==null||managerType.getMethod("getServer").invoke(manager)!=server) return unavailable("SETUP_TEAM_MANAGER");
            // Do not call TeamManager.getId(): it generates an ID if absent.
            if(player==null) {var value=new JsonObject();value.addProperty("status","manager_ready");return value;}
            // This UUID overload only reads knownPlayers/actualTeam. The other
            // overload and getPlayerTeamID have different null/fallback semantics.
            var team=managerType.getMethod("getPlayerTeam",UUID.class).invoke(manager,player.getUUID());
            if(team==null) return unavailable("SETUP_TEAM_MISSING");
            var base=Class.forName("dev.ftb.mods.ftbteams.data.TeamBase");
            var id=(UUID)base.getMethod("getId").invoke(team);
            var type=(Enum<?>)base.getMethod("getType").invoke(team);
            var rank=(Enum<?>)base.getMethod("getHighestRank",UUID.class).invoke(team,player.getUUID());
            return teamProjection(id,type.name(),(Set<?>)base.getMethod("getMembers").invoke(team),rank.name());
        } catch(ReflectiveOperationException|RuntimeException error) {return unavailable("SETUP_TEAM_UNAVAILABLE");}
    }

    static JsonObject capture(MinecraftServer server,ServerPlayer player,String transaction,String phase) {
        if(!server.isSameThread()||!(server instanceof DedicatedServer dedicated)) throw new IllegalStateException("SETUP_THREAD");
        var result=new JsonObject();result.addProperty("policy",POLICY);result.addProperty("phase",phase);
        if(transaction==null) result.add("transaction_id",JsonNull.INSTANCE);else result.addProperty("transaction_id",transaction);
        var world=server.getWorldData();var properties=dedicated.getProperties();
        var nativeServer=new JsonObject();nativeServer.addProperty("default_game_mode",server.getDefaultGameType().getName());
        nativeServer.addProperty("world_game_mode",world.getGameType().getName());
        nativeServer.addProperty("difficulty",world.getDifficulty().name().toLowerCase(Locale.ROOT));
        nativeServer.addProperty("hardcore",server.isHardcore());nativeServer.addProperty("world_allows_commands",world.getAllowCommands());
        nativeServer.addProperty("command_blocks_enabled",properties.enableCommandBlock);
        nativeServer.addProperty("rcon_enabled",properties.enableRcon);
        var levels=new JsonArray();var ops=server.getPlayerList().getOps().getEntries();
        if(ops.size()>128) throw new IllegalStateException("SETUP_OP_QUOTA");
        ops.stream().map(entry->entry.getLevel()).sorted().forEach(levels::add);
        nativeServer.add("operator_levels",levels);nativeServer.addProperty("command_events_seen",COMMAND_EVENTS.get());
        result.add("server",nativeServer);result.add("pack",pack());result.add("team",team(server,player));
        if(player==null) result.add("actor",JsonNull.INSTANCE);
        else {
            var actor=new JsonObject();actor.addProperty("uuid",player.getUUID().toString());
            actor.addProperty("game_mode",player.gameMode.getGameModeForPlayer().getName());
            actor.addProperty("is_operator",server.getPlayerList().isOp(player.getGameProfile()));result.add("actor",actor);
        }
        return result;
    }
}
