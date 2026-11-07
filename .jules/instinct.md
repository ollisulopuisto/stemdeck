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
