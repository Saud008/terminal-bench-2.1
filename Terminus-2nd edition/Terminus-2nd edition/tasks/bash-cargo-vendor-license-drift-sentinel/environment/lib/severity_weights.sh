#!/usr/bin/env bash
# Severity weight loader — catalog helper, not on ingest hot path.
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
python3 -c "import json; print(json.load(open('${APP_ROOT}/config/severity-weights.json')))"
