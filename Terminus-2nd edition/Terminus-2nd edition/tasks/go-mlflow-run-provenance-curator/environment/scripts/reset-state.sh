#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/provenance-staging.json /app/work/provenance.db /app/output/*
mkdir -p /app/state /app/work /app/output
