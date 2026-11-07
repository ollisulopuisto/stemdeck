#!/usr/bin/env bash
# Retry only transient URLSession failures; never turn failed validation green.
set -euo pipefail
FILE="${1:?artifact required}"
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT
for action in staple validate; do
  attempt=1
  while :; do
    if xcrun stapler "$action" "$FILE" > "$LOG" 2>&1; then
      cat "$LOG"
      break
    else
      status=$?
    fi
    cat "$LOG" >&2
    # An invalid/missing ticket or signature is not a network retry case.
    # URLSession -1001 = timeout, -1005 = connection lost, -1009 = offline.
    if [[ "$attempt" -ge 3 ]] || ! grep -Eq 'NSURLErrorDomain Code=-(1001|1005|1009)([^0-9]|$)' "$LOG"; then
      echo "ERROR: stapler $action failed; release stopped" >&2
      exit "$status"
    fi
    delay=$((attempt * 10))
    echo "Retrying stapler $action after transient network failure in ${delay}s ($attempt/3)" >&2
    sleep "$delay"
    attempt=$((attempt + 1))
  done
done
