// Per-song rehearsal state. Uses the existing desktop/browser store supplied
// by the caller. Never stores playback's playing flag: reopening stays paused.
const finite = (value, fallback) => typeof value === 'number' && Number.isFinite(value) ? value : fallback;
export function normalizeWorkspace(value, duration) {
  const v = value && typeof value === 'object' ? value : {};
  const end = Math.max(0, finite(duration, 0));
  const time = n => Math.min(end, Math.max(0, finite(n, 0)));
  const loopStart = time(v.loopStart), loopEnd = time(v.loopEnd);
  const rate = finite(v.speed, 1);
  return { loopEnabled: v.loopEnabled === true && loopEnd - loopStart >= .2,
    loopStart, loopEnd, zoom: Math.min(10, Math.max(1, finite(v.zoom, 1))),
    position: time(v.position), speed: rate >= .5 && rate <= 1 ? rate : 1 };
}

export function createWorkspaceSession({read, write}) {
  let active = null, queue = Promise.resolve();
  return {
    open(id, duration) {
      const key = `stemdeck:workspace:${id}`;
      const state = { touched: false, ready: false, restored: false, last: null };
      active = state;
      const loaded = Promise.resolve(read(key)).catch(() => null);
      return {
        touch() { state.touched = true; },
        async restore(apply) {
          const value = await loaded;
          if (active !== state || state.restored) return;
          state.restored = true;
          if (value && !state.touched) apply(normalizeWorkspace(value, duration));
          state.ready = true;
        },
        save(value) {
          if (active !== state || !state.ready) return;
          const snapshot = normalizeWorkspace(value, duration);
          const serial = JSON.stringify(snapshot);
          if (serial === state.last) return;
          state.last = serial;
          // Serialize writes so a slow desktop command cannot overwrite a
          // newer checkpoint with an older one. Failure leaves later saves live.
          queue = queue.catch(() => {}).then(() => write(key, snapshot));
        },
      };
    },
    close() { active = null; },
    flush() { return queue; },
  };
}
