# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Released entries up to v0.20.0 are condensed from the upstream
[stemdeckapp/stemdeck](https://github.com/stemdeckapp/stemdeck) release
notes; the full notes live on the upstream releases page. Entries under
"Unreleased" are changes made in this fork on top of v0.20.0.

## [Unreleased]

### Added

- What's New panel: after an upgrade the studio shows what changed, and the
  full release history is always available from the About dialog (this fork).
- Optional BS-Roformer-SW six-stem separation engine (vocals, drums, bass,
  guitar, piano, other).
- On-demand lead/backing vocal split can use the aufr33/viperx karaoke
  checkpoint as an opt-in model (STEMDECK_KARAOKE_MODEL; its licence is
  unresolved and stated in the docs).
- MP4 export on macOS prefers Apple's hardware AudioToolbox AAC encoder.
- The Demucs model now preloads while the source is still downloading.

### Fixed

- MPS separations on Apple Silicon stay on the GPU when one operation is
  unsupported, instead of falling the whole run back to CPU.
- Security hardening: job-ID sanitisation, origin validation on client
  fetches, cookie symlink validation, SSRF findings closed, and dependency
  floors raised (Pillow, certifi, idna, msgpack, rustls, setuptools, torch,
  urllib3, zip).

### Changed

- README rewritten: download table, feature list, and no claims it cannot
  back.

## [0.20.0] - 2026-10-04

- New Guide button turns the studio into its own manual: point at any
  control and a plain-words box explains what it does.
- Trash shows a count on its icon and is easier to use; deleting a song
  while it extracts now actually stops the extraction.

## [0.19.1] - 2026-10-02

- Slowed-down practice sounds right: stutter, doubled kicks and echo at
  0.75x are fixed via Signalsmith Stretch, and the slow speed is freely
  adjustable.
- NVIDIA setup is sturdier on older cards; favourites sync to mobile; the
  top bar works at any window width.

## [0.19.0] - 2026-09-29

- Every track knows what song it is: imports are identified via tags or
  title against MusicBrainz, and the now-playing card shows song and artist
  info, including the musical or film a song comes from.
- Lyrics tab follows the singer line by line while you practise.
- Optional Discogs token and AcoustID fingerprinting in a new Song details
  settings tab for bands Wikipedia does not cover.

## [0.18.1] - 2026-09-25

- Fixed the search box failing with "Search failed. Check your connection."
  on every platform: the trimmed yt-dlp build was missing the three
  extractors that handle searches.

## [0.18.0] - 2026-09-23

- Rebuilt top bar: two grid rows that stay the same height from 2560px down
  to 900px in every language, with stems folding behind a button as the
  window narrows.
- A vocals control that says what it does, and a count-in that plays every
  time.

## [0.17.3] - 2026-09-21

- Apple Silicon Macs falling back to the FFmpeg mirror no longer receive an
  Intel build they cannot run; setup runs the binaries and offers Rosetta or
  a custom URL on mismatch.

## [0.17.2] - 2026-09-13

- Transport footer measures itself and collapses properly, so the click
  track controls no longer stack into a tall column on 15-inch laptops or
  scaled 4K displays.

## [0.17.1] - 2026-09-13

- Count-in length is a choice: off, or 1 to 4 bars.
- The click follows odd and compound meters (7/8 as 3+2+2, 6/8 in two) with
  editable groupings.
- Exports keep your transposition instead of reverting to the original key.

## [0.17.0] - 2026-09-04

- Drag a stem or a loop straight into your DAW: lane handles export that
  stem's slice, the top-edge handle carries the mix with your fader balance,
  click and count-in. Files land in an exports folder you can move.
- StemDeck can be used from a device that is not the one it runs on.

## [0.16.1] - 2026-09-01

- macOS song sections work again: 0.16.0's package carried AppleDouble
  sidecars that broke the runtime. macOS users need the full download, not
  the in-place updater.
- Library fixes: deleted songs stay deleted, trashed songs stay in Trash,
  settings survive.

## [0.16.0] - 2026-08-30

- Automatic song structure: the sections bar fills itself in with intro,
  verse, chorus, bridge, solo, outro (off by default, per import).
- Transpose one instrument without the others; zoomable waveforms;
  fold-away panels; Korean language.

## [0.15.2] - 2026-08-26

- Windows portable starts again: the backend identity check no longer
  mistakes StemDeck's own launcher for an intruder process.

## [0.15.1] - 2026-08-25

- macOS builds restored (0.15.0 shipped without them due to a packaging
  script matching the wrong architecture name). Everything else as 0.15.0.

## [0.15.0] - 2026-08-25

- Search without leaving StemDeck: the link box takes queries, with results
  in YouTube songs, YouTube playlists and SoundCloud tabs.
- Preview button on every result: audition before committing to a
  separation.
- YouTube extraction moved off the deprecated signature-solver path.

## [0.14.2] - 2026-08-24

- You only hear about a release once it is built, installed and verified on
  real machines; no more announcements for downloads that do not exist yet.

## [0.14.1] - 2026-08-24

- Installing a new version no longer resets your settings: StemDeck keeps a
  seed copy outside the install folder and a fresh extract picks your
  choices back up.

## [0.14.0] - 2026-08-23

- Click-to-update on Windows and Linux: the updater fetches only the app
  layer (5 MB instead of 284 MB), leaving data, settings and the Python
  runtime untouched.
- Leaner packages; French language added.

## [0.13.0] - 2026-08-22

- Seven languages: English, Polski, Japanese, Simplified Chinese, Deutsch,
  Portugues, Bahasa Indonesia, with per-language plural forms.
- Setup prefers a working system FFmpeg on macOS and Windows instead of
  forcing a download.

## [0.12.2] - 2026-08-21

- The default jobs folder is no longer recreated after you relocate your
  library; new portable Windows installs default their library inside the
  package.
- Footer waveform and summary card polish.

## [0.12.1] - 2026-08-21

- Fixed the lead/backing vocal split failing on shipped builds with "No
  module named 'audioread'"; packaging now verifies the split's imports.

## [0.12.0] - 2026-08-21

- On-demand lead/backing vocal split: the Vocals stem can be split into
  Lead Vocals and Backing Vocals lanes via UVR-MDX-NET Karaoke 2.
- Stems relocation fixes and faster first-run setup on desktop.

## [0.11.3] - 2026-08-21

- The Windows portable zip is more portable; failure notifications clean up
  after themselves.

## [0.11.2] - 2026-08-20

- YouTube imports failing with HTTP 403 work again: bundled yt-dlp updated
  for YouTube's server-side changes.

## [0.11.1] - 2026-08-17

- macOS FFmpeg setup has a real second source, fails fast instead of
  hanging, retries flaky connections, and reports readable errors.

## [0.11.0] - 2026-08-17

- The library warns when a track's files went missing, with one-click
  restore for URL imports.
- Reporting a failure opens the report; more YouTube link shapes work.

## [0.10.0] - 2026-08-16

- Count-in before playback, independent of the click track, and available
  on exports.
- Transport bar rebuilt so every click-track control is visible.

## [0.9.0] - 2026-08-12

- Import flow rebuilt around a real queue: imports run in the background,
  no longer take over the app, and several tracks can line up at once.
- Version numbers dropped the alpha suffix; StemDeck remains alpha.

---

Releases before 0.9.0 were alpha snapshots (0.8.0-alpha.*); see the
upstream release history for those.
