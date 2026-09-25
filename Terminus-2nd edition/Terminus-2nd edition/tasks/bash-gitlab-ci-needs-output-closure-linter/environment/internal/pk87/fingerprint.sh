#!/usr/bin/env bash
set -euo pipefail
fp_hex() {
  echo -n "$1" | sha256sum | awk '{print $1}'
}
