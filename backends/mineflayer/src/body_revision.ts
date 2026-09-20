import type { Bot } from 'mineflayer';

export const BODY_REVISION_POLICY = 'exact-body-pose-motion-ground-dimension/1';

/** Position packets include idle heartbeats. A packet is not itself a body change. */
export function trackBodyRevision(bot: Bot, changed: () => void): {sample(): void; close(): void} {
  const read = (): readonly unknown[] => {
    const entity = bot.entity;
    if (!entity) return [null, bot.game?.dimension];
    return [entity, bot.game?.dimension, entity.position?.x, entity.position?.y, entity.position?.z,
      entity.yaw, entity.pitch, entity.onGround, entity.velocity?.x, entity.velocity?.y, entity.velocity?.z];
  };
  let previous = read();
  const sample = () => {
    const current = read();
    // Exact values: no positional tolerance, rounding, hidden motion or refresh of old observations.
    if (current.length !== previous.length || current.some((value, index) => value !== previous[index])) {
      previous = current;
      changed();
    }
  };
  const events = ['move', 'physicsTick', 'forcedMove', 'spawn'] as const;
  for (const event of events) bot.on(event, sample);
  const close = () => { for (const event of events) bot.off(event, sample); };
  bot.once('end', close);
  return {sample, close};
}
