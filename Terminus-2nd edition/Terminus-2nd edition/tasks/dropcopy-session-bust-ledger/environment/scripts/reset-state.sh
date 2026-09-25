#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/dropcopy-stage.json /app/state/replay-generation.json /app/work/dropcopy.db
rm -rf /app/output/*
mkdir -p /app/state /app/work /app/output
