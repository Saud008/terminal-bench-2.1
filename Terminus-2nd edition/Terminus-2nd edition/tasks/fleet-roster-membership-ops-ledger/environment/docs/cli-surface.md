# CLI surface

Binary `/app/bin/rosterctl` (Python policy modules under `/app/lib/roster/`).

```text
rosterctl replay-log --cluster ID --scenario SLUG [--fixture-dir DIR]
rosterctl merge-snapshot --cluster ID --scenario SLUG [--fixture-dir DIR]
rosterctl audit-membership --cluster ID --scenario SLUG
rosterctl export-committed --cluster ID --scenario SLUG [--output-ledger PATH] [--output-seal PATH]
```

Fixture dir defaults to `/app/fixtures`. `TB3_FIXTURE_DIR` overrides for hidden scenarios.

After policy-module edits under `/app/lib/roster/`, leave `/app/bin/rosterctl` current (`/app/scripts/verifier-rebuild.sh`).
