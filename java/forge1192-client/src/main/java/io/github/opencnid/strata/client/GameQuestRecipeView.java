package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.Map;

/** Private opening provenance for a recipe screen; never a rendered recipe-page projection. */
final class GameQuestRecipeView {
    static final Map<String,String> ARTIFACTS=Map.of(
        "ftb-xmod-compat-forge-1.2.4.jar","9c8c169088cf53834190cc3ac78f554a78c8b8e9c0689cf287ab1c158582fede",
        "jei-1.19.2-forge-11.8.1.1034.jar","4ca677c4d7b8234da2071b3e93424a2e1eedd06906c20f55ff22a078cfd6e3b2");
    static void requireArtifacts(Map<String,String> artifacts)throws IOException {
        GameQuestCatalog.requireArtifacts(artifacts);
        for(var pin:ARTIFACTS.entrySet())if(!pin.getValue().equals(artifacts.get(pin.getKey())))
            throw new IOException("GAME_QUEST_RECIPE_ARTIFACT_UNSUPPORTED");
    }
    record Binding(Object screen,GameQuestScreen.Frame parent,Object task,Object runtime,GameActionLane.Operation validity) {
        void validate()throws IOException {
            if(screen==null || parent==null || task==null || runtime==null || validity==null)throw changed();
            parent.validate();
            if(!parent.kind().equals("quest_book") || parent.quest()==null || screen==parent.screen())throw changed();
            validity.run();
        }
        boolean same(Binding other) {
            return screen==other.screen && task==other.task && runtime==other.runtime && parent.same(other.parent);
        }
    }
    static final class Bindings {
        private Binding value;
        void bind(Binding next)throws IOException {
            if(next==null)throw changed();next.validate();
            if(value!=null && !value.same(next))throw changed();value=next;
        }
        void tick(Object screen) {
            if(value==null)return;
            try {value.validate();if(value.screen!=screen)clear();}
            catch(IOException | RuntimeException changed){clear();}
        }
        Binding current(Object screen)throws IOException {tick(screen);if(value==null)throw changed();return value;}
        void clear(){value=null;}
    }
    static boolean sameOrigin(GameQuestScreen.Frame a,GameQuestScreen.Frame b) {
        return a.source()==b.source() && a.screen()==b.screen() && a.chapterObject()==b.chapterObject()
            && a.questObject()==b.questObject() && java.util.Objects.equals(a.chapter(),b.chapter())
            && java.util.Objects.equals(a.quest(),b.quest()) && a.kind().equals(b.kind());
    }
    static GameQuestScreen.Frame frame(Binding binding,GameQuestScreen.Frame parent,String layout)throws IOException {
        binding.validate();parent.validate();if(!sameOrigin(binding.parent,parent) || layout==null || !layout.matches("[a-f0-9]{64}"))throw changed();
        return new GameQuestScreen.Frame(parent.source(),binding.screen,parent.chapterObject(),parent.questObject(),parent.chapter(),parent.quest(),
            KeyOptions.sha256(layout+"/"+parent.context()),"task_recipes");
    }
    static void confirmReturn(Binding binding,GameQuestScreen.Frame parent)throws IOException {
        binding.validate();parent.validate();if(!sameOrigin(binding.parent,parent))throw changed();
    }
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
}
