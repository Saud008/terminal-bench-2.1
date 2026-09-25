# Oracle solve — task identity customs-tariff-origin-rule-classifier token c7f3a891
#!/usr/bin/env bash
set -euo pipefail

PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

validate_fixture_tree() {
  local manifest_dir="/app/fixtures/manifests"
  if [[ ! -d "${manifest_dir}" ]]; then
    echo "fixture manifests directory missing" >&2
    return 1
  fi
  local count
  count="$(find "${manifest_dir}" -maxdepth 1 -name '*.json' | wc -l)"
  if [[ "${count}" -lt 5 ]]; then
    echo "expected bundled customs manifests" >&2
    return 1
  fi
  return 0
}

verify_go_module() {
  if [[ ! -f /app/go.mod ]]; then
    echo "go.mod missing under /app" >&2
    return 1
  fi
  grep -q 'module github.com/terminus/originctl' /app/go.mod
}

prepare_oracle_frontier() {
  validate_fixture_tree
  verify_go_module
  bash "${ROOT_DIR}/apply_frontier.sh"
}

rebuild_originctl_binary() {
  python3 /app/fixtures/build_fixtures.py
  go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/originctl ./cmd/originctl
  test -x /app/bin/originctl
}

prepare_oracle_frontier
rebuild_originctl_binary
echo "customs-tariff-origin-rule-classifier oracle ready"
