#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p0 -d /app < files/patches/parse_lines.patch
patch -p0 -d /app < files/patches/rank_winners.patch
patch -p0 -d /app < files/patches/ca_reader.patch
patch -p0 -d /app < files/patches/krl_reader.patch
patch -p0 -d /app < files/patches/scope_resolver.patch
patch -p0 -d /app < files/patches/wildcard_policy.patch
patch -p0 -d /app < files/patches/witness_binder.patch
cd /app
make install-sshap
bash /app/scripts/reset-state.sh
CFG=/app/config/sshap.json
PR=$(jq -r '.principals_dir' "$CFG")
CA=$(jq -r '.ca_dir' "$CFG")
KRL=$(jq -r '.krl' "$CFG")
LED=$(jq -r '.ledger' "$CFG")
MAT=$(jq -r '.match_dir' "$CFG")
PRB=$(jq -r '.probes' "$CFG")
OUT=$(jq -r '.attestation_out' "$CFG")
/usr/local/bin/sshap ingest --principals-dir "$PR" --ca-dir "$CA" --krl "$KRL" --ledger "$LED"
/usr/local/bin/sshap attest --ledger "$LED" --match-dir "$MAT" --probes "$PRB" --out "$OUT"
