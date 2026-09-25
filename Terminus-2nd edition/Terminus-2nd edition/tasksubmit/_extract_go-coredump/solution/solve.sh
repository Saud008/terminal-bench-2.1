# Oracle solve — task identity go-coredump-buildid-symbolization-indexer token 1066c154
#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
export PATH="/usr/local/go/bin:${PATH}"
patch -p0 --forward --batch -d /app -i patches/internal__gnubuildid__buildid.go.patch
patch -p0 --forward --batch -d /app -i patches/internal__vmarange__locate.go.patch
patch -p0 --forward --batch -d /app -i patches/internal__symcatalog__catalog.go.patch
patch -p0 --forward --batch -d /app -i patches/internal__splitpath__resolve.go.patch
patch -p0 --forward --batch -d /app -i patches/internal__orchestrate__frame_symbol.go.patch
patch -p0 --forward --batch -d /app -i patches/internal__crashfold__group.go.patch
patch -p0 --forward --batch -d /app -i patches/internal__frozenstage__write.go.patch
patch -p0 --forward --batch -d /app -i patches/internal__indexsql__export.go.patch
cd /app
go mod tidy
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/coreidx ./cmd/coreidx
bash /app/scripts/reset-state.sh
CRASH="${TB3_CRASH_DIR:-/app/fixtures/crashes}"
/app/bin/coreidx ingest --crash-dir "$CRASH" --catalog /app/fixtures/catalog/build_index.json --staging /app/state/crash_staging.jsonl
/app/bin/coreidx export --staging /app/state/crash_staging.jsonl --sqlite /app/output/crash_index.sqlite --summary /app/output/crash_summary.json
