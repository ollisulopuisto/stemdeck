## 2026-11-07 - PR32 conflict repair

Keep main's newer normalized-root/NUL/absolute path guards and preserve the
PR's raw forward/backslash traversal regression tests. Do not replace those
checks with the older Path(raw) version flagged by CodeQL. No suppression or
security baseline changes. Python syntax and focused lint/format pass locally;
full tests need CI dependencies and CodeQL must pass before approved merge.

## 2026-11-07 - PR27 security conflict repair

Instinct merges current main into PR27 without downgrading main's raw-input
NUL/traversal, absolute-path and normalized-root checks. Preserve PR27's torch
2.10 security floors/lockfile and tests. Earlier CodeQL annotations targeted
the pre-main Path(raw) constructors; retain main's normalization rather than
suppress a finding. Native/full CI and CodeQL remain merge gates. No UI or
model selection changes, no main push. Maintainer approved PR27 then PR32 and
29-31 once green, then notarization PR and one release. Rollback: revert PR27.
