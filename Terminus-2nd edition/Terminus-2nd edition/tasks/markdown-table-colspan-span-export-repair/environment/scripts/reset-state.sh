#!/usr/bin/env bash
set -euo pipefail

rm -rf /app/output
mkdir -p /app/output
rm -f /app/state/grid.snapshot.json
mkdir -p /app/state

if [[ -d /opt/fixture-seed/tables ]]; then
  rm -rf /app/fixtures/tables
  mkdir -p /app/fixtures/tables
  cp -a /opt/fixture-seed/tables/. /app/fixtures/tables/
fi

if [[ -f /opt/fixture-seed/manifest.json ]]; then
  cp /opt/fixture-seed/manifest.json /app/fixtures/manifest.json
fi
