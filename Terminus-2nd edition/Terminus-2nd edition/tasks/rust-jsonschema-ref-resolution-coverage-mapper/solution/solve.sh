#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
patch -d /app --forward --strip=0 < files/patches/01_doc_loader.patch
patch -d /app --forward --strip=0 < files/patches/02_anchor_index.patch
patch -d /app --forward --strip=0 < files/patches/03_visit_guard.patch
patch -d /app --forward --strip=0 < files/patches/04_combinator_cov.patch
patch -d /app --forward --strip=0 < files/patches/05_graph_export.patch
patch -d /app --forward --strip=0 < files/patches/06_report_emit.patch
patch -d /app --forward --strip=0 < files/patches/07_pointer_walk.patch
(cd /app/environment && cargo build --release -p jscovmap)
exec python3 apply_jscov_oracle.py
