# holdfairctl CLI surface

Ingest and export stages are separate: mount loads SQLite, write-assignment-atlas emits the atlas.

Binary path: /app/bin/holdfairctl

Fixed pipeline order for every scenario:

1. mount-library-db --scenario NAME [--fixture-dir PATH]
2. compose-rollup --scenario NAME
3. rank-fair-holds --scenario NAME
4. write-assignment-atlas --scenario NAME

Environment overrides:

- TB3_FIXTURE_DIR replaces default /app/fixtures
- TB3_RECONCILE_DATE replaces reconcile_date from scenario_meta
