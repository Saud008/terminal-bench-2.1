#!/usr/bin/env bash
# Risk severity weight loader from /app/config/severity-weights.json
set -euo pipefail
python3 -c "import json,sys; json.load(open(sys.argv[1]))" "${1:-/app/config/severity-weights.json}"
