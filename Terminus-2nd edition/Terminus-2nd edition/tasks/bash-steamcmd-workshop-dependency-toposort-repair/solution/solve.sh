#!/usr/bin/env bash
set -euo pipefail

make -C /solution install

bash /app/scripts/reset-state.sh
/app/bin/workshop-plan plan \
  --manifest-dir /app/fixtures/workshop/001-linear \
  --config /app/config/plan.json \
  --output /app/output/plan.json
