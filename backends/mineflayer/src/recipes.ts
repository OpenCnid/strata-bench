import { Fault, requireThat } from './protocol.js';
import { isDeepStrictEqual } from 'node:util';

type Slot = {present: boolean; itemId?: number; itemCount?: number; nbtData?: unknown};
type DeclaredRecipe = {type: string; recipeId: string; data?: {
  width?: number; height?: number; ingredients?: Slot[][] | Slot[][][]; result?: Slot;
}};
export interface Recipe {
  recipe_id: string; serializer: string; width: number; height: number;
  ingredients: number[][]; result: {type: number; count: number; nbt?: unknown};
}
export interface RecipeInventoryItem {type: number; count: number; nbt?: unknown}
export interface RecipeBinding {recipe: Recipe; authorization: number}
const namespaced = /^[a-z0-9_.-]+:[a-z0-9_./-]+$/;
export const FRESH_TOOL_NBT = {type:'compound',name:'',value:{Damage:{type:'int',value:0}}};

/** 1.19.2 declaration/unlock packet shapes inspected in the pinned minecraft-data protocol.
 * Raw declarations stay private. Only server-unlocked, supported recipes are projected.
 * This is not the global minecraft-data recipe table and does not qualify Forge serializers.
 */
export class RecipeBook {
  private declared = new Map<string, Recipe | null>();
  private unlocked = new Set<string>();
  private authorizations = new Map<string, number>();
  revision = 0;
  constructor(private readonly itemName: (id: number) => string | undefined,
    private readonly durability: (id:number) => number | undefined = () => undefined) {}
  private slot(slot: Slot, output = false): Recipe['result'] {
    requireThat(slot?.present === true && Number.isSafeInteger(slot.itemId) && slot.itemId! >= 0 &&
      Number.isSafeInteger(slot.itemCount) && slot.itemCount! > 0 && slot.itemCount! <= 64,
      'REGISTRY_UNSUPPORTED');
    requireThat(this.itemName(slot.itemId!) !== undefined, 'REGISTRY_UNSUPPORTED');
    if (slot.nbtData != null) {
      // Fresh vanilla damageable outputs carry their ordinary Damage=0 tag.
      // No tagged ingredients, enchantments, names or altered damage are admitted.
      requireThat(output && slot.itemCount === 1 && (this.durability(slot.itemId!) ?? 0) > 0
        && isDeepStrictEqual(slot.nbtData, FRESH_TOOL_NBT), 'MECHANIC_UNSUPPORTED');
      return {type:slot.itemId!,count:1,nbt:structuredClone(slot.nbtData)};
    }
    return {type:slot.itemId!,count:slot.itemCount!};
  }
  declare(packet: {recipes: DeclaredRecipe[]}): void {
    requireThat(Array.isArray(packet.recipes) && packet.recipes.length <= 10000, 'REGISTRY_UNSUPPORTED');
    const next = new Map<string, Recipe | null>();
    for (const entry of packet.recipes) {
      requireThat(typeof entry.recipeId === 'string' && entry.recipeId.length <= 256 &&
        namespaced.test(entry.recipeId) && !next.has(entry.recipeId), 'REGISTRY_UNSUPPORTED');
      try {
        requireThat(['minecraft:crafting_shapeless','minecraft:crafting_shaped'].includes(entry.type), 'MECHANIC_UNSUPPORTED');
        const data = entry.data!;
        requireThat(data && Array.isArray(data.ingredients), 'REGISTRY_UNSUPPORTED');
        const shaped = entry.type === 'minecraft:crafting_shaped';
        const width = shaped ? data.width! : 0;
        const height = shaped ? data.height! : 0;
        requireThat(!shaped || (Number.isInteger(width) && width >= 1 && width <= 3 &&
          Number.isInteger(height) && height >= 1 && height <= 3), 'MECHANIC_UNSUPPORTED');
        // The pinned decoder groups the linear wire ingredients by width/height.
        // Flatten once, then index the protocol's row-major width during placement.
        const ingredients = (shaped ? data.ingredients.flat() : data.ingredients) as Slot[][];
        requireThat(ingredients.length > 0 && ingredients.length <= 9 &&
          (!shaped || ingredients.length === width * height), 'MECHANIC_UNSUPPORTED');
        const choices = ingredients.map(options => {
          requireThat(Array.isArray(options) && options.length <= 16, 'MECHANIC_UNSUPPORTED');
          requireThat(shaped || options.length > 0, 'MECHANIC_UNSUPPORTED');
          return [...new Set(options.map(s => {
            const item = this.slot(s); requireThat(item.count === 1, 'MECHANIC_UNSUPPORTED');
            const name = this.itemName(item.type)!;
            requireThat(!name.endsWith('_bucket') && name !== 'honey_bottle', 'MECHANIC_UNSUPPORTED');
            return item.type;
          }))].sort((a,b) => a-b);
        });
        requireThat(choices.some(options => options.length > 0), 'MECHANIC_UNSUPPORTED');
        next.set(entry.recipeId, {recipe_id: entry.recipeId, serializer: entry.type,
          width, height, ingredients: choices, result: this.slot(data.result!,true)});
      } catch (error) {
        if (!(error instanceof Fault)) throw error;
        next.set(entry.recipeId, null); // unsupported is retained, never replaced with vanilla data
      }
    }
    this.declared = next; this.revision++;
  }
  unlock(packet: {action: number; recipes1: string[]}): void {
    requireThat([0,1,2].includes(packet.action) && Array.isArray(packet.recipes1) &&
      packet.recipes1.length <= 10000 && packet.recipes1.every(id => typeof id === 'string' &&
        id.length <= 256 && namespaced.test(id)), 'REGISTRY_UNSUPPORTED');
    if (packet.action === 0) { this.unlocked.clear(); this.authorizations.clear(); }
    for (const id of packet.recipes1) {
      if (packet.action === 2) { this.unlocked.delete(id); this.authorizations.delete(id); }
      else if (!this.unlocked.has(id)) {
        this.unlocked.add(id); this.authorizations.set(id, this.revision + 1);
      }
    }
    this.revision++;
  }
  get(id: string): Recipe {
    requireThat(this.unlocked.has(id), 'FORBIDDEN');
    const recipe = this.declared.get(id);
    requireThat(recipe, 'MECHANIC_UNSUPPORTED');
    return recipe;
  }
  bind(id: string): RecipeBinding {
    return {recipe: this.get(id), authorization: this.authorizations.get(id)!};
  }
  validate(binding: RecipeBinding): void {
    requireThat(this.get(binding.recipe.recipe_id) === binding.recipe &&
      this.authorizations.get(binding.recipe.recipe_id) === binding.authorization, 'REVISION_CONFLICT');
  }
  list(after: number): unknown {
    const ids = [...this.unlocked].sort();
    requireThat(Number.isSafeInteger(after) && after >= 0 && after <= ids.length, 'OUT_OF_ORDER');
    const recipes = [];
    let cursor = after;
    for (; cursor < ids.length && recipes.length < 32; cursor++) {
      const recipe = this.declared.get(ids[cursor]!);
      const projection = recipe ? {recipe_id: recipe.recipe_id, serializer: recipe.serializer,
        supported: true, width: recipe.width, height: recipe.height,
        ingredients: recipe.ingredients.map(options => options.map(id => `minecraft:${this.itemName(id)}`)),
        result: {item_id: `minecraft:${this.itemName(recipe.result.type)}`, count: recipe.result.count,
          ...(recipe.result.nbt ? {component_summary:{damage:0}} : {})}}
        : {recipe_id: ids[cursor], supported: false};
      if (Buffer.byteLength(JSON.stringify([...recipes, projection])) > 32768) break;
      recipes.push(projection);
    }
    return {revision: this.revision, recipes, next_cursor: cursor < ids.length ? cursor : null};
  }
  select(recipe: Recipe, items: (RecipeInventoryItem | null)[], gridWidth: number): (number | null)[] {
    requireThat(gridWidth === 2 || gridWidth === 3, 'MECHANIC_UNSUPPORTED');
    requireThat(recipe.width <= gridWidth && recipe.height <= gridWidth &&
      recipe.ingredients.length <= gridWidth * gridWidth, 'PRECONDITION_FAILED');
    const counts = new Map<number, number>();
    for (const item of items) if (item && item.nbt == null) counts.set(item.type, (counts.get(item.type) ?? 0) + item.count);
    const chosen: (number | null)[] = [];
    let attempts = 0;
    const choose = (index: number): boolean => {
      requireThat(++attempts <= 4096, 'MECHANIC_UNSUPPORTED');
      if (index === recipe.ingredients.length) return true;
      const alternatives = recipe.ingredients[index]!;
      if (!alternatives.length) { chosen[index] = null; return choose(index + 1); }
      for (const type of alternatives) if ((counts.get(type) ?? 0) > 0) {
        counts.set(type, counts.get(type)! - 1); chosen[index] = type;
        if (choose(index + 1)) return true;
        counts.set(type, counts.get(type)! + 1);
      }
      return false;
    };
    requireThat(choose(0), 'PRECONDITION_FAILED');
    const cells: (number | null)[] = Array(gridWidth * gridWidth).fill(null);
    chosen.forEach((type, index) => {
      const slot = recipe.width ? Math.floor(index / recipe.width) * gridWidth + index % recipe.width : index;
      cells[slot] = type;
    });
    return cells;
  }
}
