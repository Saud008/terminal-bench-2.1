#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/settlement-lines.jsonl /app/state/ppa-settlement.db
rm -f /app/output/invoice-rollup.json
rm -rf /app/work/*
