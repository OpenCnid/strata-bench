package io.github.opencnid.strata.telemetry;

import java.util.IdentityHashMap;
import java.util.regex.Pattern;

/** Bounded observed object lineage. Equality or matching outputs never binds recipes. */
final class RecipeRegistrationIndex {
    private static final Pattern NAME=Pattern.compile("[a-z0-9_.-]+:[a-z0-9_./-]+");
    record Source(Object recipe, String id, String type, String serializer) {}
    record Entry(Source source, String machineId, String origin, long generation) {}
    private final int limit;
    private final IdentityHashMap<Object,Source> converted = new IdentityHashMap<>();
    private final IdentityHashMap<Object,Entry> internals = new IdentityHashMap<>();
    private Object manager, registry;
    private Thread owner;
    private long generation;
    private boolean refreshing, cleared, ready, broken;
    private Entry pending;

    RecipeRegistrationIndex(int limit) {
        if(limit<1 || limit>65536) throw new IllegalArgumentException("MACHINE_REGISTRATION_QUOTA");
        this.limit=limit;
    }
    synchronized void begin(Object manager, Object registry) {
        if(broken || refreshing || manager==null || registry==null || generation>=9007199254740991L) fail();
        this.manager=manager;this.registry=registry;owner=Thread.currentThread();
        generation++;refreshing=true;cleared=false;ready=false;pending=null;
        converted.clear();internals.clear();
    }
    synchronized void clear(Object manager) {
        if(broken) fail();
        if(refreshing) {
            requireOwner(manager);
            if(cleared || pending!=null) fail();
            cleared=true;
        } else {
            // An out-of-refresh native clear invalidates everything immediately.
            ready=false;this.manager=null;registry=null;
        }
        converted.clear();internals.clear();
    }
    synchronized void converted(Object manager, Object machineRecipe, Source source) {
        requireOwner(manager);
        if(!cleared || pending!=null || machineRecipe==null || source==null
                || converted.containsKey(machineRecipe) || converted.size()>=limit) fail();
        source(source);
        converted.put(machineRecipe,source);
    }
    synchronized Source conversion(Object manager,Object machineRecipe) {
        requireOwner(manager);return converted.get(machineRecipe);
    }
    synchronized void enter(Object manager, String machineId, Source source, String origin) {
        requireOwner(manager);
        if(!cleared || pending!=null || source==null || !name(machineId)
                || !"direct".equals(origin) && !"converted_cooking".equals(origin)) fail();
        source(source);
        pending=new Entry(source,machineId,origin,generation);
    }
    synchronized void returned(Object manager,Object internal) {
        requireOwner(manager);
        if(pending==null) fail();
        if(internal==null) return; // Native rejection creates no identity binding.
        if(internals.containsKey(internal) || internals.size()>=limit) fail();
        internals.put(internal,pending);
    }
    synchronized void leave(Object manager) {
        requireOwner(manager);if(pending==null) fail();pending=null;
    }
    synchronized void end(Object manager) {
        requireOwner(manager);if(!cleared || pending!=null) fail();
        refreshing=false;ready=true;owner=null;
    }
    synchronized Entry lookup(Object manager,Object registry,Object internal) {
        if(broken || !ready || refreshing || this.manager!=manager || this.registry!=registry) return null;
        return internals.get(internal);
    }
    synchronized boolean idle() { return !broken && !refreshing && pending==null; }
    synchronized void poison() { broken=true;ready=false; }
    private void requireOwner(Object manager) {
        if(broken || !refreshing || this.manager!=manager || owner!=Thread.currentThread()) fail();
    }
    private void source(Source source) {
        if(source.recipe()==null || !name(source.id()) || !name(source.type()) || !name(source.serializer())) fail();
    }
    private static boolean name(String value) { return value!=null && value.length()<=256 && NAME.matcher(value).matches(); }
    private void fail() { broken=true;ready=false;throw new IllegalStateException("MACHINE_REGISTRATION_LIFETIME"); }
}
