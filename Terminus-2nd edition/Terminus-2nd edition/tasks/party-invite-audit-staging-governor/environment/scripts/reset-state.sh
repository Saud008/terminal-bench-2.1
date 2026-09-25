#!/usr/bin/env bash
set -euo pipefail

rm -f /app/work/party.db
rm -f /app/output/party-audit.json
rm -f /app/state/party-audit-snapshot.json
mkdir -p /app/work /app/output /app/state
