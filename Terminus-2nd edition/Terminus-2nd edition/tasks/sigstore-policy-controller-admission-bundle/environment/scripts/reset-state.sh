#!/usr/bin/env bash
# Resets slsacip's staged witness state and published admission ledger output.
set -euo pipefail

rm -rf /app/state/slsacip /app/output
mkdir -p /app/state/slsacip /app/output
