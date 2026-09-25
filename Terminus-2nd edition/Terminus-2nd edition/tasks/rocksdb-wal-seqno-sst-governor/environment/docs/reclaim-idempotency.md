# Reclaim idempotency

reclaimed_bytes is the sum of size_bytes across selected_sst on the current planning pass.

Pass 1 records reclaimed_bytes in /app/state/compact-state.json.

Pass 2 with unchanged staging must emit the same reclaimed_bytes as pass 1.

Re-adding pass 1 reclaimed totals to a fresh sum is incorrect.
