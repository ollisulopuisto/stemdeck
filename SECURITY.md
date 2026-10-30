# Security Policy

## Supported Versions

StemDeck is in active alpha. Only the latest release receives security fixes -
there are no long-term-support branches yet. Please update to the newest
release before reporting an issue.

| Version         | Supported |
| --------------- | --------- |
| Latest release  | Yes       |
| Any older build | No        |

## Reporting a Vulnerability

Please report security issues privately, not in a public issue. Open the
repository's **Security** tab and click **Report a vulnerability** (GitHub
Private Vulnerability Reporting). This keeps the details private until a fix is
available.

Include where you can:

- Affected version and operating system
- Steps to reproduce
- Impact (what an attacker could do)
- Any relevant logs or proof of concept

What to expect:

- Acknowledgement within about 5 business days (best-effort; small team).
- We confirm the report, assess severity, and keep you updated.
- Fixes ship in the next release. We credit reporters unless you prefer not to
  be named.

## Scope and threat model

StemDeck is local-first and single-user by design: it runs on your own machine,
has no authentication, and is same-origin only. Reports that it "has no login"
or "no per-user access control" describe intended behavior, not vulnerabilities.

We are most interested in reports about:

- Malicious media files or URLs (SSRF, command or argument injection)
- Cross-site scripting (XSS) or Content-Security-Policy bypass in the desktop
  webview
- Path traversal in the backend file APIs
- Integrity of downloaded binaries (FFmpeg, the runtime pack)

## Good-faith research

We will not pursue action against good-faith security research that respects
user privacy and avoids data destruction or service disruption. Thank you for
helping keep StemDeck users safe.

## Follow-up on the October 29 CodeQL locations

The cookie-path guard previously resolved a path before checking whether it
was a symlink. That erased the evidence the guard needed. Validation now
checks the original expanded path before resolution, with a regression test.
This is not a general filesystem sandbox: explicitly selected local cookie
files remain supported, and concurrent filesystem replacement is not solved.

The library-location guard already rejects direct symlinks, parent traversal,
relative paths, a destination inside the current library, and unrelated
nonempty folders. Regression coverage checks refusal without filesystem
creation. Arbitrary absolute local destinations are an intentional feature;
restricting them to an invented application root would break that feature.
The reported line alone does not establish an unauthorized path operation.

The `--emit-lan-cert` command prints certificate and key **paths** requested by
the caller, not certificate or private-key contents. No secret logging was
reproduced at the reported `println!` site; it is not rewritten or suppressed.

Test fixture routing now requires an HTTPS Wikipedia subdomain with no
credentials or nonstandard port, not a domain-name substring. User-agent
assertions compare the configured value rather than looking for `github.com`.
Acceptance reports encode HTML punctuation instead of deleting it, and lyric
normalization removes nested markup to a fixed point. Existing assertions and
fixtures remain in place. These test changes do not imply a production SSRF
or XSS was present at every reported test location.

The current alert data-flow traces/status could not be read with available
API access. No alerts were dismissed and no scanner configuration was changed.
