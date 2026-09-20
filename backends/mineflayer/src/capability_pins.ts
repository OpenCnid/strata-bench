import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';

export const hashFile = (path: URL): string => createHash('sha256').update(readFileSync(path)).digest('hex');
/** Pin every compiled broker module, including transitive imports and this pinning policy. */
export function implementationPins(): Record<string,string> {
  return Object.fromEntries(readdirSync(new URL('./',import.meta.url),{withFileTypes:true})
    .filter(entry => entry.isFile() && entry.name.endsWith('.js'))
    .map(entry => entry.name).sort().map(name => [name,hashFile(new URL(`./${name}`,import.meta.url))]));
}
