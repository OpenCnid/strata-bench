/** Operator-only metadata decoder for Forge 1.19.2-43.4.23 / FML3.
 * Source: the exact Forge sources JAR, SHA-256
 * 663e58cdde75ce06f4713cfcedea4414c39d17adcfddcfa81c6da5adcd59102f.
 * This does not implement registries, mod channels, or grant a Forge capability.
 */
import { requireThat, Fault } from './errors.js';

class Reader {
  private offset = 0;
  constructor(private readonly bytes: Buffer) {
    requireThat(bytes.length <= 1024 * 1024, 'FORGE_PAYLOAD_LIMIT');
  }
  byte(): number {
    requireThat(this.offset < this.bytes.length, 'FORGE_PAYLOAD_INVALID');
    return this.bytes[this.offset++]!;
  }
  count(maximum: number): number {
    let value = 0;
    for (let index = 0; index < 5; index++) {
      const byte = this.byte();
      requireThat(index < 4 || byte <= 7, 'FORGE_PAYLOAD_INVALID');
      value += (byte & 127) * 2 ** (7 * index);
      if (!(byte & 128)) {
        requireThat(index === 0 || byte !== 0, 'FORGE_PAYLOAD_INVALID');
        requireThat(value <= maximum, 'FORGE_PAYLOAD_LIMIT');
        return value;
      }
    }
    throw new Fault('FORGE_PAYLOAD_INVALID');
  }
  take(length: number): Buffer {
    requireThat(this.offset + length <= this.bytes.length, 'FORGE_PAYLOAD_INVALID');
    const result = this.bytes.subarray(this.offset, this.offset + length);
    this.offset += length;
    return result;
  }
  text(maximum = 256): string {
    const bytes = this.take(this.count(maximum * 3));
    let value: string;
    try {value = new TextDecoder('utf-8', {fatal:true,ignoreBOM:true}).decode(bytes);}
    catch {throw new Fault('FORGE_PAYLOAD_INVALID');}
    requireThat(value.length <= maximum && !/[\x00-\x1f\x7f]/.test(value), 'FORGE_PAYLOAD_INVALID');
    return value;
  }
  resource(): string {
    const value = this.text(32767);
    requireThat(/^[a-z0-9_.-]+:[a-z0-9/._-]+$/.test(value), 'FORGE_PAYLOAD_INVALID');
    return value;
  }
  mod(): string {
    const value = this.text();
    requireThat(/^[a-z][a-z0-9_]{1,63}$/.test(value), 'FORGE_PAYLOAD_INVALID');
    return value;
  }
  done(): void { requireThat(this.offset === this.bytes.length, 'FORGE_PAYLOAD_INVALID'); }
  list<T>(read: () => T, key: (value:T) => string): T[] {
    const count = this.count(4096);
    const result: T[] = []; const keys = new Set<string>();
    for (let i=0; i<count; i++) {
      const value = read(); const id = key(value);
      requireThat(!keys.has(id), 'FORGE_PAYLOAD_INVALID');
      keys.add(id); result.push(value);
    }
    return result;
  }
}

export type ForgeOffer = {kind:'mod_data'; mods:{id:string; name:string; version:string}[]} |
  {kind:'mod_list'; mods:string[]; channels:{id:string;version:string}[];
    registries:string[]; datapack_registries:string[]};

export function unwrapForgeLogin(channel: string, data: Buffer): {channel:string;data:Buffer} {
  requireThat(channel === 'fml:loginwrapper', 'FORGE_CHANNEL_UNSUPPORTED');
  requireThat(Buffer.isBuffer(data), 'FORGE_PAYLOAD_INVALID');
  const outer = new Reader(data);
  const target = outer.resource();
  const payload = outer.take(outer.count(1024 * 1024));
  outer.done();
  return {channel:target,data:payload};
}

export function decodeForgeOffer(channel: string, data: Buffer): ForgeOffer {
  const payload = unwrapForgeLogin(channel,data);
  requireThat(payload.channel === 'fml:handshake', 'FORGE_CHANNEL_UNSUPPORTED');
  const reader = new Reader(payload.data);
  const discriminator = reader.byte();
  let result: ForgeOffer;
  if (discriminator === 5) {
    result = {kind:'mod_data',mods:reader.list(() => ({id:reader.mod(),name:reader.text(),
      version:reader.text()}), value => value.id)};
  } else if (discriminator === 1) {
    result = {kind:'mod_list',mods:reader.list(() => reader.mod(), value => value),
      channels:reader.list(() => ({id:reader.resource(),version:reader.text()}), value => value.id),
      registries:reader.list(() => reader.resource(), value => value),
      datapack_registries:reader.list(() => reader.resource(), value => value)};
  } else throw new Fault('FORGE_MESSAGE_UNSUPPORTED');
  reader.done();
  return result;
}
