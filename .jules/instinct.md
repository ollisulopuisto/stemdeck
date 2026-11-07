## 2026-11-07 - PR32 conflict repair

Keep main's newer normalized-root/NUL/absolute path guards and preserve the
PR's raw forward/backslash traversal regression tests. Do not replace those
checks with the older Path(raw) version flagged by CodeQL. No suppression or
security baseline changes. Python syntax and focused lint/format pass locally;
full tests need CI dependencies and CodeQL must pass before approved merge.
