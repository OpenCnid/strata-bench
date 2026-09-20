import type { Bot } from 'mineflayer';
import { RecipeBook } from './recipes.js';
import { requireThat, type Action } from './protocol.js';

/** Fixed slot motor for one explicitly requested, server-unlocked recipe.
 * Every click is followed by pinned Mineflayer server resynchronization. No
 * recipe chains, ingredient acquisition, private recipes or client-predicted
 * outputs are accepted as completion.
 */
export async function craft(bot: Bot, book: RecipeBook, action: Extract<Action, {kind:'craft'}>,
  revision: number, guard: () => void, emit: () => void): Promise<void> {
  requireThat(action.recipe_selection == null, 'CAPABILITY_MISSING');
  const window = bot.currentWindow ?? bot.inventory;
  requireThat(window.id === action.window_id && revision === action.expected_window_revision, 'REVISION_CONFLICT');
  const width = window === bot.inventory ? 2 : window.type === 'minecraft:crafting' ? 3 : 0;
  requireThat(width > 0, 'MECHANIC_UNSUPPORTED');
  const syncBot = bot as Bot & {_syncWindow?: (w: typeof window) => Promise<void>};
  requireThat(typeof syncBot._syncWindow === 'function', 'MECHANIC_UNSUPPORTED');
  const recipe = book.get(action.recipe_id);
  const bookRevision = book.revision;
  const check = () => {
    guard(); requireThat((bot.currentWindow ?? bot.inventory) === window && book.revision === bookRevision,
      'REVISION_CONFLICT');
  };
  const inventory = () => window.slots.slice(window.inventoryStart, window.inventoryEnd);
  const cursor = () => window.selectedItem;
  const totals = () => {
    const result = new Map<number,number>();
    for (const item of inventory()) if (item) result.set(item.type, (result.get(item.type) ?? 0) + item.count);
    return result;
  };
  const click = async (slot: number, button: number) => {
    check(); emit(); await bot.clickWindow(slot, button, 0); check();
    emit(); await syncBot._syncWindow!(window); check();
  };
  for (let iteration=0; iteration<action.count; iteration++) {
    check(); requireThat(!window.selectedItem && window.slots.slice(0,width*width+1).every(s => !s), 'PRECONDITION_FAILED');
    // Reserve one empty destination for the output. No implicit drop/rearrange routine.
    const destination = window.slots.findIndex((item,index) => !item && index >= window.inventoryStart && index < window.inventoryEnd);
    requireThat(destination >= 0, 'PRECONDITION_FAILED');
    const selected = book.select(recipe, inventory(), width);
    const before = totals();
    const expected = new Map(before);
    for (const type of selected) if (type !== null) expected.set(type, expected.get(type)! - 1);
    expected.set(recipe.result.type, (expected.get(recipe.result.type) ?? 0) + recipe.result.count);
    for (let index=0; index<selected.length; index++) {
      const type = selected[index];
      if (type === null) continue;
      const source = window.slots.findIndex((item,slot) => slot >= window.inventoryStart &&
        slot < window.inventoryEnd && item !== null && item.type === type && item.nbt == null);
      requireThat(source >= 0 && !window.selectedItem && !window.slots[index+1], 'PRECONDITION_FAILED');
      await click(source,0);
      requireThat(cursor()?.type === type, 'PRECONDITION_FAILED');
      await click(index+1,1);
      requireThat(window.slots[index+1]?.type === type && window.slots[index+1]?.count === 1, 'PRECONDITION_FAILED');
      if (window.selectedItem) await click(source,0);
      requireThat(!window.selectedItem, 'PRECONDITION_FAILED');
    }
    requireThat(window.slots[0]?.type === recipe.result.type && window.slots[0]?.count === recipe.result.count,
      'PRECONDITION_FAILED');
    await click(0,0); // server-produced output, not an invented local recipe result
    requireThat(cursor()?.type === recipe.result.type && cursor()?.count === recipe.result.count,
      'PRECONDITION_FAILED');
    await click(destination,0);
    requireThat(!window.selectedItem && window.slots.slice(0,width*width+1).every(s => !s), 'PRECONDITION_FAILED');
    const after = totals();
    requireThat([...new Set([...before.keys(), ...expected.keys(), ...after.keys()])]
      .every(type => (after.get(type) ?? 0) === (expected.get(type) ?? 0)), 'PRECONDITION_FAILED');
  }
}
