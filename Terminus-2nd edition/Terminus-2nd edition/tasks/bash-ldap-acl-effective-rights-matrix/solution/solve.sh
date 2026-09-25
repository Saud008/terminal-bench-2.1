#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p0 -d /app < files/patches/ldaprm-normalize.patch
patch -p0 -d /app < files/patches/ldaprm-member_closure.patch
patch -p0 -d /app < files/patches/ldaprm-parse_blocks.patch
patch -p0 -d /app < files/patches/ldaprm-scope_match.patch
patch -p0 -d /app < files/patches/ldaprm-rank_aces.patch
patch -p0 -d /app < files/patches/ldaprm-attribute_gate.patch
patch -p0 -d /app < files/patches/ldaprm-inherit_walk.patch
patch -p0 -d /app < files/patches/ldaprm-matrix_builder.patch
cd /app && make install-ldaprm
bash /app/scripts/reset-state.sh
CFG=/app/config/ldaprm.json
LDIF=$(jq -r '.ldif' "$CFG")
GRP=$(jq -r '.groups' "$CFG")
ACL=$(jq -r '.acls' "$CFG")
DEF=$(jq -r '.defaults' "$CFG")
STG=$(jq -r '.staging' "$CFG")
SUB=$(jq -r '.subjects' "$CFG")
OUT=$(jq -r '.matrix_out' "$CFG")
/usr/local/bin/ldaprm ingest --ldif "$LDIF" --groups "$GRP" --acls "$ACL" --defaults "$DEF" --staging "$STG"
/usr/local/bin/ldaprm export --staging "$STG" --subjects "$SUB" --out "$OUT"
