#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
APP=desktop/src-tauri/target/aarch64-apple-darwin/release/bundle/macos/StemDeck.app
# Do not distribute a manifest pointing at upstream or an invented release.
python3 - "$APP/Contents/Resources/runtime-manifest.json" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
assert m['localOnly'] is True and m['runtimeUrl']=='', m
assert m['arch']=='arm64' and len(m['runtimeSha256'])==64
PY
hdiutil verify .build/macos-dist/StemDeck-macOS-arm64.dmg
mkdir -p .build/preview
cp .build/macos-dist/StemDeck-macOS-arm64.dmg .build/preview/
cp .build/StemDeck-runtime-macOS-arm64.tar.zst .build/preview/
cp scripts/macos/Install-and-launch.command .build/preview/
(cd .build/preview && shasum -a 256 StemDeck-macOS-arm64.dmg StemDeck-runtime-macOS-arm64.tar.zst > SHA256SUMS-preview.txt)
