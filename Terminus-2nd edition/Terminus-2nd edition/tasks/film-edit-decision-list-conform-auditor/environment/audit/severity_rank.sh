#!/usr/bin/env bash
# Map finding categories to numeric rank for report sorting (not on stage hot path).
set -euo pipefail
category="$1"
case "${category}" in
  reel_unmapped) echo 10 ;;
  handle_overflow) echo 20 ;;
  timecode_mismatch) echo 30 ;;
  pulldown_drift) echo 40 ;;
  missing_media) echo 50 ;;
  *) echo 99 ;;
esac
