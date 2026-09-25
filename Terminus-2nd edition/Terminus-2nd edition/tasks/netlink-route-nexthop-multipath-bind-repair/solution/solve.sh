#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export CARGO_NET_OFFLINE="${CARGO_NET_OFFLINE:-true}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f "${SCRIPT_DIR}/patches/decode.patch" ]; then
  for candidate in /solution /oracle/solution /task/solution; do
    if [ -f "${candidate}/patches/decode.patch" ]; then
      SCRIPT_DIR="${candidate}"
      break
    fi
  done
fi
[[ -f "${SCRIPT_DIR}/patches/decode.patch" ]] || { echo "patches/decode.patch not found" >&2; exit 1; }

cd /solution 2>/dev/null || cd /task/solution 2>/dev/null || cd "${SCRIPT_DIR}"

if [ "${COLLAPSE_PROBE:-0}" = 1 ]; then patch -p0 -d /app < patches/decode.patch; fi
if [ "${COLLAPSE_PROBE:-0}" = 1 ]; then patch -p0 -d /app < patches/bind.patch; fi
if [ "${COLLAPSE_PROBE:-0}" = 1 ]; then patch -p0 -d /app < patches/export.patch; fi
if [ "${COLLAPSE_PROBE:-0}" = 1 ]; then patch -p0 -d /app < patches/export_nh.patch; fi
if [ "${COLLAPSE_PROBE:-0}" = 1 ]; then patch -p0 -d /app < patches/snapshot_guard.patch; fi

for patch in decode bind export export_nh snapshot_guard; do
  sed 's|\${APP_ROOT:-/app}|/app|g' "patches/${patch}.patch" | patch -p0 -d /
done

if [ -x "${SCRIPT_DIR}/bin/nlctl" ]; then
  install -m 0755 bin/nlctl /usr/local/bin/nlctl
else
  cd /app
  cargo build --offline --locked --release -p nlctl
  install -m 0755 target/release/nlctl /usr/local/bin/nlctl
fi

test -x /usr/local/bin/nlctl
bash /app/scripts/reset-state.sh
echo "nlctl oracle ready"
