import type { Entity } from 'prismarine-entity';
import { Vec3 } from 'vec3';
import { requireThat } from './protocol.js';

/** Entity IDs authorize only previously projected identities, never registry guesses. */
export class ObservedEntities {
  private seen = new Map<string, {entity: Entity; dimension: string; captured: number}>();
  reset(): void { this.seen.clear(); }
  deliver(entities: Entity[], dimension: string, captured: number): void {
    for (const entity of entities) {
      const key = String(entity.id);
      if ((this.seen.get(key)?.captured ?? -1) > captured) continue;
      this.seen.delete(key); this.seen.set(key, {entity, dimension, captured});
    }
    while (this.seen.size > 1024) this.seen.delete(this.seen.keys().next().value!);
  }
  target(id: string, dimension: string, read: (id: number) => Entity | undefined,
    eye: Vec3, visible: (eye: Vec3, target: Vec3) => boolean): Entity {
    const known = this.seen.get(id);
    requireThat(known && known.dimension === dimension && read(known.entity.id) === known.entity, 'PRECONDITION_FAILED');
    const entity = known.entity;
    const point = entity.position.offset(0, Math.min(entity.height / 2, 1), 0);
    requireThat(eye.distanceTo(point) <= 3 && visible(eye, point), 'PRECONDITION_FAILED');
    return entity;
  }
}
