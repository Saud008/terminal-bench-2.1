# overbookctl command reference

Financial displacement pipeline: database mount, revenue snapshot seal, night optimization, atlas publish.

Binary path: /app/bin/overbookctl

Fixed pipeline order for every scenario:

1. open-database --scenario NAME [--fixture-dir PATH]
2. freeze-capacity-snapshot --scenario NAME
3. solve-overbook-plan --scenario NAME
4. publish-displacement-atlas --scenario NAME

Environment overrides:

- TB3_FIXTURE_DIR replaces default /app/fixtures
- TB3_NIGHT_DATE replaces night_date from scenario_meta

Legacy compatibility verbs are accepted per route.go alias table.
