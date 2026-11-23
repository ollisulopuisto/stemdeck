import {test,expect} from '@playwright/test';
import {openStudio} from './helpers.mjs';
test('a delayed desktop store reply cannot overwrite a user edit',async({page})=>{
 await page.addInitScript(()=>{
  window.__workspaceResolve=null;
  window.__TAURI__={core:{invoke:(cmd,args)=>{
   if(cmd==='store_get') {
    if(args.key?.startsWith('stemdeck:workspace:')) return new Promise(resolve=>window.__workspaceResolve=resolve);
    return Promise.resolve(JSON.parse(localStorage.getItem(args.key)||'null'));
   }
   if(cmd==='store_set')localStorage.setItem(args.key,JSON.stringify(args.value));
   if(cmd==='get_setup_status')return Promise.resolve({ready:true});
   return Promise.resolve(null);
  }},event:{listen:()=>Promise.resolve(()=>{})}};
 });
 await openStudio(page);
 await expect.poll(()=>page.evaluate(async()=>Boolean((await import('/js/state.js')).audioEngine))).toBe(true);
 await page.locator('#t-speed-05').click();
 await page.evaluate(()=>window.__workspaceResolve({speed:1,zoom:4,loopEnabled:true,loopStart:1,loopEnd:4,position:3}));
 await page.waitForTimeout(200);
 expect(await page.evaluate(async()=>{const s=await import('/js/state.js');return [s.playbackSpeed,s.waveZoom,s.loopEnabled]})).toEqual([.5,1,false]);
});
