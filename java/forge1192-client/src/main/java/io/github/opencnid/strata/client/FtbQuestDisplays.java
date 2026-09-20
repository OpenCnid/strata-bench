package io.github.opencnid.strata.client;

import static io.github.opencnid.strata.client.NativeQuests.*;
import dev.ftb.mods.ftblibrary.util.TooltipList;
import dev.ftb.mods.ftblibrary.util.WrappedIngredient;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;

/** Optional FTB public display API. Loaded only after the three exact artifact guards. */
final class FtbQuestDisplays {
    static List<GameQuestText.Line> itemTooltip(ItemStack stack,Minecraft client)throws IOException {
        requireNormalModifiers();var tooltip=new Capture();
        try {
            var lines=stack.getTooltipLines(client.player,TooltipFlag.Default.NORMAL);
            if(lines.size()>64)throw new IOException("GAME_QUEST_BOUNDS");for(var line:lines)tooltip.add(line);
        }catch(UncheckedIOException failure){throw failure.getCause();}
        requireNormalModifiers();return tooltip.result();
    }
    static List<GameQuestText.Line> widgetTooltip(dev.ftb.mods.ftblibrary.ui.Widget widget)throws IOException {
        requireNormalModifiers();var tooltip=new Capture();
        try{widget.addMouseOverText(tooltip);}catch(UncheckedIOException failure){throw failure.getCause();}
        requireNormalModifiers();return tooltip.result();
    }
    static void requireNormalModifiers() throws IOException {
        if(Screen.hasShiftDown() || Screen.hasControlDown() || Screen.hasAltDown())
            throw new IOException("GAME_QUEST_MODIFIER_ACTIVE");
    }
    static GameQuestComponents.Display task(Object task,Object team,boolean startable) throws IOException {
        requireNormalModifiers();requireClass(task,"task");
        String title=plain(call(task,"getTitle"));var tooltip=new Capture();
        Class<?> teamType=type("quest.TeamData"),taskType=type("quest.task.Task"),objectType=type("quest.QuestObject");
        call(task,"addMouseOverHeader",new Class<?>[]{TooltipList.class,teamType,boolean.class},tooltip,team,false);
        String progress=GameQuestComponents.progressLabel(new GameQuestComponents.Progress() {
            public boolean startable(){return startable;}
            public long maximum()throws IOException{return number(call(task,"getMaxProgress"));}
            public long current()throws IOException{return number(call(team,"getProgress",new Class<?>[]{taskType},task));}
            public boolean hiddenNumbers()throws IOException{return bool(call(task,"hideProgressNumbers"));}
            public int percent()throws IOException{return FtbQuestDisplays.percent(call(task,"getRelativeProgressFromChildren",new Class<?>[]{teamType},team));}
            public String maximumLabel()throws IOException{return string(call(task,"formatMaxProgress"));}
            public String currentLabel(long current)throws IOException{return string(call(task,"formatProgress",new Class<?>[]{teamType,long.class},team,current));}
        });
        if(progress!=null)tooltip.add(Component.literal(progress));
        boolean optional=bool(call(task,"isOptionalForProgression"));
        if(optional)tooltip.add(Component.translatable("ftbquests.quest.optional"));
        call(task,"addMouseOverText",new Class<?>[]{TooltipList.class,teamType},tooltip,team);
        boolean completed=bool(call(team,"isCompleted",new Class<?>[]{objectType},task));
        requireNormalModifiers();return new GameQuestComponents.Display(title,tooltip.result(),
            new GameQuestComponents.Task(completed,optional,progress),null);
    }
    static GameQuestComponents.Display reward(Object reward,Object team,Minecraft client) throws IOException {
        requireNormalModifiers();requireClass(reward,"reward");
        var title=call(reward,"getTitle");String titleText=plain(title);var tooltip=new Capture();
        if(bool(call(reward,"addTitleInMouseOverText")))tooltip.add((Component)title);
        boolean teamReward=bool(call(reward,"isTeamReward"));
        if(teamReward) {
            Object ingredient=call(reward,"getIngredient");
            if(ingredient instanceof WrappedIngredient wrapped && wrapped.tooltip) {
                Object unwrapped=WrappedIngredient.unwrap(ingredient);
                if(unwrapped instanceof ItemStack stack && !stack.isEmpty()) {
                    var lines=stack.getTooltipLines(client.player,TooltipFlag.Default.NORMAL);
                    if(lines.size()>64)throw new IOException("GAME_QUEST_BOUNDS");for(var line:lines)tooltip.add(line);
                }
            }
            tooltip.blankLine();
        }
        call(reward,"addMouseOverText",new Class<?>[]{TooltipList.class},tooltip);
        if(teamReward)tooltip.add(Component.translatable("ftbquests.reward.team_reward"));
        Object claim=call(team,"getClaimType",new Class<?>[]{java.util.UUID.class,type("quest.reward.Reward")},client.player.getUUID(),reward);
        if(!(claim instanceof Enum<?> value) || !claim.getClass().getName().equals("dev.ftb.mods.ftbquests.quest.reward.RewardClaimType"))
            throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
        String state=switch(value.name()) {case "CAN_CLAIM"->"can_claim";case "CANT_CLAIM"->"cannot_claim";case "CLAIMED"->"claimed";
            default->throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");};
        requireNormalModifiers();return new GameQuestComponents.Display(titleText,tooltip.result(),null,new GameQuestComponents.Reward(state,teamReward));
    }
    private static void requireClass(Object value,String part) throws IOException {
        if(!value.getClass().getName().startsWith("dev.ftb.mods.ftbquests.quest."+part+"."))
            throw new IOException("GAME_QUEST_COMPONENT_UNSUPPORTED");
    }
    private static long number(Object value)throws IOException {
        if(!(value instanceof Long number) || number<0)throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");return number;
    }
    private static int percent(Object value)throws IOException {
        if(!(value instanceof Integer number) || number<0 || number>100)throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");return number;
    }
    private static final class Capture extends TooltipList {
        private final List<GameQuestText.Line> captured=new ArrayList<>();
        private int bytes;
        @Override public void add(Component component) {
            try {
                if(captured.size()>=64)throw new IOException("GAME_QUEST_BOUNDS");
                GameQuestText.Line line;
                try{line=new GameQuestText.Line("text",plain(component));}
                catch(UnsupportedText unsupported){line=new GameQuestText.Line("unsupported",null);}
                bytes+=line.json().toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length;
                if(bytes>16384)throw new IOException("GAME_QUEST_BOUNDS");captured.add(line);
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        @Override public void reset(){captured.clear();bytes=0;}
        @Override public boolean shouldRender(){return !captured.isEmpty();}
        List<GameQuestText.Line> result(){return List.copyOf(captured);}
    }
}
