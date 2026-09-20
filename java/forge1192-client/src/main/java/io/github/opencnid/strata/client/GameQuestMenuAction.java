package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;

/** One ordinary Back or wheel gesture on the currently observed supported menu. */
final class GameQuestMenuAction {
    static final String POLICY="ftb-current-item-choice-menu-back-wheel/2";
    record Request(String operation,String direction,long source,long generation,long revision) {
        static Request read(JsonObject value)throws IOException {
            SettingsJson.fields(value,"kind","operation","direction","source","source_generation","expected_menu_generation","expected_menu_revision");
            if(!SettingsJson.string(value,"kind").equals("quest_menu") || !SettingsJson.string(value,"source").equals("ftb_quests"))throw invalid();
            String operation=SettingsJson.string(value,"operation"),direction=value.get("direction").isJsonNull()?null:SettingsJson.string(value,"direction");
            if(!(operation.equals("back") && direction==null || operation.equals("scroll") && ("up".equals(direction)||"down".equals(direction))))throw invalid();
            return new Request(operation,direction,SettingsJson.integer(value,"source_generation"),SettingsJson.integer(value,"expected_menu_generation"),
                SettingsJson.integer(value,"expected_menu_revision"));
        }
    }
    /** Pinned ScrollBar uses Mth.clamp even for a negative content-minus-viewport maximum. */
    record Wheel(double value,double minimum,double maximum) {
        void validate(Scroll scroll)throws IOException {
            for(double n:new double[]{value,minimum,maximum})if(!Double.isFinite(n) || Math.abs(n)>1048576)throw invalid();
            if(minimum!=0 || maximum!=scroll.contentHeight-scroll.height || scroll.x!=0
                    || value<Math.min(0,maximum) || value>Math.max(0,maximum)
                    || scroll.y!=(maximum>0?value:0))throw invalid();
        }
        double next(double step,String direction) {
            double attempted=value+(direction.equals("up")?-step:step);
            return attempted<minimum?minimum:attempted>maximum?maximum:attempted;
        }
    }
    record Scroll(double x,double y,double step,int width,int height,int contentWidth,int contentHeight,Wheel wheel) {
        Scroll(double x,double y,double step,int width,int height,int contentWidth,int contentHeight) {
            this(x,y,step,width,height,contentWidth,contentHeight,null);
        }
        void validate()throws IOException {
            for(double value:new double[]{x,y,step})if(!Double.isFinite(value))throw invalid();
            if(step<=0 || step>1024 || width<=0 || height<=0 || contentWidth<0 || contentHeight<0
                    || width>1048576 || height>1048576 || contentWidth>1048576 || contentHeight>1048576
                    || x<0 || x>Math.max(0,contentWidth-width) || y<0 || y>Math.max(0,contentHeight-height))throw invalid();
            if(wheel!=null)wheel.validate(this);
        }
        double nextY(String direction)throws IOException {
            validate();if(!"up".equals(direction) && !"down".equals(direction))throw invalid();
            if(wheel!=null)return wheel.maximum>0?wheel.next(step,direction):0;
            // Pinned Panel.scrollPanel with released Shift uses -step * wheelDelta on Y.
            return contentHeight>height?Math.max(0,Math.min(contentHeight-height,y+(direction.equals("up")?-step:step))):y;
        }
        Scroll after(String direction)throws IOException {
            double next=nextY(direction);
            return new Scroll(x,next,step,width,height,contentWidth,contentHeight,
                wheel==null?null:new Wheel(wheel.next(step,direction),wheel.minimum,wheel.maximum));
        }
    }
    record State(long source,long generation,long revision,Object menu,Object parent,Object task,
                 String shape,Scroll scroll,boolean back,boolean wheel) {
        void validate()throws IOException {
            for(long n:new long[]{source,generation,revision})if(n<0 || n>9007199254740991L)throw invalid();
            if(menu==null || parent==null || task==null || menu==parent || shape==null || !shape.matches("[a-f0-9]{64}"))throw invalid();
            if(scroll==null)throw invalid();scroll.validate();
        }
        boolean identity(State other) {
            return source==other.source && generation==other.generation && menu==other.menu && parent==other.parent && task==other.task
                && shape.equals(other.shape) && back==other.back && wheel==other.wheel;
        }
        boolean same(State other){return identity(other) && revision==other.revision && scroll.equals(other.scroll);}
    }
    interface Port {
        State read()throws IOException;
        void back(State before)throws IOException;
        void wheel(State before,String direction)throws IOException;
        void confirmBack(State before)throws IOException;
    }
    static State validate(Port port,Request request)throws IOException {
        var state=port.read();if(state==null)throw invalid();state.validate();
        if(state.source!=request.source || state.generation!=request.generation || state.revision!=request.revision)throw changed();
        if(request.operation.equals("back")?!state.back:!state.wheel)throw new IOException("TARGET_NOT_OBSERVED");
        var second=port.read();if(second==null)throw changed();second.validate();if(!state.same(second))throw changed();return state;
    }
    private static void confirm(Port port,Request request,State before)throws IOException {
        if(request.operation.equals("back")){port.confirmBack(before);return;}
        var after=port.read();if(after==null)throw changed();after.validate();
        var expected=before.scroll.after(request.direction);
        if(!before.identity(after) || !expected.equals(after.scroll))throw new IOException("GAME_QUEST_SCROLL_UNCONFIRMED");
    }
    static GameActionLane.Motor start(Port port,Request request,GameActionLane.Emitter emit)throws IOException {
        var before=validate(port,request);
        emit.invoke(()->{
            if(!before.same(validate(port,request)))throw changed();
            if(request.operation.equals("back"))port.back(before);else port.wheel(before,request.direction);
        });
        confirm(port,request,before);return ignored->{confirm(port,request,before);return true;};
    }
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
    private static IOException invalid(){return new IOException("GAME_QUEST_MENU_ACTION_INVALID");}
}
