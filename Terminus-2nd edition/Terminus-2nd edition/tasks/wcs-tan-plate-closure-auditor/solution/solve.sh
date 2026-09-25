#!/usr/bin/env bash
# Oracle solve — task identity wcs-tan-plate-closure-auditor token wtpca9041
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

validate_fixture_tree() {
  local scenario_dir="/app/fixtures/scenarios"
  if [[ ! -d "${scenario_dir}" ]]; then
    echo "fixture scenarios directory missing" >&2
    return 1
  fi
  local count
  count="$(find "${scenario_dir}" -maxdepth 1 -name '*.json' | wc -l)"
  if [[ "${count}" -lt 5 ]]; then
    echo "expected bundled plate scenarios" >&2
    return 1
  fi
}

verify_go_module() {
  [[ -f /app/go.mod ]] || { echo "go.mod missing" >&2; return 1; }
  grep -q 'module github.com/terminus/platclosectl' /app/go.mod
}

validate_fixture_tree
verify_go_module
bash "${ROOT_DIR}/apply_frontier.sh"
bash /app/scripts/rebuild-platclosectl.sh
echo "wcs-tan-plate-closure-auditor oracle ready"
