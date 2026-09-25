# demurctl CLI surface

demurctl is installed at /app/bin/demurctl. All paths are absolute.

## Subcommands

| Verb | Purpose |
|------|---------|
| load-yard | Load scenario JSON into /app/state/yard.db and reset clock_pass to zero |
| run-dwell-ledger | Advance dwell clock, write /app/work/dwell-ledger.json, populate staged_dwell |
| publish-invoices | Emit /app/output/demurrage-invoices.json when clock_pass is positive |

## load-yard flags

- --scenario NAME required scenario stem matching fixtures/scenarios/NAME.json
- --fixture-dir PATH defaults to /app/fixtures

Environment TB3_FIXTURE_DIR overrides --fixture-dir for hidden overlay runs.

## Pipeline order

Operators must run load-yard, then run-dwell-ledger, then publish-invoices. publish-invoices rejects when clock_pass is zero per invoice-publish-contract.md.

## Rebuild and reset

Rebuild with /app/scripts/verifier-rebuild.sh. Reset /app/state, /app/work, and /app/output with /app/scripts/reset-state.sh before cross-run checks.
