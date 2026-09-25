#!/usr/bin/env bash
set -euo pipefail
gclint_config() {
  jq -r "$1" /app/config/gclint.json
}
