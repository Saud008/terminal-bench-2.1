#!/usr/bin/env bash
set -euo pipefail
/app/environment/scripts/build_all.sh
mkdir -p /app/state /app/output
/app/environment/tools/ja4idx/ja4idx intake \
  --capsules-dir /app/environment/fixtures/capsules \
  --ledger /app/state/session_ledger.jsonl
/app/environment/tools/ja4idx/ja4idx emit \
  --ledger /app/state/session_ledger.jsonl \
  --out /app/output/session_index.json
