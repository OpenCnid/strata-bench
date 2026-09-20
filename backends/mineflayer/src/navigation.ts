import { EventEmitter } from 'node:events';
import type { Bot } from 'mineflayer';
import pathfinderModule from 'mineflayer-pathfinder';
import type { ComputedPath } from 'mineflayer-pathfinder';
import { Vec3 } from 'vec3';
import { ObservedMap } from './observations.js';
import { requireThat } from './protocol.js';

const {pathfinder, Movements, goals} = pathfinderModule;

/** A planning-only facade has no socket, raw world, or mutation methods. */
export function plan(bot: Bot, map: ObservedMap, target: Vec3, tolerance: number): Vec3[] {
  const minY = (bot.game as typeof bot.game & {minY?: number})?.minY;
  requireThat(typeof minY === 'number' && Number.isSafeInteger(minY), 'CAPABILITY_MISSING');
  const facade = Object.assign(new EventEmitter(), {
    registry: bot.registry,
    // Public dimension geometry is needed even when drops are disallowed: the
    // pinned planner still examines landing candidates while expanding nodes.
    // Never hand it the raw game/world object or undisclosed block access.
    game: {minY},
    entity: {position: bot.entity.position.clone(), onGround: bot.entity.onGround},
    inventory: {items: () => []}, entities: {}, blockAt: map.blockAt,
  }) as unknown as Bot;
  pathfinder(facade);
  const movements = new Movements(facade);
  movements.canDig = false; movements.allow1by1towers = false;
  movements.allowParkour = false; movements.allowSprinting = false;
  movements.allowFreeMotion = false; movements.allowEntityDetection = false;
  movements.canOpenDoors = false; movements.scafoldingBlocks = [];
  movements.maxDropDown = 0; movements.infiniteLiquidDropdownDistance = false;
  const search = facade.pathfinder.getPathFromTo(movements, bot.entity.position,
    new goals.GoalNear(target.x, target.y, target.z, tolerance),
    {optimizePath: false, timeout: 20, tickTimeout: 20, searchRadius: 16});
  const result = search.next().value?.result as ComputedPath | undefined;
  requireThat(result?.status === 'success', 'PATH_BLOCKED');
  // Initial motor supports level, ordinary walking only. Unknown geometry cannot be guessed.
  requireThat(result.path.every(p => p.toBreak.length === 0 && p.toPlace.length === 0 &&
    p.y === Math.floor(bot.entity.position.y)), 'PATH_BLOCKED');
  return result.path.map(p => new Vec3(p.x + 0.5, p.y, p.z + 0.5));
}
