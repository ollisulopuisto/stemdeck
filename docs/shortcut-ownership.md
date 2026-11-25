# App-wide keyboard shortcuts

`static/js/shortcuts.js` is the registry and shared target/modifier guard for
transport and library actions. Main and catalog handlers dispatch registry IDs.
Space plays, brackets seek, L toggles loop, K toggles metronome, I/O set loop
bounds, and Delete/Backspace trash the open track. Every chord is bare: Control,
Command, Option/Alt and Shift combinations pass to the host. No replacement
chords were added.

Text fields, selects, contenteditable elements, buttons, links, sliders and
visible dialogs keep their keys. Already-handled events and IME composition
also pass through. Shadow-origin targets and the active element are checked.

Local control activation, menu navigation, lyrics sync and beat-grid editor
commands remain local. Their distinct editing rules are not moved into this
app-wide registry. This is not a claim that every keyboard event is centralized.

## Verification

Failing-first test reproduced Option-Space starting playback through the actual
main handler. Regression tests execute the production transport and library
handlers, all registered rows and modifier combinations, focused controls,
active/shadow text targets, visible dialogs, handled events and composition.
All JS scripts passed after adapting the old textarea structural assertion to
the shared guard, and changed modules pass Node syntax checks.

Own adversarial review RAN. Traced main transport dispatch, live clock and
loop state, catalog deletion, focused controls, modal detection and existing
local listeners. No open findings. Real browser/native Mac, audio playback,
Python/backend and packaging were not run for this frontend-only change.

Version is tag-derived; the dynamic Python version and 0.0.0 desktop release
placeholders are intentionally unchanged. The next release must use a fresh
tag. No build, tag, publish or merge was performed.
