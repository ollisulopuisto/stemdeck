import { test, expect } from '@playwright/test';
import { openStudio, JOB_ID, SIBLING_JOB_ID } from './helpers.mjs';
const read = page => page.evaluate(async () => {
  const s = await import('/js/state.js');
  return {start:s.loopStart,end:s.loopEnd,enabled:s.loopEnabled,zoom:s.waveZoom,speed:s.playbackSpeed,
    position:(s.audioEngine??s.multitrack)?.getCurrentTime(),playing:(s.audioEngine??s.multitrack)?.isPlaying()};
});
for (const mode of ['chunked', 'streaming']) {
const saved = {loopEnabled:true,loopStart:1,loopEnd:4,zoom:2,position:2,speed:.65};
test(`${mode}: restores existing controls paused, then saves real edits and isolates another song`, async ({page}, testInfo) => {
  await page.addInitScript(([id,value])=>{if(!localStorage.getItem(`stemdeck:workspace:${id}`))localStorage.setItem(`stemdeck:workspace:${id}`,JSON.stringify(value));},[JOB_ID,saved]);
  if(mode==='streaming') await page.addInitScript(()=>localStorage.setItem('stemdeck.audioEngine','0'));
  await openStudio(page);
  await expect.poll(async()=> (await read(page)).position).toBeCloseTo(2,1);
  expect(await read(page)).toMatchObject({start:1,end:4,enabled:true,zoom:2,speed:.65,playing:false});
  await expect(page.locator('#t-speed-075')).toHaveText('0.65x');
  await page.locator('#t-loop').click();
  await page.locator('#t-speed-1').click();
  await expect.poll(()=>page.evaluate(id=>JSON.parse(localStorage.getItem(`stemdeck:workspace:${id}`)),JOB_ID)).toMatchObject({loopEnabled:false,speed:1});
  await page.reload();
  await page.locator(`.cat-item[data-id="${JOB_ID}"]`).first().dblclick();
  await expect.poll(async()=> (await read(page)).position).toBeCloseTo(2,1);
  expect(await read(page)).toMatchObject({start:1,end:4,enabled:false,zoom:2,speed:1,playing:false});
  await expect(page.locator('#waveLoadingOverlay')).toHaveClass(/hidden/);
  await page.screenshot({path:testInfo.outputPath(`workspace-restored-${mode}.png`),fullPage:true});
  await page.locator(`.cat-item[data-id="${SIBLING_JOB_ID}"]`).first().dblclick();
  await expect.poll(async()=>page.evaluate(async()=> (await import('/js/state.js')).currentJobId)).toBe(SIBLING_JOB_ID);
  await expect.poll(async()=> (await read(page)).zoom).toBe(1);
  expect((await read(page)).enabled).toBe(false);
  expect((await read(page)).speed).toBe(1);
});

}
