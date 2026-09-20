import loadItems, { type Item } from 'prismarine-item';
import type { Bot } from 'mineflayer';

/** Decode only the player's carried stack; never expose packet access to agents. */
export function trackCursor(bot: Bot, changed: () => void): () => void {
  const Items = (loadItems as unknown as (registry: Bot['registry']) => typeof Item)(bot.registry);
  const cursor = (packet: {windowId: number; slot: number; item: object}) => {
    if (packet.windowId !== -1 || packet.slot !== -1) return;
    // The pinned inventory plugin ignores window -1; normal server cursor updates
    // must nevertheless invalidate the public window revision before another click.
    (bot.currentWindow ?? bot.inventory).selectedItem = Items.fromNotch(packet.item);
    changed();
  };
  const contents = (packet: {windowId: number; carriedItem?: object}) => {
    if (packet.windowId === (bot.currentWindow ?? bot.inventory).id && packet.carriedItem !== undefined) changed();
  };
  bot._client.on('set_slot', cursor);
  bot._client.on('window_items', contents);
  return () => { bot._client.off('set_slot', cursor); bot._client.off('window_items', contents); };
}
