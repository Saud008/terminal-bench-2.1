#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
for d in "$root"/fixtures/scenarios/*/; do
  test -f "$d/zones.json"
  test -f "$d/fires.json"
done
