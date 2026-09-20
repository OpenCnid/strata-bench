import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

test('pinned auth consumers retain CommonJS UUID v4 and reject truncated supplied buffers', () => {
  // Resolve from each real consumer, not merely the top-level package: nested vulnerable
  // copies must not silently survive a lock update. No account or network is used.
  for (const consumer of ['@azure/msal-node', 'yggdrasil']) {
    const fromConsumer = createRequire(require.resolve(consumer));
    const uuid = fromConsumer('uuid');
    assert.equal(fromConsumer('uuid/package.json').version, '11.1.1');
    assert.equal(uuid.validate(uuid.v4()), true);
    assert.equal(uuid.version(uuid.v4()), 4);
    const buffer = new Uint8Array(8).fill(0xaa);
    for (const fn of [
      () => uuid.v3('strata-fixture', uuid.v3.DNS, buffer, 0),
      () => uuid.v5('strata-fixture', uuid.v5.DNS, buffer, 0),
      () => uuid.v6({}, buffer, 0),
    ]) {
      assert.throws(fn, RangeError);
      assert.deepEqual(buffer, new Uint8Array(8).fill(0xaa));
    }
    assert.doesNotThrow(() => fromConsumer(consumer));
  }
});
