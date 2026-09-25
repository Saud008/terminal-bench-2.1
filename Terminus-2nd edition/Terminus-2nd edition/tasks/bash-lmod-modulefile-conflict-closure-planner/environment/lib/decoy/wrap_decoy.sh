#!/bin/bash
# Optional decoy wrapper — not used by export hot path.
set -euo pipefail
wrap_module_name() {
  local name="$1"
  echo "wrap-${name}"
}
