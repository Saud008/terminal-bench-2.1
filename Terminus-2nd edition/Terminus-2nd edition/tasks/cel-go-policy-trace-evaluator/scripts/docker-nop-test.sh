#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
TASK="${REPO}/tasks/cel-go-policy-trace-evaluator"
docker run --rm \
  -v "${TASK}/tests:/tests:ro" \
  cel-go-policy-trace-evaluator:test \
  bash -lc 'cd /app && go build -o /usr/local/bin/celctl ./cmd/celctl && python3 -m pytest /tests/test_outputs.py -q --tb=line'
