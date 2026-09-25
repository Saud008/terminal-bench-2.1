#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/accession-vault.json /app/work/register.db /app/output/*
mkdir -p /app/state /app/work /app/output
