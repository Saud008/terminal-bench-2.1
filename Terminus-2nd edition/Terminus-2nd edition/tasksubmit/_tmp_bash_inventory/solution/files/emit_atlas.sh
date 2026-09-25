#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
exec python3 "${APP_ROOT}/lib/inventory_engine.py" emit "$@"
