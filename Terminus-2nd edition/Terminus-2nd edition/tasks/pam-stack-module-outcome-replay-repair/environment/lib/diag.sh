#!/usr/bin/env bash
# Diagnostic helpers — not invoked by pamreplay export path.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pamreplay_diag_session_gate() {
  echo "session-gate-open"
}

pamreplay_diag_phase_sorter() {
  python3 -c 'import sys; print(",".join(sorted(sys.argv[1:])))' -- "$@"
}
