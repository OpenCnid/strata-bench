import { Vec3 } from 'vec3';
import type { Block } from 'prismarine-block';
import type { Bot } from 'mineflayer';
import { utc, type StructuredState } from './protocol.js';

export const key = (p: Vec3): string => `${Math.floor(p.x)},${Math.floor(p.y)},${Math.floor(p.z)}`;
export const id = (name: string): string => name.includes(':') ? name : `minecraft:${name}`;

/** Conservative voxel traversal: even transparent occupied cells occlude the next cell. */
export function trace(origin: Vec3, direction: Vec3, radius: number, read: (p: Vec3) => Block | null): Block[] {
  const d = direction.normalize();
  const p = origin.floored();
  const axes = ['x', 'y', 'z'] as const;
  const step = axes.map(a => Math.sign(d[a]));
  const delta = axes.map(a => d[a] === 0 ? Infinity : Math.abs(1 / d[a]));
  const next = axes.map((a, i) => d[a] === 0 ? Infinity :
    ((step[i]! > 0 ? p[a] + 1 : p[a]) - origin[a]) / d[a]);
  const result: Block[] = [];
  for (let n = 0; n < 96; n++) {
    const block = read(p.clone());
    if (!block) break;
    result.push(block);
    if (block.name !== 'air' && block.name !== 'cave_air' && block.name !== 'void_air') break;
    const distance = Math.min(...next);
    if (distance > radius || !Number.isFinite(distance)) break;
    // Supercover: stop at edge/corner ties; do not look through a diagonal crack.
    const crossings = next.filter(v => Math.abs(v - distance) < 1e-9).length;
    if (crossings !== 1) break;
    const index = next.indexOf(distance);
    p[axes[index]!] += step[index]!; next[index]! += delta[index]!;
  }
  return result;
}

export class ObservedMap {
    private cells = new Map<string, {block: Block; at: string}>();
    private dimension = '';
    private anchor: Vec3 | null = null;
  constructor(private read: (p: Vec3) => Block | null) {}
  reset(): void { this.cells.clear(); this.anchor = null; this.dimension = ''; }
  blockAt = (p: Vec3): Block | null => this.cells.get(key(p))?.block ?? null;
  capture(eye: Vec3, dimension: string): {block: Block; at: string}[] {
    if (dimension !== this.dimension) { this.reset(); this.dimension = dimension; }
    // Own-body geometry only. Capture still cannot promote an undisclosed block.
    this.anchor = eye.clone();
    const candidates = new Map<string, {block: Block; at: string}>();
    const now = utc();
    const ray = (d: Vec3) => {
      for (const block of trace(eye, d, 16, this.read)) {
        if (eye.distanceTo(block.position.offset(.5,.5,.5)) <= 16) candidates.set(key(block.position), {block, at: now});
      }
    };
    // Fixed rays; no adaptive search for ores or hidden state. Pin in capability policy.
    for (let i = 0; i < 256; i++) {
      const y = 1 - 2 * (i + 0.5) / 256;
      const a = i * Math.PI * (3 - Math.sqrt(5));
      ray(new Vec3(Math.cos(a) * Math.sqrt(1-y*y), y, Math.sin(a) * Math.sqrt(1-y*y)));
    }
    for (let x = -3; x <= 3; x++) for (let z = -3; z <= 3; z++) ray(new Vec3(x + 0.13, -2.12, z + 0.17));
    const sorted = [...candidates.values()].sort((a,b) =>
      a.block.position.distanceSquared(eye)-b.block.position.distanceSquared(eye) || key(a.block.position).localeCompare(key(b.block.position)));
    return sorted.map(entry => ({at: entry.at,
      block: Object.assign(Object.create(Object.getPrototypeOf(entry.block)), entry.block,
        {position: entry.block.position.clone(), shapes: entry.block.shapes?.map(shape => [...shape]) ?? []}) as Block}));
  }
  project(entries: {block: Block; at: string}[]): StructuredState['nearby_blocks'] {
    return entries.map(({block, at}) => ({position: vector(block.position), block_id: id(block.name), observed_at: at}));
  }
  deliver(entries: {block: Block; at: string}[], dimension: string): void {
    if (dimension !== this.dimension) return;
    for (const entry of entries) {
      const previous = this.cells.get(key(entry.block.position));
      // An old page cannot overwrite knowledge from a newer delivered snapshot.
      if (previous && previous.at > entry.at) continue;
      this.cells.delete(key(entry.block.position));
      this.cells.set(key(entry.block.position), entry);
    }
    if (this.cells.size > 1024 && this.anchor) {
      const anchor = this.anchor;
      // Far pages must not evict the nearby floor/head cells needed to walk.
      // Retain only already delivered cells, with the same fixed capacity.
      this.cells = new Map([...this.cells].sort(([ka,a],[kb,b]) =>
        a.block.position.distanceSquared(anchor)-b.block.position.distanceSquared(anchor) || ka.localeCompare(kb))
        .slice(0,1024));
    }
  }
  scan(eye: Vec3, dimension: string): StructuredState['nearby_blocks'] {
    const entries = this.capture(eye, dimension).slice(0, 128);
    this.deliver(entries, dimension);
    return this.project(entries);
  }
  visible(eye: Vec3, target: Vec3): boolean {
    if (eye.distanceTo(target) > 16) return false;
    const cells = trace(eye, target.minus(eye), eye.distanceTo(target), this.read);
    return cells.some(b => key(b.position) === key(target));
  }
}
export const vector = (p: Vec3) => ({x: p.x, y: p.y, z: p.z});
export function slots(items: Bot['inventory']['slots']): StructuredState['inventory'] {
  return items.map((item, slot) => ({slot, item_id: item ? id(item.name) : null,
    count: item?.count ?? 0, component_summary: {}}));
}
