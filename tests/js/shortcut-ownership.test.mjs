import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { SHORTCUTS, matchShortcut } from '../../static/js/shortcuts.js';
const main = readFileSync(new URL('../../static/js/main.js', import.meta.url), 'utf8');
const block = main.split('// ─── Keyboard shortcuts ───')[1].split('// ─── Drag audio')[0];
let handler;
let plays = 0;
const doc = { addEventListener: (_, fn) => { handler = fn; }, activeElement: null, querySelectorAll: () => [] };
class Input {}
vm.runInNewContext(block, {
  document: doc, HTMLInputElement: Input, HTMLTextAreaElement: class {},
  transport: () => ({ getCurrentTime: () => 10 }), togglePlayPause: () => plays++,
  matchShortcut, loopEnabled: false, loopBtn: {click(){}}, toggleMetronome(){},
});
const plain = {code:'Space', key:' ', target: {}, preventDefault(){this.defaultPrevented=true;}};
handler({...plain, altKey:true});
assert.equal(plays, 0, 'Option-Space must not start playback');
handler({...plain});
assert.equal(plays, 1, 'bare Space still plays');
for (const row of SHORTCUTS) {
  const e = {...plain, code:row.code, key:row.key};
  assert.equal(matchShortcut(e,row.scope,doc),row.id);
  for(const mod of ['metaKey','ctrlKey','altKey','shiftKey']) assert.equal(matchShortcut({...e,[mod]:true},row.scope,doc),null);
  for(const target of [{isContentEditable:true},{closest:()=>({})}]) assert.equal(matchShortcut({...e,target},row.scope,doc),null);
  assert.equal(matchShortcut({...e,defaultPrevented:true},row.scope,doc),null);
  assert.equal(matchShortcut({...e,isComposing:true},row.scope,doc),null);
  assert.equal(matchShortcut(e,row.scope,{...doc,querySelectorAll:()=>[{getClientRects:()=>[{}]}]}),null);
}
const catalog = readFileSync(new URL('../../static/js/catalog.js', import.meta.url), 'utf8');
const deleteBlock = catalog.slice(catalog.indexOf('function wireLibraryDeleteKeys()'), catalog.indexOf('// ─── Rendering helpers'));
let trashes = 0;
doc.body = {dataset:{}};
vm.runInNewContext(deleteBlock + '\nwireLibraryDeleteKeys();', {
  document:doc, matchShortcut, _currentTrackId:'a', tracks:{a:{}}, moveTrackToTrash:()=>trashes++,
});
handler({...plain,code:'Backspace',key:'Backspace',metaKey:true});
assert.equal(trashes,0,'modified delete belongs to host');
handler({...plain,code:'Backspace',key:'Backspace'});
assert.equal(trashes,1,'plain delete still trashes open track');
assert.equal(matchShortcut(plain,'transport',{...doc,activeElement:{isContentEditable:true}}),null);
assert.equal(matchShortcut({...plain,composedPath:()=>[{isContentEditable:true}]},'transport',doc),null);
console.log('shortcut ownership and actual transport/library handlers: pass');
