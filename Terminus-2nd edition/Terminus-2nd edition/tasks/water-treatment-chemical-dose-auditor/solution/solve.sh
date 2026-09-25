#!/usr/bin/env bash
set -euo pipefail

PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

validate_shift_fixture_tree() {
  local shift_dir="/app/fixtures/plant_shifts"
  if [[ ! -d "${shift_dir}" ]]; then
    echo "plant shift fixtures missing" >&2
    return 1
  fi
  local count
  count="$(find "${shift_dir}" -maxdepth 1 -name '*.json' | wc -l)"
  if [[ "${count}" -lt 5 ]]; then
    echo "expected bundled plant shift bundles" >&2
    return 1
  fi
  return 0
}

verify_cargo_workspace() {
  if [[ ! -f /app/Cargo.toml ]]; then
    echo "Cargo.toml missing under /app" >&2
    return 1
  fi
  grep -q 'wtcdctl' /app/Cargo.toml
}

prepare_oracle_frontier() {
  validate_shift_fixture_tree
  verify_cargo_workspace
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qa.rs.patch"
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qb.rs.patch"
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qc.rs.patch"
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qd.rs.patch"
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qe.rs.patch"
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qf.rs.patch"
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qg.rs.patch"
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qh.rs.patch"
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qi.rs.patch"
  patch -d /app -p1 < "${ROOT_DIR}/patches/internal/wv/qj.rs.patch"
}

rebuild_wtcdctl_binary() {
  python3 /app/fixtures/build_fixtures.py --seed 4821 --out-dir /app/fixtures/plant_shifts
  /usr/local/cargo/bin/cargo build --release
  install -m 0755 /app/target/release/wtcdctl /app/bin/wtcdctl
  test -x /app/bin/wtcdctl
}

prepare_oracle_frontier
rebuild_wtcdctl_binary
bash /app/scripts/reset-workspace.sh
echo "water-treatment-chemical-dose-auditor oracle ready"
