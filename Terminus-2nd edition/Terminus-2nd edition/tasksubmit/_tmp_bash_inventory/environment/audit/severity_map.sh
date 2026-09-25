#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
python3 -c "import json; print(json.dumps(json.load(open('${APP_ROOT}/config/severity-weights.json'))))"
