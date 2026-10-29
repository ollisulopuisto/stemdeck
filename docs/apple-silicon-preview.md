# Apple Silicon preview build

This is an opt-in local preview, not a release and not a universal-best claim.
The selected candidates are BS-Roformer-SW for six stems and aufr33/viperx for
lead/backing, based on the directional benchmark evidence in models.md. They
remain unproven on real audio/native MPS here. Weights are not redistributed.

Manual workflow `Apple Silicon preview (no release)` uses public standard
`macos-15` (ARM64), with an architecture assertion and a 120 minute limit.
No release, container, Windows/Intel build, self-hosted host or persistent cache
is touched. It defaults to **no upload**. Upload requires checking included
storage first: at most 2 GiB for one day, actual size reported in the job.
Public standard compute is free; artifact storage can consume the account's
shared allowance and accrue charges beyond it. No paid allowance is assumed.

A successful upload is a tar.gz in an Actions artifact, requiring GitHub sign-in
and read access. Expiry is one day, not a durable release URL. Extract the zip,
then tar.gz. Keep the preview folder together. `Install-and-launch.command`
checks hashes, explains downloads, asks for RUN, mounts the DMG readonly and
stages its paired runtime archive for the existing setup's second hash check.
The manifest is local-only: it never invents an anonymous runtime download URL.
The shell launcher is required to select the stronger engines. Launching the
app directly without it keeps the normal defaults. No silent fallback from SW
is intended if its model fails.

Preview data/models/jobs/settings use a separate StemDeck-preview directory.
Setup may download support models; SW (~700 MB) and karaoke weights arrive on
first requested use, not in the installer. Karaoke size is unverified. No paid
model, gated-download workaround, user-machine model installation or copyright
permission is implied by this build. Gatekeeper/notarization and real listening
acceptance stay open until tested. Do not disable macOS security checks blindly.

Before delivery verify the terminal Mac build, runtime import/tests, mounted
DMG contents, SHA256 and actual downloads. Then use /api/health to identify the
selected engine, run a short user-owned clip, check all six nonempty output
stems and a lead/backing split, and record device, time, peak memory and listening
result. Import tests alone are not inference or quality proof.

Workflow activation is blocked by the existing credential's workflow-write
scope. Source changes can be reviewed/merged normally; the separate workflow
file must be added through the owner's authorized GitHub route. Do not widen
tokens or publish a release to bypass this gate. The workflow must be on the
selected branch before its one manual run can exist.
