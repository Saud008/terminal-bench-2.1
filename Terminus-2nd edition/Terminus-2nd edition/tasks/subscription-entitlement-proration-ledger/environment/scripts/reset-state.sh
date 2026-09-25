#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/billing.db /app/work/entitlement-buffer.json
rm -f /app/output/subscription-invoices.json /app/output/entitlement-ledger.jsonl
echo '{"reconcile_pass":0,"publish_pass":0}' > /app/state/reconcile-pass.json
