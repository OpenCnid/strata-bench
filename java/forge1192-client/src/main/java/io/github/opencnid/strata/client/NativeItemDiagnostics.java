package io.github.opencnid.strata.client;

import java.util.LinkedHashMap;
import java.util.TreeSet;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;

/** Bounded operator-only failure diagnosis. Never changes item comparison or exports values. */
final class NativeItemDiagnostics {
    private static final LinkedHashMap<String,CompoundTag> snapshots = new LinkedHashMap<>();
    static synchronized void remember(String hash, CompoundTag tag) {
        if (snapshots.containsKey(hash)) return;
        if (snapshots.size() == 128) snapshots.remove(snapshots.keySet().iterator().next());
        snapshots.put(hash,tag.copy());
    }
    static synchronized void mismatch(GameInventory.View reply, GameInventory.View current) {
        int[] remaining = {16};
        for (int i=0;i<Math.min(reply.slots().size(),current.slots().size()) && remaining[0]>0;i++) {
            var a=reply.slots().get(i);var b=current.slots().get(i);
            if (i==reply.resultSlot() || a.equals(b)) continue;
            var before=snapshots.get(a.components());var after=snapshots.get(b.components());
            if (before!=null && after!=null) diff(before,after,"slot"+i,0,remaining);
        }
    }
    private static void diff(Tag a, Tag b, String path, int depth, int[] remaining) {
        if (java.util.Objects.equals(a,b) || remaining[0]<=0) return;
        if (depth<8 && a instanceof CompoundTag left && b instanceof CompoundTag right) {
            var keys=new TreeSet<>(left.getAllKeys());keys.addAll(right.getAllKeys());
            for(String key:keys) {
                // No arbitrary tag text or component value enters the log.
                String safe=key.matches("[A-Za-z0-9_:.-]{1,64}")?key:"key_sha256_"+KeyOptions.sha256(key);
                diff(left.get(key),right.get(key),path+"/"+safe,depth+1,remaining);
                if(remaining[0]<=0) break;
            }
        } else {
            remaining[0]--;
            System.getLogger(NativeItemDiagnostics.class.getName()).log(System.Logger.Level.WARNING,
                "STRATA_ITEM_COMPONENT_DIFFERENCE path="+path+" reply_type="+(a==null?-1:a.getId())
                +" current_type="+(b==null?-1:b.getId())+" reply_sha256="+hash(a)+" current_sha256="+hash(b));
        }
    }
    private static String hash(Tag tag) { return tag==null?"absent":KeyOptions.sha256(tag.toString()); }
    private NativeItemDiagnostics() {}
}
