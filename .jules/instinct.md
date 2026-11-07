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
