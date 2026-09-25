#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=1
export GOFLAGS="-mod=readonly"
export GOCACHE="${GOCACHE:-/opt/gocache}"
export GOMODCACHE="${GOMODCACHE:-/go/pkg/mod}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in \
  "${SCRIPT_DIR}/files" \
  "${SCRIPT_DIR}" \
  "/solution/files" \
  "/solution" \
  "/oracle/solution" \
  "/task/solution"; do
  if [[ -f "${candidate}/golden_parse.go" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done

if [[ -z "${SOL_DIR}" ]]; then
  echo "oracle: golden sources not found" >&2
  exit 1
fi

cp -f "${SOL_DIR}/golden_parse.go" "${APP_ROOT}/internal/mailparse/parse.go"
cp -f "${SOL_DIR}/golden_prepare.go" "${APP_ROOT}/internal/thread/prepare.go"
cp -f "${SOL_DIR}/golden_link.go" "${APP_ROOT}/internal/thread/link.go"
cp -f "${SOL_DIR}/golden_root.go" "${APP_ROOT}/internal/thread/root.go"
cp -f "${SOL_DIR}/golden_assign.go" "${APP_ROOT}/internal/thread/assign.go"
cp -f "${SOL_DIR}/golden_store.go" "${APP_ROOT}/internal/store/store.go"
cp -f "${SOL_DIR}/golden_snapshot.go" "${APP_ROOT}/internal/staging/snapshot.go"
cp -f "${SOL_DIR}/golden_publish.go" "${APP_ROOT}/internal/export/publish.go"
cp -f "${SOL_DIR}/golden_main.go" "${APP_ROOT}/cmd/mailindex/main.go"
cp -f "${SOL_DIR}/golden_writer.go" "${APP_ROOT}/internal/staging/writer.go"
cp -f "${SOL_DIR}/golden_wrap.go" "${APP_ROOT}/internal/export/wrap.go"

cd "${APP_ROOT}"
go build -mod=readonly -o /usr/local/bin/mailindex ./cmd/mailindex
test -x /usr/local/bin/mailindex

bash "${APP_ROOT}/scripts/reset-state.sh"

set +e
mailindex index \
  --mail-dir "${APP_ROOT}/fixtures/mail" \
  --thread-db "${APP_ROOT}/data/thread.db" \
  --output "${APP_ROOT}/output/thread-index.json"
code=$?
set -e

if [[ ! -f "${APP_ROOT}/output/thread-index.json" ]]; then
  echo "oracle: thread index missing" >&2
  exit 1
fi
if [[ "$code" -gt 2 ]]; then
  exit 1
fi

echo "mailindex oracle applied"
