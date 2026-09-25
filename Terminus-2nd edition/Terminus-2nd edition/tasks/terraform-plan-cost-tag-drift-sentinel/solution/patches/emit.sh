#!/usr/bin/env bash
# Export-stage helper — delegates to report.sh (audit hot path).
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/report.sh"

emit_violation_report() {
  write_violation_report "$1" "$2" "$3"
}
