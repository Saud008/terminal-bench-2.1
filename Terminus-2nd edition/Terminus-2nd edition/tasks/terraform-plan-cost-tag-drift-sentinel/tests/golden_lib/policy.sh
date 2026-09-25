#!/usr/bin/env bash
# Deny and waiver policy evaluation helpers.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

# Policy helpers are implemented inside report.sh for audit isolation.
