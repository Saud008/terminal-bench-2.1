# CLI surface

Binary /app/bin/duelctl

admit-log --arena ID --scenario SLUG [--fixture-dir DIR]
fold-branches --arena ID --scenario SLUG [--fixture-dir DIR]
score-windows --arena ID --scenario SLUG
seal-ledger --arena ID --scenario SLUG [--db PATH] [--seal PATH]

Fixture dir defaults to /app/fixtures. TB3_FIXTURE_DIR overrides for hidden scenarios.
