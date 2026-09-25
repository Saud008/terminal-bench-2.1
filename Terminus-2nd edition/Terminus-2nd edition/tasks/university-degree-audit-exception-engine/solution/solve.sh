#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${ROOT_DIR}/files"
cd /app
patch -p1 --forward --batch < "${FILES}/oracle_catalog_year.patch"
patch -p1 --forward --batch < "${FILES}/oracle_transfer_equiv.patch"
patch -p1 --forward --batch < "${FILES}/oracle_subst_expiry.patch"
patch -p1 --forward --batch < "${FILES}/oracle_repeat_fold.patch"
patch -p1 --forward --batch < "${FILES}/oracle_req_closure.patch"
patch -p1 --forward --batch < "${FILES}/oracle_transcript_fp.patch"
patch -p1 --forward --batch < "${FILES}/oracle_pass_seal.patch"
patch -p1 --forward --batch < "${FILES}/oracle_publish_report.patch"
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
python3 /app/fixtures/gen_degree_db.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/degaudit ./cmd/degaudit
test -x /app/bin/degaudit
echo "university-degree-audit-exception-engine oracle ready"
