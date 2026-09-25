#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/acl_staging.json
rm -f /app/output/effective_rights_matrix.json
mkdir -p /app/state /app/output
