#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +

install -m 0644 "${ROOT_DIR}/files/oracle_overlap_pick.go" /app/internal/policyoverlap/overlap_pick.go
install -m 0644 "${ROOT_DIR}/files/oracle_ceiling_delta.go" /app/internal/temporalceiling/ceiling_delta.go
install -m 0644 "${ROOT_DIR}/files/oracle_category_ok.go" /app/internal/categoryguard/category_ok.go
install -m 0644 "${ROOT_DIR}/files/oracle_alias_resolve.go" /app/internal/codealias/alias_resolve.go
install -m 0644 "${ROOT_DIR}/files/oracle_atlas_publish.go" /app/internal/atlaswriter/atlas_publish.go
