package io.github.opencnid.strata.telemetry;

import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class RecipeRegistrationIndexTest {
    private final Object manager=new Object(),registry=new Object();
    private RecipeRegistrationIndex.Source source(Object recipe,String id) {
        return new RecipeRegistrationIndex.Source(recipe,id,"thermal:furnace","thermal:furnace");
    }
    private RecipeRegistrationIndex start(int limit) {
        var index=new RecipeRegistrationIndex(limit);index.begin(manager,registry);index.clear(manager);return index;
    }
    @Test void directRegistrationBindsEveryReturnedAlternativeOnlyAfterCompleteRefresh() {
        var index=start(4);var recipe=new Object();var a=new Object();var b=new Object();
        index.enter(manager,"thermal:registered",source(recipe,"thermal:registered"),"direct");
        index.returned(manager,a);index.returned(manager,null);index.returned(manager,b);index.leave(manager);
        assertNull(index.lookup(manager,registry,a));index.end(manager);
        assertSame(recipe,index.lookup(manager,registry,a).source().recipe());
        assertEquals(index.lookup(manager,registry,a),index.lookup(manager,registry,b));
        assertNull(index.lookup(new Object(),registry,a));assertNull(index.lookup(manager,new Object(),a));
    }
    private static final class EqualObject {
        public boolean equals(Object other) { return other instanceof EqualObject; }
        public int hashCode() { return 1; }
    }
    @Test void convertedRecipesWithEqualKeysOrIdsKeepTheirActualObjectLineage() {
        var index=start(4);var first=new EqualObject();var second=new EqualObject();
        var source1=source(new Object(),"minecraft:first");var source2=source(new Object(),"minecraft:second");
        index.converted(manager,first,source1);index.converted(manager,second,source2);
        assertSame(source1,index.conversion(manager,first));assertSame(source2,index.conversion(manager,second));
        assertNull(index.conversion(manager,new EqualObject()));
        var a=new EqualObject();var b=new EqualObject();
        index.enter(manager,"thermal:collision",source1,"converted_cooking");index.returned(manager,a);index.leave(manager);
        index.enter(manager,"thermal:collision",source2,"converted_cooking");index.returned(manager,b);index.leave(manager);index.end(manager);
        assertSame(source1,index.lookup(manager,registry,a).source());assertSame(source2,index.lookup(manager,registry,b).source());
        assertNull(index.lookup(manager,registry,new EqualObject()));
    }
    @Test void reloadAndNativeClearInvalidatePriorBindings() {
        var index=start(4);var internal=new Object();var source=source(new Object(),"thermal:one");
        index.enter(manager,"thermal:one",source,"direct");index.returned(manager,internal);index.leave(manager);index.end(manager);
        long old=index.lookup(manager,registry,internal).generation();
        index.begin(manager,registry);assertNull(index.lookup(manager,registry,internal));index.clear(manager);
        var replacement=new Object();index.enter(manager,"thermal:one",source,"direct");
        index.returned(manager,replacement);index.leave(manager);index.end(manager);
        assertNull(index.lookup(manager,registry,internal));assertEquals(old+1,index.lookup(manager,registry,replacement).generation());
        index.clear(manager);assertNull(index.lookup(manager,registry,replacement));
    }
    @Test void incompleteOrNestedRefreshAndUnpairedReturnsCannotBecomeReady() {
        var index=new RecipeRegistrationIndex(4);index.begin(manager,registry);
        assertThrows(IllegalStateException.class,()->index.end(manager));
        assertThrows(IllegalStateException.class,()->index.begin(manager,registry));
        var unpaired=start(4);
        assertThrows(IllegalStateException.class,()->unpaired.returned(manager,new Object()));
        var pending=start(4);pending.enter(manager,"thermal:one",source(new Object(),"thermal:one"),"direct");
        assertThrows(IllegalStateException.class,()->pending.end(manager));
        var nested=start(4);nested.enter(manager,"thermal:one",source(new Object(),"thermal:one"),"direct");
        assertThrows(IllegalStateException.class,()->nested.enter(manager,"thermal:one",source(new Object(),"thermal:one"),"direct"));
        assertFalse(index.idle());
    }
    @Test void quotaAndDuplicateNativeObjectsFailInsteadOfEvictingEvidence() {
        var index=start(1);var internal=new Object();index.enter(manager,"thermal:one",source(new Object(),"thermal:one"),"direct");
        index.returned(manager,internal);
        assertThrows(IllegalStateException.class,()->index.returned(manager,new Object()));
        assertThrows(IllegalStateException.class,()->index.leave(manager));
        assertNull(index.lookup(manager,registry,internal));assertFalse(index.idle());
        var duplicate=start(2);duplicate.enter(manager,"thermal:one",source(new Object(),"thermal:one"),"direct");
        duplicate.returned(manager,internal);assertThrows(IllegalStateException.class,()->duplicate.returned(manager,internal));
        var conversion=start(1);var converted=new Object();var source=source(new Object(),"minecraft:one");
        conversion.converted(manager,converted,source);
        assertThrows(IllegalStateException.class,()->conversion.converted(manager,new Object(),source));
    }
    @Test void refreshOwnerThreadCannotBeSubstituted() throws Exception {
        var index=start(4);var failure=new AtomicReference<Throwable>();
        var other=new Thread(()->{try {index.end(manager);} catch(Throwable error) {failure.set(error);}});
        other.start();other.join(3000);assertFalse(other.isAlive());assertInstanceOf(IllegalStateException.class,failure.get());
        assertFalse(index.idle());assertThrows(IllegalStateException.class,()->index.end(manager));
    }
    @Test void malformedOrOversizedLineagePoisonsTheIndexBeforeRetention() {
        for(String id:new String[]{null,"missing_namespace","thermal:bad space","thermal:"+"a".repeat(256)}) {
            var index=start(1);
            assertThrows(IllegalStateException.class,()->index.enter(manager,id,source(new Object(),"thermal:one"),"direct"));
            assertFalse(index.idle());
            var converted=start(1);
            assertThrows(IllegalStateException.class,()->converted.converted(manager,new Object(),source(new Object(),id)));
            assertFalse(converted.idle());
        }
    }
}
