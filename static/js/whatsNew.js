// whatsNew.js — "What's New" panel: shows the changelog entries for the
// versions installed since the user's last acknowledged version, once, on
// the first launch after an upgrade. The full release history is always
// available from the About dialog and never touches the seen-marker.
//
// Marker semantics (shared with the sibling apps' What's New):
//   - upgrade:            entries newer than the seen version, up to current
//   - first run of panel: the current version's entries only, never history
//   - downgrade/reinstall: nothing
//   - the marker is recorded only on the panel's explicit Close and only
//     ever moves forward; Escape / clicking the backdrop hides the panel
//     and it reappears on the next launch
//   - [Unreleased] is never shown

import { storeGet, storeSet } from "./utils.js";

const SEEN_KEY = "stemdeck.whatsNewSeen";

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Numeric per-segment compare; v-prefix ignored, missing segments are 0. */
export function compareVersions(a, b) {
  const pa = String(a || "").replace(/^v/i, "").split(".").map((x) => parseInt(x, 10) || 0);
  const pb = String(b || "").replace(/^v/i, "").split(".").map((x) => parseInt(x, 10) || 0);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const d = (pa[i] || 0) - (pb[i] || 0);
    if (d) return d < 0 ? -1 : 1;
  }
  return 0;
}

/**
 * Parse Keep-a-Changelog markdown into [{ version, date, body }].
 * Only `## [X.Y.Z] - YYYY-MM-DD` sections are entries; [Unreleased] and
 * everything before the first released heading are skipped.
 */
export function parseChangelog(md) {
  const sections = [];
  let current = null;
  for (const line of String(md || "").split("\n")) {
    const m = line.match(/^## \[(v?\d[\w.-]*)\]\s*-\s*(\d{4}-\d{2}-\d{2})/);
    if (m) {
      current = { version: m[1].replace(/^v/i, ""), date: m[2], body: [] };
      sections.push(current);
    } else if (/^## /.test(line)) {
      current = null; // [Unreleased] or any other section: not shown
    } else if (current) {
      current.body.push(line);
    }
  }
  for (const s of sections) {
    while (s.body.length && !s.body[0].trim()) s.body.shift();
    while (s.body.length && !s.body[s.body.length - 1].trim()) s.body.pop();
  }
  return sections.filter((s) => s.body.length);
}

/** The minimal markdown the changelog uses: bullets, paragraphs, **bold**, [links](url). */
function renderBody(lines) {
  const html = [];
  let list = null;
  const inline = (t) =>
    esc(t)
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  for (const raw of lines) {
    const line = raw.trimEnd();
    const bullet = line.match(/^\s*-\s+(.*)/);
    if (bullet) {
      if (!list) { list = []; html.push(list); }
      list.push(bullet[1]);
    } else {
      list = null;
      if (!line.trim()) continue;
      if (line.trim() === "---") continue;
      const h = line.match(/^###\s+(.*)/);
      html.push(h ? `<h4>${inline(h[1])}</h4>` : `<p>${inline(line)}</p>`);
    }
  }
  return html
    .map((x) => (Array.isArray(x) ? `<ul>${x.map((li) => `<li>${inline(li)}</li>`).join("")}</ul>` : x))
    .join("");
}

let sectionsPromise = null;
function loadSections() {
  if (!sectionsPromise) {
    sectionsPromise = fetch("/api/whats-new", { cache: "no-store" })
      .then((r) => (r.ok ? r.text() : ""))
      .then((md) => parseChangelog(md))
      .catch((e) => { console.warn("[whatsNew] changelog fetch failed:", e); return []; });
  }
  return sectionsPromise;
}

function buildDialog() {
  const backdrop = document.createElement("div");
  backdrop.className = "about-backdrop wn-backdrop hidden";
  backdrop.id = "whatsNewDialog";
  backdrop.setAttribute("role", "dialog");
  backdrop.setAttribute("aria-modal", "true");
  backdrop.innerHTML = `
    <div class="about-card wn-card">
      <button class="about-close" id="whatsNewClose" type="button" aria-label="Close">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
      <h2 id="whatsNewTitle"></h2>
      <div class="wn-body" id="whatsNewBody"></div>
      <button class="about-link about-link-accent wn-done" id="whatsNewDone" type="button"></button>
    </div>`;
  document.body.appendChild(backdrop);
  return backdrop;
}

/**
 * Open the panel.
 * @param sections entries to render
 * @param history  true for the About-dialog full-history view: never
 *                 records the seen-marker, whatever the dismissal
 * @param onExplicitClose called only when the user closes via the buttons
 *                        (not Escape/backdrop) and history is false
 */
function openWhatsNew(sections, { history = false, since = null, onExplicitClose = null } = {}) {
  const backdrop = document.getElementById("whatsNewDialog") || buildDialog();
  const title = backdrop.querySelector("#whatsNewTitle");
  const body = backdrop.querySelector("#whatsNewBody");
  const done = backdrop.querySelector("#whatsNewDone");
  const close = backdrop.querySelector("#whatsNewClose");

  title.textContent = history
    ? "Release history"
    : sections.length === 1 && !since
      ? `What's new in ${sections[0].version}`
      : `What's new since ${since || sections[sections.length - 1].version}`;
  done.textContent = history ? "Close" : "Got it";
  body.innerHTML = sections.length
    ? sections
        .map((s) => `<h3><span class="wn-ver">v${esc(s.version)}</span> <span class="wn-date">${esc(s.date)}</span></h3>${renderBody(s.body)}`)
        .join("")
    : `<p class="wn-empty">The changelog is not available in this build.</p>`;
  body.scrollTop = 0;

  const hide = () => backdrop.classList.add("hidden");
  const explicit = () => { hide(); if (!history && onExplicitClose) onExplicitClose(); };
  done.onclick = explicit;
  close.onclick = explicit;
  backdrop.onmousedown = (e) => { if (e.target === backdrop) hide(); };
  backdrop.onkeydown = (e) => { if (e.code === "Escape") hide(); };
  backdrop.classList.remove("hidden");
}

async function openHistory() {
  openWhatsNew(await loadSections(), { history: true });
}

/**
 * Wire the About-dialog entry and show the post-upgrade panel if one is due.
 * Failures are silent: the panel is additive, never a startup blocker.
 */
export async function initWhatsNew(currentVersion) {
  document.getElementById("aboutWhatsNew")?.addEventListener("click", openHistory);

  const sections = await loadSections();
  if (!sections.length) return;

  const seen = await storeGet(SEEN_KEY, null);
  let pending;
  if (seen === null) {
    // First launch with this feature: the running version's notes only,
    // never the whole history at someone who has used StemDeck for months.
    pending = sections.filter((s) => compareVersions(s.version, currentVersion) === 0);
  } else if (compareVersions(currentVersion, seen) > 0) {
    pending = sections.filter(
      (s) => compareVersions(s.version, seen) > 0 && compareVersions(s.version, currentVersion) <= 0,
    );
  } else {
    return; // up to date, downgrade, or reinstall: nothing
  }
  if (!pending.length) return;

  openWhatsNew(pending, {
    since: seen,
    onExplicitClose: () => {
      // Forward-only: never move the marker backwards.
      storeGet(SEEN_KEY, null).then((cur) => {
        if (cur === null || compareVersions(currentVersion, cur) > 0) {
          storeSet(SEEN_KEY, currentVersion);
        }
      });
    },
  });
}
