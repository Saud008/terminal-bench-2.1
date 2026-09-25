# ppareconctl CLI surface

Binary path: /app/bin/ppareconctl

## materialize-lines

Loads a scenario JSON from /app/fixtures/scenarios or --fixture-dir, aligns meter readings to 15-minute UTC floors, applies curtailment masks, resolves market prices, computes settlement lines, and writes:

- /app/state/settlement-lines.jsonl (one JSON object per line)
- /app/state/ppa-settlement.db (meta plus settlement_lines table)

Flags:

- --scenario NAME (required)
- --fixture-dir PATH (default /app/fixtures)

## rollup-billing-invoice

Reads materialized settlement lines and publishes /app/output/invoice-rollup.json with billing day counts and totals.

Requires materialize-lines for the same scenario first.

Flags:

- --scenario NAME (required)
- --fixture-dir PATH (default /app/fixtures)

Rebuild after Go edits: /app/scripts/verifier-rebuild.sh

Reset workspace: /app/scripts/reset-state.sh
