# CLI surface

Binary /app/bin/qqraftctl

replay-log --cluster ID --scenario SLUG [--fixture-dir DIR]
merge-snapshot --cluster ID --scenario SLUG [--fixture-dir DIR]
audit-membership --cluster ID --scenario SLUG
export-committed --cluster ID --scenario SLUG [--output-ledger PATH] [--output-seal PATH]

Fixture dir defaults to /app/fixtures. TB3_FIXTURE_DIR overrides for hidden scenarios.

After authenticity-policy edits under `/app/internal/`, leave `/app/bin/qqraftctl` current (`/app/scripts/verifier-rebuild.sh`).

