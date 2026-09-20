package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.Objects;

/** Small current-screen projection with private object identity and no widget/graph export. */
final class GameQuestScreen {
    static final String POLICY="ftb-own-team-book-and-task-recipes-state/2";
    record Frame(long source,Object screen,Object chapterObject,Object questObject,String chapter,String quest,String context,String kind) {
        Frame(long source,Object screen,Object chapterObject,Object questObject,String chapter,String quest,String context) {
            this(source,screen,chapterObject,questObject,chapter,quest,context,screen==null?"closed":"quest_book");
        }
        void validate()throws IOException {
            if(source<0 || source>9007199254740991L || context==null || !context.matches("[a-f0-9]{64}"))throw invalid();
            for(String id:new String[]{chapter,quest})if(id!=null && !id.matches("[0-9A-F]{16}"))throw invalid();
            if((chapterObject==null)!=(chapter==null) || (questObject==null)!=(quest==null)
                    || quest!=null && chapter==null || screen==null && (chapter!=null || quest!=null)
                    || kind==null || !java.util.Set.of("closed","quest_book","task_recipes").contains(kind)
                    || kind.equals("closed")!=(screen==null) || kind.equals("task_recipes") && quest==null)throw invalid();
        }
        boolean same(Frame other) {
            return source==other.source && screen==other.screen && chapterObject==other.chapterObject && questObject==other.questObject
                && Objects.equals(chapter,other.chapter) && Objects.equals(quest,other.quest) && context.equals(other.context) && kind.equals(other.kind);
        }
    }
    record Snapshot(Frame frame,long generation,long revision) {
        JsonObject json() {
            var value=new JsonObject();value.addProperty("policy",POLICY);value.addProperty("source_generation",frame.source);
            value.addProperty("screen_generation",generation);value.addProperty("revision",revision);
            value.addProperty("kind",frame.kind);
            value.addProperty("chapter_id",frame.chapter);value.addProperty("quest_id",frame.quest);return value;
        }
    }
    interface Source {Frame read()throws IOException;}
    private Frame previous;private long generation,revision;
    private final java.util.function.LongSupplier clock;
    GameQuestScreen(){this(System::nanoTime);}
    GameQuestScreen(java.util.function.LongSupplier clock){this.clock=clock;}
    Snapshot capture(Source source)throws IOException {
        long start=clock.getAsLong();var first=source.read();if(first==null)throw invalid();first.validate();
        var second=source.read();if(second==null)throw invalid();second.validate();
        if(!first.same(second))throw new IOException("GAME_QUEST_CHANGED");
        if(clock.getAsLong()-start>100_000_000L)throw new IOException("GAME_QUEST_TIMEOUT");
        if(previous==null || previous.screen!=first.screen || previous.source!=first.source || !previous.kind.equals(first.kind))generation++;
        if(previous==null || !previous.same(first))revision++;
        if(generation>9007199254740991L || revision>9007199254740991L)throw invalid();
        previous=first;return new Snapshot(first,generation,revision);
    }
    private static IOException invalid(){return new IOException("GAME_QUEST_SCREEN_INVALID");}
}
