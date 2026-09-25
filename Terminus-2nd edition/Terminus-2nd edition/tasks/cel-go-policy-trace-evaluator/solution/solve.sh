#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SOLUTION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp -f "${SOLUTION_ROOT}/files/internal/eval/eval.go" "${APP_ROOT}/internal/eval/eval.go"
cp -f "${SOLUTION_ROOT}/files/internal/duration/duration.go" "${APP_ROOT}/internal/duration/duration.go"

cd "${APP_ROOT}"
export PATH="/usr/local/go/bin:${PATH}"
go build -o /usr/local/bin/celctl ./cmd/celctl
