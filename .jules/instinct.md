## 2026-11-07 - Notarized release path

Instinct applies the analyst's hardened-runtime/notary patch, then requires
Apple's explicit Accepted JSON status, staples/validates the app before DMG
packing, and staples/validates the final DMG before checksums/upload. Gatekeeper
checks both. Missing credentials fail early. A self-hosted Mac preflight checks
secret presence (names only), shell syntax and no build/upload on PR/manual
preflight; full package remains release-published only. No hosted build minutes
added. No model/runtime layout changes: Intel remains Demucs-only and optional
BS-Roformer-SW remains Apple Silicon. Runtime pack is separate from notarized
app/DMG and not claimed notarized. Native CI/notary acceptance still pending.
Maintainer approved this PR once green and one release after ordered merges.
Rollback: revert this PR. No main push or credentials in source.

## 2026-11-07 - PR27 security conflict repair

Instinct merges current main into PR27 without downgrading main's raw-input
NUL/traversal, absolute-path and normalized-root checks. Preserve PR27's torch
2.10 security floors/lockfile and tests. Earlier CodeQL annotations targeted
the pre-main Path(raw) constructors; retain main's normalization rather than
suppress a finding. Native/full CI and CodeQL remain merge gates. No UI or
model selection changes, no main push. Maintainer approved PR27 then PR32 and
29-31 once green, then notarization PR and one release. Rollback: revert PR27.

## Hosted-runner correction (Instinct, 2026-11-07)

Owner corrected the runner model: GitHub-hosted, not self-hosted. Native Mac
and Windows checks now use standard macos-15 and windows-latest. macOS release
and credential preflight use macos-15 (Apple Silicon), install uv/zstd and Rust
targets, and ensure Rosetta for Intel runtime generation. Signing uses a random
throwaway keychain password, so no extra KEYCHAIN_PASSWORD secret is needed.
GitHub docs confirm standard hosted jobs are free for this public repository:
https://docs.github.com/en/actions/concepts/billing-and-usage
No larger runners, artifact storage or additional services were added.

Manual builds take a validated vMAJOR.MINOR.PATCH input, run only the macOS
pipeline, and upload to a draft release. This avoids the unrelated inherited
Linux/Windows release-event jobs, which remain untouched. Full published
release behavior is preserved for larger releases.
