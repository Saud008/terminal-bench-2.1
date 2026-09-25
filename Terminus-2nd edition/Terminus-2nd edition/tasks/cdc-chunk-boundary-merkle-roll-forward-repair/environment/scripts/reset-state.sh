#!/usr/bin/env bash
set -euo pipefail

rm -rf /app/state /app/output/*
mkdir -p /app/state /app/output
echo "state reset"
