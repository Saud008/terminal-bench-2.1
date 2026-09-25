#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

patch -d /app -p1 < "${ROOT}/patches/internal/wv/qa.rs.patch"
patch -d /app -p1 < "${ROOT}/patches/internal/wv/qb.rs.patch"
patch -d /app -p1 < "${ROOT}/patches/internal/wv/qc.rs.patch"
patch -d /app -p1 < "${ROOT}/patches/internal/wv/qd.rs.patch"
patch -d /app -p1 < "${ROOT}/patches/internal/wv/qe.rs.patch"
patch -d /app -p1 < "${ROOT}/patches/internal/wv/qf.rs.patch"
patch -d /app -p1 < "${ROOT}/patches/internal/wv/qg.rs.patch"
patch -d /app -p1 < "${ROOT}/patches/internal/wv/qh.rs.patch"
patch -d /app -p1 < "${ROOT}/patches/internal/wv/qi.rs.patch"
patch -d /app -p1 < "${ROOT}/patches/internal/wv/qj.rs.patch"
