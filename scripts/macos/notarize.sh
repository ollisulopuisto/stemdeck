#!/usr/bin/env bash
# A successful upload is not acceptance. Require Apple's final Accepted state.
set -euo pipefail
FILE="${1:?artifact required}"
: "${APPLE_ID:?Missing APPLE_ID}"
: "${APPLE_APP_PASSWORD:?Missing APPLE_APP_PASSWORD}"
RESULT="$(mktemp)"
trap 'rm -f "$RESULT"' EXIT
xcrun notarytool submit "$FILE" \
  --apple-id "$APPLE_ID" --password "$APPLE_APP_PASSWORD" \
  --team-id "${APPLE_TEAM_ID:-LWSR8T5392}" --wait --output-format json > "$RESULT"
python3 - "$RESULT" <<'PY'
import json,sys
result=json.load(open(sys.argv[1]))
status=result.get('status')
print('Apple notarization status:',status)
if status!='Accepted':raise SystemExit('Apple did not accept this artifact; release stopped')
PY
