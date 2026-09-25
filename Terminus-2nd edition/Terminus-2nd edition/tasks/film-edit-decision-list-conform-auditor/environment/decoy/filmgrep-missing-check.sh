#!/usr/bin/env bash
# Legacy grep-based missing media check — not used by edl-conform-audit.
set -euo pipefail
reel="$1"
dir="$2"
grep -R "${reel}" "${dir}" >/dev/null 2>&1
