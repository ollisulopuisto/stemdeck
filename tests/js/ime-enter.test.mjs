// Enter during IME composition (CJK input) is the composition's confirm key,
// not a commit. modern-web-guidance legacy-scan (ime-safe-enter-submit)
// flagged the keydown listeners on the settings secret field (catalog.js),
// the section rename field (sections.js) and the loop start/end fields
// (transport.js) for acting on Enter without checking event.isComposing /
// event.keyCode === 229. All three wrap their handler in guardIme from
// static/js/imeEnter.js, so this drives that wrapper with composing and
// plain keydown events the way those listeners use it.
//
// Run:  node tests/js/ime-enter.test.mjs

import { guardIme } from "../../static/js/imeEnter.js";

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

// Minimal element stand-in: the same addEventListener/dispatch shape the
// real fields use.
function fakeField() {
  const listeners = [];
  return {
    addEventListener: (type, fn) => {
      if (type === "keydown") listeners.push(fn);
    },
    keydown: (e) => listeners.forEach((fn) => fn(e)),
  };
}

const field = fakeField();
const seen = [];
field.addEventListener("keydown", guardIme((e) => seen.push(e)));

field.keydown({ key: "Enter", isComposing: true });
check("composing Enter never reaches the handler", seen.length === 0, JSON.stringify(seen));

field.keydown({ key: "Enter", keyCode: 229 });
check("keyCode 229 Enter never reaches the handler", seen.length === 0, JSON.stringify(seen));

const plain = { key: "Enter" };
field.keydown(plain);
check("plain Enter reaches the handler", seen.length === 1, JSON.stringify(seen));
check("the handler gets the original event", seen[0] === plain);

field.keydown({ key: "Escape" });
check("non-Enter keys pass the guard", seen.length === 2, JSON.stringify(seen));

if (fail) {
  console.error(`ime-enter: ${fail} failed, ${pass} passed`);
  process.exit(1);
}
console.log(`ime-enter: ${pass} passed`);
