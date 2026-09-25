#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
bash apply_compat_hunks.sh
exec python3 run_avsc_oracle.py
