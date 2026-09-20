import test from 'node:test';
import assert from 'node:assert/strict';
import { decodeForgeOffer, unwrapForgeLogin } from '../src/forge_handshake.js';

const vint=(n:number):Buffer=>{const b=[];do{let v=n&127;n>>>=7;if(n)v|=128;b.push(v);}while(n);return Buffer.from(b);};
const text=(s:string)=>{const b=Buffer.from(s);return Buffer.concat([vint(b.length),b]);};
const wrapper=(b:Buffer)=>Buffer.concat([text('fml:handshake'),vint(b.length),b]);
const data=wrapper(Buffer.concat([Buffer.from([5,1]),text('example'),text('Example mod'),text('1.0')]));
const list=wrapper(Buffer.concat([Buffer.from([1,1]),text('example'),Buffer.from([1]),text('example:main'),
  text('1'),Buffer.from([1]),text('minecraft:block'),Buffer.from([1]),text('example:registry')]));

test('exact FML3 mod metadata and registry offers decode without advertising support', () => {
  assert.deepEqual(decodeForgeOffer('fml:loginwrapper',data), {kind:'mod_data',
    mods:[{id:'example',name:'Example mod',version:'1.0'}]});
  assert.deepEqual(decodeForgeOffer('fml:loginwrapper',list), {kind:'mod_list',mods:['example'],
    channels:[{id:'example:main',version:'1'}],registries:['minecraft:block'],datapack_registries:['example:registry']});
});

test('truncation, trailing bytes, channel confusion and unsupported messages fail closed', () => {
  for (let i=0;i<data.length;i++) assert.throws(()=>decodeForgeOffer('fml:loginwrapper',data.subarray(0,i)),/FORGE_/);
  assert.throws(()=>decodeForgeOffer('other:channel',data),/FORGE_CHANNEL_UNSUPPORTED/);
  assert.throws(()=>decodeForgeOffer('fml:loginwrapper',Buffer.concat([data,Buffer.from([0])])),/FORGE_PAYLOAD_INVALID/);
  assert.throws(()=>decodeForgeOffer('fml:loginwrapper',wrapper(Buffer.from([3,0]))),/FORGE_MESSAGE_UNSUPPORTED/);
  // FML2's list lacks the required FML3 datapack registry count.
  assert.throws(()=>decodeForgeOffer('fml:loginwrapper',wrapper(Buffer.from([1,0,0,0]))),/FORGE_PAYLOAD_INVALID/);
});

test('invalid UTF-8, duplicate identities, oversized counts and noncanonical varints reject', () => {
  const cases=[Buffer.from([5,0x80,0]),Buffer.from([5,0xff,0xff,0xff,0xff,0x0f]),
    Buffer.concat([Buffer.from([5]),vint(4097)]),Buffer.from([5,1,1,0xff]),
    Buffer.concat([Buffer.from([5,2]),text('example'),text('A'),text('1'),text('example'),text('B'),text('2')])];
  for (const bytes of cases) assert.throws(()=>decodeForgeOffer('fml:loginwrapper',wrapper(bytes)),/FORGE_/);
  assert.throws(()=>decodeForgeOffer('fml:loginwrapper',Buffer.alloc(1024*1024+1)),/FORGE_PAYLOAD_LIMIT/);
});

test('unknown wrapped channels can be inventoried without claiming handshake support', () => {
  const payload=Buffer.from([98,4,255]);
  const packet=Buffer.concat([text('example:login'),vint(payload.length),payload]);
  assert.deepEqual(unwrapForgeLogin('fml:loginwrapper',packet), {channel:'example:login',data:payload});
  assert.throws(()=>decodeForgeOffer('fml:loginwrapper',packet), /FORGE_CHANNEL_UNSUPPORTED/);
});
