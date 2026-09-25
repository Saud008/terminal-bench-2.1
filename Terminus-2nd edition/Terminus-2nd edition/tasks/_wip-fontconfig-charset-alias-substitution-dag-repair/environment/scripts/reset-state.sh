#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output/* /app/state/*
mkdir -p /app/output /app/state
echo 0 > /app/state/compile-seq.txt
