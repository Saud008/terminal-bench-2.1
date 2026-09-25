#!/usr/bin/env bash
# systemd-timer-planner — load / forecast / write-report dispatch.
set -euo pipefail

APP_ROOT="/app"
export APP_ROOT

usage() {
  cat <<'EOF'
Usage:
  systemd-timer-planner load --bundle <timer.bundle> --timer-name <name>
  systemd-timer-planner forecast --bundle <timer.bundle> --context <context.json> --now <iso>
  systemd-timer-planner write-report --bundle <timer.bundle> --out <drift-report.json>
EOF
  exit 1
}

[ $# -ge 1 ] || usage
cmd="$1"
shift

case "${cmd}" in
  load)
    exec bash "${APP_ROOT}/scripts/load.sh" "$@"
    ;;
  forecast)
    exec bash "${APP_ROOT}/scripts/forecast.sh" "$@"
    ;;
  write-report)
    exec bash "${APP_ROOT}/scripts/write_report.sh" "$@"
    ;;
  *)
    usage
    ;;
esac
