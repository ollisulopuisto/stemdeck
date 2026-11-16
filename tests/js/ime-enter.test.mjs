// Enter during IME composition (CJK input) is the composition's confirm key,
// not a submit. modern-web-guidance legacy-scan (ime-safe-enter-submit)
// flagged these keydown listeners for acting on Enter without checking
// event.isComposing / event.keyCode === 229. Each must return early at the
// top of the handler.
//
// Run:  node tests/js/ime-enter.test.mjs

import { readFileSync } from "node:fs";

let pass = 0,
  fail = 0;
const check = (name, cond, detail = "") => {
  if (cond) {
    pass++;
  } else {
    fail++;
    console.error(`FAIL ${name}`, detail);
  }
};

const GUARDED = {
  "static/js/catalog.js": [4230],
  "static/js/sections.js": [580],
  "static/js/transport.js": [420],
};

for (const [file, lines] of Object.entries(GUARDED)) {
  const source = readFileSync(new URL(`../../${file}`, import.meta.url), "utf8").split("\n");
  for (const line of lines) {
    check(
      `${file}:${line} is the flagged keydown listener (re-anchor if it moved)`,
      /addEventListener\("keydown"/.test(source[line - 1]),
      source[line - 1],
    );
    const head = source.slice(line, line + 3).join("\n");
    check(`${file}:${line} returns early during IME composition`, /isComposing/.test(head), head);
  }
}

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
