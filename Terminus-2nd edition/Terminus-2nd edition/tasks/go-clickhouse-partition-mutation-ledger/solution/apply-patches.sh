#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
patch -p1 --forward -d /app < patches/partkey.patch
patch -p1 --forward -d /app < patches/mutver.patch
patch -p1 --forward -d /app < patches/replag.patch
patch -p1 --forward -d /app < patches/detach.patch
patch -p1 --forward -d /app < patches/sqlledger.patch
patch -p1 --forward -d /app < patches/ledgerbuf.patch
patch -p1 --forward -d /app < patches/readiness.patch
