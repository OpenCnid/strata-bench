import { ACTION_KINDS } from './adapter.js';
import { digest } from './protocol.js';
import { hashFile, implementationPins } from './capability_pins.js';
import { MENU_CLOSE_POLICY } from './menu_close.js';
import { BODY_REVISION_POLICY } from './body_revision.js';
import { PRIMITIVE_ACCOUNTING_POLICY } from './journal.js';

const sourcePins = implementationPins();
const schemaPins = Object.fromEntries(['ActionBatch','ActionAck','Observation','RpcRequest']
  .map(name => [name, hashFile(new URL(`../../../../schemas/v1/public/${name}.json`, import.meta.url))]));

export const capabilityManifest = {
  schema: 'strata/Capabilities/1', contract_minor: 11, profile: 'vanilla-development/1', track: 'structured-actions/v1',
  backend: 'mineflayer', minecraft: '1.19.2', node: '24.19.0', mineflayer: '4.39.0',
  implementation_digest: digest(sourcePins), schema_digest: digest(schemaPins),
  dependency_lock_digest: hashFile(new URL('../../package-lock.json', import.meta.url)),
  auth_cache_acl_digest: hashFile(new URL('../../tools/auth_cache_acl.py', import.meta.url)),
  pathfinder: '2.4.5', protocol: '1.68.0', minecraft_data: '3.116.0',
  actions: ACTION_KINDS, keybindings: false, screenshots: false, wait_events: true,
  public_signals: {policy: 'player-events/1', ring: 128, delivery_limit: 32, max_wait_ms: 3000},
  action_restrictions: {equip: ['closed_container','explicit_source','fixed_selected_hotbar_destination','server_resync_each_click'], interact_block: ['chest','barrel','furnace','crafting_table'],
    close_window: {policy:MENU_CLOSE_POLICY,wait_tick_ms:50,completion:'emitted-input-only'},
    use_item: ['max_hold_2000ms','main_or_off_hand','closed_container','emitted_input_only'],
    attack: ['previously_delivered_identity','visible_within_3_blocks','one_attack','emitted_input_only'],
    interact_entity: ['previously_delivered_identity','visible_within_3_blocks','normal_main_hand_use','emitted_input_only'],
    chat: ['ordinary_single_message','max_256_utf16_units','no_commands_or_controls','emitted_input_only'],
    place: ['observed_air_destination','same_named_vanilla_block'],
    craft: ['server_unlocked_shaped_or_shapeless','selected_recipe_definition_and_authorization/1','plain_ingredients_plain_or_fresh_damage0_output/2','no_remainders','empty_grid_and_output_slot','server_resync_each_click'],
    click_slot: ['left_or_right_pickup_or_quick_move','inventory_crafting_furnace_generic_windows',
      'crafting_output_requires_craft_action','server_resync_required','cursor_and_full_item_conservation']},
  recipes: {source: 'server-unlocked-recipe-book/1', page_limit: 32, response_bytes: 32768}, quests: false, forge: false,
  observation: {policy: 'opaque-voxel-rays/1', radius: 16, entries: 128, snapshot_bytes: 65536,
    body_revision_policy: BODY_REVISION_POLICY,
    deliveries_per_second: 2, map_cells: 1024, map_retention:'delivered-nearest-captured-eye/1', components: [], pagination: true,
    page_policy: 'captured-region/1', cursor_ttl_ms: 30000, cached_regions: 4,
    max_captured_entries_per_kind: 16384},
  motor: {policy: 'flat-walk/1', planning_ms: 20, can_dig: false, can_place: false,
    automatic_equipment: false, parkour: false, sprint: false, doors: false},
  limits: {movement_ms: 30000, action_ms: 10000, observation_age_ms: 2000},
  release: {policy: 'confirmed-local-release/2', timeout_ms: 250, fence_on_stop_all: true},
  primitive_accounting: {policy:PRIMITIVE_ACCOUNTING_POLICY, emission_confirmation:false},
  conformance: 'unverified', campaign_admission: false,
};
export const capabilityDigest = digest(capabilityManifest);
