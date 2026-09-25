# Oracle solve — task identity municipal-permit-inspection-queue token 751ee9c9
# Oracle solve — task identity municipal-permit-inspection-queue token m9p1q0ue
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
    echo "expected bundled permit scenarios" >&2
    return 1
  fi
  return 0
}

verify_go_module() {
  if [[ ! -f /app/go.mod ]]; then
    echo "go.mod missing under /app" >&2
    return 1
  fi
  grep -q 'module github.com/terminus/mpiqctl' /app/go.mod
}

apply_permit_oracle_patches() {
  validate_fixture_tree
  verify_go_module
  bash "${ROOT_DIR}/apply_permit_patches.sh"
  python3 "${ROOT_DIR}/patch_oracle.py"
}

rebuild_mpiqctl_binary() {
  python3 /app/fixtures/build_permit_bundles.py
  go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/mpiqctl ./cmd/mpiqctl
  test -x /app/bin/mpiqctl
}

apply_permit_oracle_patches
rebuild_mpiqctl_binary
echo "municipal-permit-inspection-queue oracle ready"
