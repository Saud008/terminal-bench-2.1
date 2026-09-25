#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/fixtures/trees /app/fixtures/catalog.json /app/fixtures/seeds.json
mkdir -p /app/fixtures
cp -a /opt/verifier-fixtures/. /app/fixtures/
rm -f /app/output/*.json 2>/dev/null || true
mkdir -p /app/output
