import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Journal } from '../src/journal.js';
import { Signals } from '../src/signals.js';

test('ordered public signal ring bounds delivery, detects gaps and preserves cursor through restart', async t => {
  const dir = mkdtempSync(join(tmpdir(), 'strata-signals-'));
  let journal = new Journal(dir, 1);
  let signals = new Signals(journal);
  t.after(() => {signals.close(); journal.close(); rmSync(dir, {recursive:true});});
  for (let i=0;i<140;i++) signals.publish('inventory', 'Inventory changed.');
  const page = signals.read(0);
  assert.equal(page.event_gap, true);
  assert.equal(page.signals.length, 32);
  assert.equal(page.signals[0]!.cursor, 13);
  assert.equal(signals.read(44).signals[0]!.cursor, 45);
  assert.throws(() => signals.read(141), /OUT_OF_ORDER/);
  signals.close(); journal.close();
  journal = new Journal(dir, 2); signals = new Signals(journal);
  assert.equal(signals.cursor, 140);
  assert.equal(signals.read(0).event_gap, true);
  signals.publish('connection', 'Connected.');
  assert.equal(signals.read(140).signals[0]!.cursor, 141);
});

test('event waits time out, wake promptly, reject concurrent waits and release on shutdown', async t => {
  const dir = mkdtempSync(join(tmpdir(), 'strata-signals-'));
  const journal = new Journal(dir, 1); const signals = new Signals(journal);
  t.after(() => {signals.close(); journal.close(); rmSync(dir, {recursive:true});});
  assert.equal(await signals.wait(0, 10), false);
  const wait = signals.wait(0, 3000);
  await assert.rejects(signals.wait(0, 10), /RATE_LIMITED/);
  signals.publish('chat', 'player: ordinary chat\n' + '😀'.repeat(300));
  assert.equal(await wait, true);
  const event = signals.read(0).signals[0]!;
  assert.equal(Array.from(event.summary).length, 256);
  assert.equal(event.summary.includes('\n'), false);
  const pending = signals.wait(1, 3000);
  signals.close();
  await assert.rejects(pending, /STOPPED/);
});
