package io.github.opencnid.strata.telemetry;

import java.util.AbstractCollection;
import java.util.AbstractSet;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.function.BiFunction;
import java.util.function.Function;

/** Observe writes to the three immutable-valued pack-mode keys, never their contents. */
public final class ObservedGlobalMap extends HashMap<String, Object> {
    private void writing(Object key) {
        if ("packmode".equals(key) || "isExpertMode".equals(key) || "isNormalMode".equals(key))
            SetupHistory.attempt("global_mode_write");
    }
    @Override public Object put(String key, Object value) { writing(key); return super.put(key,value); }
    @Override public Object putIfAbsent(String key, Object value) { writing(key); return super.putIfAbsent(key,value); }
    @Override public void putAll(Map<? extends String, ?> map) {
        map.keySet().forEach(this::writing); super.putAll(map);
    }
    @Override public Object remove(Object key) { writing(key); return super.remove(key); }
    @Override public boolean remove(Object key,Object value) { writing(key); return super.remove(key,value); }
    @Override public Object replace(String key,Object value) { writing(key); return super.replace(key,value); }
    @Override public boolean replace(String key,Object oldValue,Object value) {
        writing(key); return super.replace(key,oldValue,value);
    }
    @Override public Object computeIfAbsent(String key,Function<? super String,?> f) {
        writing(key); return super.computeIfAbsent(key,f);
    }
    @Override public Object computeIfPresent(String key,BiFunction<? super String,? super Object,?> f) {
        writing(key); return super.computeIfPresent(key,f);
    }
    @Override public Object compute(String key,BiFunction<? super String,? super Object,?> f) {
        writing(key); return super.compute(key,f);
    }
    @Override public Object merge(String key,Object value,BiFunction<? super Object,? super Object,?> f) {
        writing(key); return super.merge(key,value,f);
    }
    @Override public void replaceAll(BiFunction<? super String,? super Object,?> f) {
        java.util.Objects.requireNonNull(f);
        super.replaceAll((key,value)->{ writing(key); return f.apply(key,value); });
    }
    @Override public void clear() { SetupHistory.attempt("global_mode_write"); super.clear(); }
    // A clone is detached, not another path to mutate the live GLOBAL object.
    @Override public Object clone() { return new HashMap<String,Object>(this); }

    @Override public Set<Map.Entry<String,Object>> entrySet() {
        var entries = super.entrySet();
        return new AbstractSet<>() {
            public int size() { return entries.size(); }
            public void clear() { ObservedGlobalMap.this.clear(); }
            public Iterator<Map.Entry<String,Object>> iterator() {
                var inner=entries.iterator();
                return new Iterator<>() {
                    private Map.Entry<String,Object> current;
                    public boolean hasNext() { return inner.hasNext(); }
                    public Map.Entry<String,Object> next() {
                        var entry=inner.next(); current=entry;
                        return new Map.Entry<>() {
                            public String getKey() { return entry.getKey(); }
                            public Object getValue() { return entry.getValue(); }
                            public Object setValue(Object value) { writing(entry.getKey()); return entry.setValue(value); }
                            public boolean equals(Object other) { return entry.equals(other); }
                            public int hashCode() { return entry.hashCode(); }
                            public String toString() { return entry.toString(); }
                        };
                    }
                    public void remove() {
                        if(current!=null) writing(current.getKey());
                        inner.remove(); current=null;
                    }
                };
            }
        };
    }
    private <T> Iterator<T> projected(Function<Map.Entry<String,Object>,T> project) {
        var inner=entrySet().iterator();
        return new Iterator<>() {
            public boolean hasNext() { return inner.hasNext(); }
            public T next() { return project.apply(inner.next()); }
            public void remove() { inner.remove(); }
        };
    }
    @Override public Set<String> keySet() {
        return new AbstractSet<>() {
            public int size() { return ObservedGlobalMap.this.size(); }
            public boolean contains(Object key) { return containsKey(key); }
            public void clear() { ObservedGlobalMap.this.clear(); }
            public Iterator<String> iterator() { return projected(Map.Entry::getKey); }
        };
    }
    @Override public Collection<Object> values() {
        return new AbstractCollection<>() {
            public int size() { return ObservedGlobalMap.this.size(); }
            public boolean contains(Object value) { return containsValue(value); }
            public void clear() { ObservedGlobalMap.this.clear(); }
            public Iterator<Object> iterator() { return projected(Map.Entry::getValue); }
        };
    }
}
