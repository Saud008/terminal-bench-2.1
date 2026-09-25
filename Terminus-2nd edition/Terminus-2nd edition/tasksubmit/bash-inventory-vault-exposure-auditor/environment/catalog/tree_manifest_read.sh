#!/usr/bin/env bash
set -euo pipefail
python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['tree_id'])" "$1"
