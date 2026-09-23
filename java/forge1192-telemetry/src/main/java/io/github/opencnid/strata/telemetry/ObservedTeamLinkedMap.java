package io.github.opencnid.strata.telemetry;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.function.BiFunction;
import java.util.function.Function;

/** Preserve insertion order of the two exposed FTB manager maps. */
public final class ObservedTeamLinkedMap<K,V> extends LinkedHashMap<K,V> {
    private void writing(Object key) { SetupHistory.attempt("team_map_write"); }
    private void clearing() { writing(null); }
    @Override public V put(K key,V value) { writing(key); return super.put(key,value); }
    @Override public V putIfAbsent(K key,V value) { writing(key); return super.putIfAbsent(key,value); }
    @Override public void putAll(Map<? extends K,? extends V> map) {
        map.keySet().forEach(this::writing); super.putAll(map);
    }
    @Override public V remove(Object key) { writing(key); return super.remove(key); }
    @Override public boolean remove(Object key,Object value) { writing(key); return super.remove(key,value); }
    @Override public V replace(K key,V value) { writing(key); return super.replace(key,value); }
    @Override public boolean replace(K key,V oldValue,V value) {
        writing(key); return super.replace(key,oldValue,value);
    }
    @Override public V computeIfAbsent(K key,Function<? super K,? extends V> f) {
        writing(key); return super.computeIfAbsent(key,f);
    }
    @Override public V computeIfPresent(K key,BiFunction<? super K,? super V,? extends V> f) {
        writing(key); return super.computeIfPresent(key,f);
    }
    @Override public V compute(K key,BiFunction<? super K,? super V,? extends V> f) {
        writing(key); return super.compute(key,f);
    }
    @Override public V merge(K key,V value,BiFunction<? super V,? super V,? extends V> f) {
        writing(key); return super.merge(key,value,f);
    }
    @Override public void replaceAll(BiFunction<? super K,? super V,? extends V> f) {
        java.util.Objects.requireNonNull(f);
        super.replaceAll((key,value)->{ writing(key); return f.apply(key,value); });
    }
    @Override public void clear() { clearing(); super.clear(); }
    @Override public Object clone() { return new LinkedHashMap<K,V>(this); }
    @Override public Set<Map.Entry<K,V>> entrySet() {
        return ObservedMapViews.entries(super.entrySet(),this::writing,this::clear);
    }
    @Override public Set<K> keySet() { return ObservedMapViews.keys(this); }
    @Override public Collection<V> values() { return ObservedMapViews.values(this); }
}
