#!/usr/bin/env bash
# Verifier helper — confirms scenario roots exist before pytest overlay cases.
set -euo pipefail
root="${WHRES_SCENARIO_ROOT:-/app/fixtures/scenarios}"
test -d "$root"
