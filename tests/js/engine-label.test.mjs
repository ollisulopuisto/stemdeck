// Engine badge and Settings row state.
//
// Run:  node tests/js/engine-label.test.mjs

import { engineBadgeLabel, engineRowState, engineDownloadPercent } from '../../static/js/engineLabel.js';
import { TRANSLATIONS } from '../../static/js/i18n.js';

let passed = 0;
let failed = 0;
function check(name, condition, detail = '') {
  if (condition) { passed++; console.log(`PASS  ${name}`); }
  else { failed++; console.log(`FAIL  ${name}${detail ? `  -- ${detail}` : ''}`); }
}

const t = (k) => TRANSLATIONS.en[k] ?? `!${k}`;

check('default Demucs track has no badge', engineBadgeLabel({ separationEngine: 'demucs' }, t) === '');
check('track from before the setting has no badge', engineBadgeLabel({}, t) === '');
check('roformer track shows its name', engineBadgeLabel({ separationEngine: 'roformer-sw' }, t) === 'BS-Roformer-SW');
check(
  'a fallback says Demucs (fallback)',
  engineBadgeLabel({ separationEngine: 'demucs', engineFallback: 'download failed' }, t) === 'Demucs (fallback)',
);

const st = (over = {}) => ({ roformer_available: true, roformer_unavailable_reason: null, ...over });
check('intel mac', engineRowState({ separation_engine: 'demucs', separation_engine_status: st({ roformer_unavailable_reason: 'intel-mac' }) }) === 'intel');
check('not installed', engineRowState({ separation_engine: 'demucs', separation_engine_status: st({ roformer_unavailable_reason: 'not-installed' }) }) === 'unavailable');
check('default', engineRowState({ separation_engine: 'demucs', separation_engine_status: st() }) === 'default');
check('downloading', engineRowState({ separation_engine: 'roformer-sw', separation_engine_status: st({ downloading: true }) }) === 'downloading');
check('in use', engineRowState({ separation_engine: 'roformer-sw', separation_engine_status: st({ model_ready: true }) }) === 'in-use');
check('failed fallback', engineRowState({ separation_engine: 'roformer-sw', separation_engine_status: st({ last_failure: 'x' }) }) === 'failed');
check('missing status is the default', engineRowState({}) === 'default');

check('percent from bytes', engineDownloadPercent({ model_bytes: 350, model_total_bytes: 700 }) === 50);
check('percent never reaches 100 before ready', engineDownloadPercent({ model_bytes: 900, model_total_bytes: 700 }) === 99);
check('percent with nothing yet is 0', engineDownloadPercent({ model_bytes: 0, model_total_bytes: 700 }) === 0);

for (const key of ['engine.title', 'engine.confirm.title', 'engine.confirm.go', 'engine.state.intel']) {
  check(`en has ${key}`, typeof TRANSLATIONS.en[key] === 'string');
}

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
