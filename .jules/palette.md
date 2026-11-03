## 2026-11-03 - SVG-only mobile controls need names
**Learning:** Visible transport icons and a nearby Speed label did not name the phone controls in the browser accessibility tree. The empty-track screen still exposes these controls, including disabled transport buttons.
**Action:** Name icon-only controls and the speed slider explicitly; keep a browser role/name regression for the empty mobile mixer.
