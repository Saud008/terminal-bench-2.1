#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/cms-merge-stage.json /app/state/merge-generation.json
rm -rf /app/output/*
mkdir -p /app/state /app/output
