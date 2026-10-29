#!/bin/bash
set -euo pipefail
# Explicit test installation, never the user's existing StemDeck runtime/library.
cd "$(dirname "$0")"
DATA="$HOME/Library/Application Support/StemDeck-preview"
DMG="$PWD/StemDeck-macOS-arm64.dmg"
ARCHIVE="StemDeck-runtime-macOS-arm64.tar.zst"
if [[ ! -f "$DMG" || ! -f "$ARCHIVE" ]]; then
  echo 'Keep this command, the DMG and the runtime archive together in the extracted artifact folder.' >&2
  exit 1
fi
/usr/bin/shasum -a 256 -c SHA256SUMS-preview.txt
printf '%s\n' 'Apple Silicon local preview. Uses its own StemDeck-preview data directory.' \
  'Uses BS-Roformer-SW for six stems and aufr33/viperx for lead/backing.' \
  'Weights are NOT bundled. First jobs download them (~700 MB for SW, karaoke size unverified).' \
  'Their licences/provenance are unresolved. No quality, speed or MPS acceptance is claimed.' \
  'Setup can also download beat/sections/Demucs/Whisper support models in that preview directory.' \
  'This also installs the paired Python/Torch runtime in the preview directory.'
read -r -p 'Type RUN to install the preview runtime and enable first-job model downloads: ' answer
[[ "$answer" == RUN ]] || exit 0
mkdir -p "$DATA/downloads"
cp "$ARCHIVE" "$DATA/downloads/$ARCHIVE"
# Existing setup verifies the manifest hash again before extraction.
export STEMDECK_DATA_DIR="$DATA"
export STEMDECK_JOBS_DIR="$DATA/jobs"
export STEMDECK_DEFAULT_JOBS_DIR="$DATA/jobs"
export STEMDECK_SETTINGS_DIR="$DATA/settings"
export STEMDECK_SEPARATION_ENGINE=roformer-sw
export STEMDECK_ROFORMER_SW_ACCEPT=1
export STEMDECK_KARAOKE_MODEL=mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt
MOUNT="$(mktemp -d /tmp/stemdeck-preview.XXXXXX)"
trap 'hdiutil detach "$MOUNT" >/dev/null 2>&1 || true; rmdir "$MOUNT" 2>/dev/null || true' EXIT
hdiutil attach "$DMG" -readonly -nobrowse -mountpoint "$MOUNT"
"$MOUNT/StemDeck.app/Contents/MacOS/stemdeck"
