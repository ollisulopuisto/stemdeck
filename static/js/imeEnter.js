// Enter during IME composition (CJK input) confirms the candidate in the
// composing text, it does not commit the field. The IME also eats Escape to
// cancel the composition. Every keydown listener that acts on Enter or
// Escape wraps its handler in this guard so composing keystrokes never
// reach it.
export function guardIme(handler) {
  return (e) => {
    if (e.isComposing || e.keyCode === 229) return;
    handler(e);
  };
}
