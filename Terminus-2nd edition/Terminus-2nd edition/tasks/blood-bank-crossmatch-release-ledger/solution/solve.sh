# Oracle solve — task identity blood-bank-crossmatch-release-ledger token bb7c4e91
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
  count="$(find "${scenario_dir}" -maxdepth 1 -name '*.json' | wc -l)"
  if [[ "${count}" -lt 5 ]]; then
    echo "expected bundled blood bank scenarios" >&2
    return 1
  fi
  return 0
}

verify_go_module() {
  if [[ ! -f /app/go.mod ]]; then
    echo "go.mod missing under /app" >&2
    return 1
  fi
  grep -q 'module github.com/terminus/bbreleasectl' /app/go.mod
}

prepare_patch_frontier() {
  validate_fixture_tree
  verify_go_module
  bash "${ROOT_DIR}/apply_frontier.sh"
}

rebuild_bbreleasectl_binary() {
  go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/bbreleasectl ./cmd/bbreleasectl
  test -x /app/bin/bbreleasectl
}

prepare_patch_frontier
rebuild_bbreleasectl_binary
echo "blood-bank-crossmatch-release-ledger oracle ready"
