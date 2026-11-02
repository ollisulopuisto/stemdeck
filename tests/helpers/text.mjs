// Reports preserve text with HTML entities, rather than deleting punctuation.
export function escapeHtml(value) {
  const entities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(value ?? "").replace(/[&<>"']/g, (character) => entities[character]);
}

// Make a string safe to place inside one cell of a Markdown table. The pipe
// and newline characters terminate a cell and a row, so user-controlled text
// must never be allowed to carry them through unchanged; neutralise them first,
// then HTML-escape, so nothing can break out of its cell.
export function tableCell(text) {
  let s = String(text ?? "");
  s = s.replace(/\|/g, "\\|").replace(/\r?\n|\r/g, " ");
  return escapeHtml(s);
}

// Lyrics assertions compare plain text. Repeat until nested markup is gone:
// a single replacement can expose a tag that was hidden inside another tag.
export function lyricText(value) {
  let text = String(value ?? "");
  let previous;
  do {
    previous = text;
    text = text.replace(/<[^<>]*>/g, "");
  } while (text !== previous);
  return text.replace(/[&<>"']/g, "");
}
