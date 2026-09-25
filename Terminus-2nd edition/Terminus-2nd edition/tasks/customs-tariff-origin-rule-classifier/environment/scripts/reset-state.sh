#!/usr/bin/env bash
set -euo pipefail
rm -f /app/var/ledger/tariff.db /app/var/workbench/normalized-lines.json /app/var/workbench/origin-scores.json
rm -f /app/output/tariff-classifications.json /app/output/origin-audit.jsonl
echo '{"parse_pass":0,"atlas_pass":0}' > /app/var/run/origin-pass.json
