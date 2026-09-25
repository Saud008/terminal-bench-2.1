#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${ROOT_DIR}/files"
cp "${FILES}/demur_oracle_event_sort.go" /app/internal/yardbundle/event_sort.go
sed -i 's/if rank < bestRank/if rank > bestRank/' /app/internal/holdpolicy/precedence.go
sed -i 's/bestRank := int(^uint(0) >> 1)/bestRank := -1/' /app/internal/holdpolicy/precedence.go
cp "${FILES}/demur_oracle_exclude.go" /app/internal/closurecal/exclude.go
cp "${FILES}/demur_oracle_clock_runner.go" /app/internal/pauseclock/clock_runner.go
cp "${FILES}/demur_oracle_tier_calc.go" /app/internal/tarifftier/tier_calc.go
cp "${FILES}/demur_oracle_publish.go" /app/internal/invoicewriter/publish.go
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
