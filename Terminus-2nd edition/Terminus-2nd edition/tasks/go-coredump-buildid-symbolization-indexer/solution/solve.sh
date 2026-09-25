# Oracle solve — task identity go-coredump-buildid-symbolization-indexer token 1066c154
#!/bin/bash
set -euo pipefail
export PATH="/usr/local/go/bin:${PATH}"
APP_ROOT="${APP_ROOT:-/app}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_DIR=""
for candidate in \
    "${SCRIPT_DIR}/patches" \
    "/solution/patches" \
    "/oracle/solution/patches" \
    "/task/solution/patches"; do
    if [ -f "${candidate}/internal__gnubuildid__buildid.go.patch" ]; then
        PATCH_DIR="${candidate}"
        break
    fi
done
if [ -z "${PATCH_DIR}" ]; then
    echo "oracle: patch directory not found" >&2
    exit 1
fi

apply_patch() {
    patch -p0 --forward --batch -d "${APP_ROOT}" -i "${PATCH_DIR}/$1"
}

apply_patch internal__gnubuildid__buildid.go.patch
apply_patch internal__vmarange__locate.go.patch
apply_patch internal__symcatalog__catalog.go.patch
apply_patch internal__splitpath__resolve.go.patch
apply_patch internal__orchestrate__frame_symbol.go.patch
apply_patch internal__crashfold__group.go.patch
apply_patch internal__frozenstage__write.go.patch
apply_patch internal__indexsql__export.go.patch
cd "${APP_ROOT}"
go mod tidy
go build -mod=readonly -trimpath -ldflags="-s -w" -o "${APP_ROOT}/bin/coreidx" ./cmd/coreidx
bash "${APP_ROOT}/scripts/reset-state.sh"
CRASH="${TB3_CRASH_DIR:-${APP_ROOT}/fixtures/crashes}"
"${APP_ROOT}/bin/coreidx" ingest --crash-dir "$CRASH" --catalog "${APP_ROOT}/fixtures/catalog/build_index.json" --staging "${APP_ROOT}/state/crash_staging.jsonl"
"${APP_ROOT}/bin/coreidx" export --staging "${APP_ROOT}/state/crash_staging.jsonl" --sqlite "${APP_ROOT}/output/crash_index.sqlite" --summary "${APP_ROOT}/output/crash_summary.json"
