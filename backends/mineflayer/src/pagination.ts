import { randomUUID } from 'node:crypto';
import { mono, requireThat, type StructuredState } from './protocol.js';

/** A captured page is private until the gateway journals and projects it. */
export interface Snapshot {
  state: StructuredState;
  captured_mono_ms: number;
  state_revision: number;
  delivered?(): void;
}
export interface Scene extends Snapshot {
  blocks: StructuredState['nearby_blocks'];
  entities: StructuredState['nearby_entities'];
  promote(offset: number): void;
}
interface CachedScene { scene: Scene; cursors: string[] }

/** Opaque, bounded, expiring cursors refer only to an already captured region. */
export class SpatialPages {
  private scenes: CachedScene[] = [];
  private cursors = new Map<string, { entry: CachedScene; page: number }>();
  constructor(private now: () => number = mono) {}
  reset(): void { this.scenes = []; this.cursors.clear(); }
  private prune(): void {
    for (const entry of [...this.scenes]) {
      if (this.now() - entry.scene.captured_mono_ms >= 30000) this.remove(entry);
    }
  }
  private remove(entry: CachedScene): void {
    for (const cursor of entry.cursors) this.cursors.delete(cursor);
    this.scenes = this.scenes.filter(value => value !== entry);
  }
  capture(scene: Scene): Snapshot {
    this.prune();
    requireThat(scene.blocks.length <= 16384 && scene.entities.length <= 16384, 'CAPACITY_EXCEEDED');
    const count = Math.max(1, Math.ceil(Math.max(scene.blocks.length, scene.entities.length) / 128));
    // The snapshot owns its bytes; later live updates cannot mutate pending pages.
    const entry = {scene: {...scene, state: structuredClone(scene.state),
      blocks: structuredClone(scene.blocks), entities: structuredClone(scene.entities)},
      cursors: Array.from({length: count - 1}, () => randomUUID())};
    this.scenes.push(entry);
    entry.cursors.forEach((cursor, index) => this.cursors.set(cursor, {entry, page: index + 1}));
    while (this.scenes.length > 4) this.remove(this.scenes[0]!);
    return this.read(entry, 0);
  }
  page(cursor: string, dimension: string): Snapshot {
    this.prune();
    const found = this.cursors.get(cursor);
    requireThat(found && found.entry.scene.state.dimension === dimension, 'STALE_OBSERVATION');
    return this.read(found.entry, found.page);
  }
  private read(entry: CachedScene, page: number): Snapshot {
    const {scene, cursors} = entry;
    const offset = page * 128;
    const next = cursors[page] ?? null;
    return {captured_mono_ms: scene.captured_mono_ms, state_revision: scene.state_revision,
      state: {...structuredClone(scene.state), nearby_blocks: structuredClone(scene.blocks.slice(offset, offset + 128)),
        nearby_entities: structuredClone(scene.entities.slice(offset, offset + 128)),
        truncated: next !== null, next_cursor: next},
      delivered: () => scene.promote(offset)};
  }
}
