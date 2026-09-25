#!/usr/bin/env bash
set -euo pipefail

rm -f /app/work/guildbank.db
rm -f /app/output/guild-audit.json
mkdir -p /app/work /app/output
