#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
APP_ROOT="${APP_ROOT:-/app}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PATCH_ROOT=""
for candidate in "${SCRIPT_DIR}/patches" "/solution/patches" "/oracle/solution/patches"; do
  if [[ -d "${candidate}" ]]; then
    PATCH_ROOT="${candidate}"
    break
  fi
done
[[ -n "${PATCH_ROOT}" ]] || { echo "oracle patches not found" >&2; exit 1; }

MODULES=(
  ft26
  kx42
  ul82
  st38
  hn55
  cv20
  je67
  qg71
  yl49
  mp93
  rw14
  zq81
)

for mod in "${MODULES[@]}"; do
  src="${PATCH_ROOT}/${mod}.rs"
  [[ -f "${src}" ]] || { echo "missing oracle patch ${src}" >&2; exit 1; }
  install -m 0644 "${src}" "${APP_ROOT}/src/${mod}.rs"
done

cd "${APP_ROOT}"
/usr/local/cargo/bin/cargo check --locked -p fbpkg
/usr/local/cargo/bin/cargo build --locked --release -p fbpkg
install -m 0755 target/release/fbdecode /usr/local/bin/fbdecode
test -x /usr/local/bin/fbdecode
echo "flatbuffers-vtable-wire-json-bundler oracle ready"
