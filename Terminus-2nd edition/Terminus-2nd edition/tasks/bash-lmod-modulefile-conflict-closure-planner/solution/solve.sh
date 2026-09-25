#!/bin/bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
SOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/files"
LIB="${APP_ROOT}/lib"

install -m 0755 "${SOL_DIR}/ingest_catalog.sh" "${LIB}/ingest/ingest_catalog.sh"
install -m 0755 "${SOL_DIR}/dep_closure.sh" "${LIB}/resolve/dep_closure.sh"
install -m 0755 "${SOL_DIR}/conflict_resolve.sh" "${LIB}/resolve/conflict_resolve.sh"
install -m 0755 "${SOL_DIR}/family_swap.sh" "${LIB}/resolve/family_swap.sh"
install -m 0755 "${SOL_DIR}/path_order.sh" "${LIB}/resolve/path_order.sh"
install -m 0755 "${SOL_DIR}/export_plan.sh" "${LIB}/export/export_plan.sh"

/opt/verifier-scripts/rebuild-lmodplan
