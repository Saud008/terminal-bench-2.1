#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/pit-staging.json /app/work/parity.db /app/output/*
mkdir -p /app/state /app/work /app/output
