# Oracle solve — task identity elevator-maintenance-callout-dispatcher token e7a1c0em
#!/usr/bin/env bash
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
  count="$(find "${scenario_dir}" -mindepth 1 -maxdepth 1 -type d | wc -l)"
  if [[ "${count}" -lt 5 ]]; then
    echo "expected bundled dispatch scenarios" >&2
    return 1
  fi
  return 0
}

verify_go_module() {
  if [[ ! -f /app/go.mod ]]; then
    echo "go.mod missing under /app" >&2
    return 1
  fi
  grep -q 'module github.com/terminus/calloutd' /app/go.mod
}

prepare_oracle_frontier() {
  validate_fixture_tree
  verify_go_module
  bash "${ROOT_DIR}/apply_frontier.sh"
}

rebuild_calloutd_binary() {
  python3 /app/fixtures/build_callout_rosters.py
  go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/calloutd ./cmd/calloutd
  test -x /app/bin/calloutd
}

prepare_oracle_frontier
rebuild_calloutd_binary
echo "elevator-maintenance-callout-dispatcher oracle ready"
