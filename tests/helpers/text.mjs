// Reports preserve text with HTML entities, rather than deleting punctuation.
export function escapeHtml(value) {
  const entities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(value ?? "").replace(/[&<>"']/g, (character) => entities[character]);
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
