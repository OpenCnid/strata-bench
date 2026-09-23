package io.github.opencnid.strata.telemetry;

import java.util.AbstractCollection;
import java.util.AbstractSet;
import java.util.Collection;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import java.util.function.Function;

/** Preserve the backing map's order while preventing unobserved mutable view aliases. */
final class ObservedMapViews {
    static <K,V> Set<Map.Entry<K,V>> entries(Set<Map.Entry<K,V>> entries,
            Consumer<Object> writing, Runnable clearing) {
        return new AbstractSet<>() {
            public int size() { return entries.size(); }
            public void clear() { clearing.run(); }
            public Iterator<Map.Entry<K,V>> iterator() {
                var inner=entries.iterator();
                return new Iterator<>() {
                    private Map.Entry<K,V> current;
                    public boolean hasNext() { return inner.hasNext(); }
                    public Map.Entry<K,V> next() {
                        var entry=inner.next(); current=entry;
                        return new Map.Entry<>() {
                            public K getKey() { return entry.getKey(); }
                            public V getValue() { return entry.getValue(); }
                            public V setValue(V value) { writing.accept(entry.getKey()); return entry.setValue(value); }
                            public boolean equals(Object other) { return entry.equals(other); }
                            public int hashCode() { return entry.hashCode(); }
                            public String toString() { return entry.toString(); }
                        };
                    }
                    public void remove() {
                        if(current!=null) writing.accept(current.getKey());
                        inner.remove(); current=null;
                    }
                };
            }
        };
    }
    private static <K,V,T> Iterator<T> projected(Map<K,V> map, Function<Map.Entry<K,V>,T> project) {
        var inner=map.entrySet().iterator();
        return new Iterator<>() {
            public boolean hasNext() { return inner.hasNext(); }
            public T next() { return project.apply(inner.next()); }
            public void remove() { inner.remove(); }
        };
    }
    static <K,V> Set<K> keys(Map<K,V> map) {
        return new AbstractSet<>() {
            public int size() { return map.size(); }
            public boolean contains(Object key) { return map.containsKey(key); }
            public void clear() { map.clear(); }
            public Iterator<K> iterator() { return projected(map,Map.Entry::getKey); }
        };
    }
    static <K,V> Collection<V> values(Map<K,V> map) {
        return new AbstractCollection<>() {
            public int size() { return map.size(); }
            public boolean contains(Object value) { return map.containsValue(value); }
            public void clear() { map.clear(); }
            public Iterator<V> iterator() { return projected(map,Map.Entry::getValue); }
        };
    }
    private ObservedMapViews() {}
}
