#!/usr/bin/env bash
# Intensity curve row-count guard used by bundled scenario catalog checks.
set -euo pipefail
test -f /app/fixtures/scenarios/baseload-two-region/scenario.json
