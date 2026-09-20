import { setTimeout as delay } from 'node:timers/promises';
import type { Bot } from 'mineflayer';
import { requireThat, type Action } from './protocol.js';
import type { PrimitiveEmitter } from './actions.js';

/** These are bounded player inputs. An emitted receipt makes no gameplay-success claim. */
export async function useItem(bot: Bot, action: Extract<Action, {kind: 'use_item'}>,
  signal: AbortSignal, guard: () => void, emit: PrimitiveEmitter,
  activate: (offHand: boolean) => void, release: () => void): Promise<'emitted'> {
  guard();
  requireThat(Number.isSafeInteger(action.hold_ms) && action.hold_ms >= 0 && action.hold_ms <= 2000, 'PRECONDITION_FAILED');
  requireThat(!bot.currentWindow && !bot.inventory.selectedItem, 'PRECONDITION_FAILED');
  const item = action.hand === 'main' ? bot.heldItem : bot.inventory.slots[45];
  requireThat(item && item.count > 0 && !bot.usingHeldItem, 'PRECONDITION_FAILED');
  emit();
  try {
    activate(action.hand === 'off');
    if (action.hold_ms) await delay(action.hold_ms, undefined, {signal});
    guard();
  } finally { release(); }
  return 'emitted';
}

export function chat(bot: Bot, text: string, guard: () => void, emit: PrimitiveEmitter): 'emitted' {
  guard();
  // Mineflayer splits UTF-16 strings into 256-unit messages. Reject implicit
  // multiple sends, commands and line/control characters before any emission.
  requireThat(text.length > 0 && text.length <= 256 && !/[\r\n\u0000-\u001f\u007f]/u.test(text) &&
    !text.trimStart().startsWith('/'), 'FORBIDDEN');
  requireThat(!bot.supportFeature('chatCommandsQueuedToMainThread'), 'MECHANIC_UNSUPPORTED');
  emit(); bot.chat(text); return 'emitted';
}
