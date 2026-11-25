// App-wide shortcuts. Local controls and dialogs keep their own key handling.
export const SHORTCUTS = Object.freeze([
  { id: 'play', code: 'Space', scope: 'transport' },
  { id: 'seekBack', code: 'BracketLeft', scope: 'transport' },
  { id: 'seekForward', code: 'BracketRight', scope: 'transport' },
  { id: 'loop', code: 'KeyL', scope: 'transport' },
  { id: 'metronome', code: 'KeyK', scope: 'transport' },
  { id: 'loopIn', code: 'KeyI', scope: 'transport' },
  { id: 'loopOut', code: 'KeyO', scope: 'transport' },
  { id: 'trashTrack', key: 'Delete', scope: 'library' },
  { id: 'trashTrack', key: 'Backspace', scope: 'library' },
]);

export function shortcutTargetOwned(event, doc = globalThis.document) {
  const target = event.composedPath?.()[0] ?? event.target;
  const owned = (el) => Boolean(el?.isContentEditable || el?.closest?.(
    'input, textarea, select, button, a, [role="button"], [role="slider"], [role="textbox"], [contenteditable]:not([contenteditable="false"]), .folder-editor',
  ));
  if (owned(target) || owned(doc?.activeElement)) return true;
  return [...(doc?.querySelectorAll?.('dialog[open], [role="dialog"][aria-modal="true"]') ?? [])]
    .some((el) => el.getClientRects().length > 0);
}

export function matchShortcut(event, scope, doc = globalThis.document) {
  if (event.defaultPrevented || event.isComposing || event.keyCode === 229
      || event.metaKey || event.ctrlKey || event.altKey || event.shiftKey
      || shortcutTargetOwned(event, doc)) return null;
  return SHORTCUTS.find((row) => row.scope === scope
    && (row.code ? row.code === event.code : row.key === event.key))?.id ?? null;
}
