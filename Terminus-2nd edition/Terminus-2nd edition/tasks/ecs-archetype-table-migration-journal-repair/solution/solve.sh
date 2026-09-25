#!/usr/bin/env bash
set -euo pipefail

SELF="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SELF")"

INSTALLER="${SCRIPT_DIR}/oracle/install_archecore_oracle.py"
[[ -f "${INSTALLER}" ]] || { echo "oracle: install_archecore_oracle.py not found" >&2; exit 1; }

python3 "${INSTALLER}"
