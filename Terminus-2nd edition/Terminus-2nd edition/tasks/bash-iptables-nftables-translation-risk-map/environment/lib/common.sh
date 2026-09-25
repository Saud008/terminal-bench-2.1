#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

pair_fingerprint() {
  local manifest="$1" ipt="$2" nft="$3"
  cat "$manifest" "$ipt" "$nft" | sha256sum | awk '{print $1}'
}
