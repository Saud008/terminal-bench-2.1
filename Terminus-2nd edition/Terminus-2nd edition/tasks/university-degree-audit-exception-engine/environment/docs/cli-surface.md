# degaudit CLI surface

Binary path: /app/bin/degaudit

Fixed pipeline order for every scenario:

1. load-scenario --scenario NAME [--fixture-dir PATH]
2. materialize-transcript --scenario NAME
3. run-audit --scenario NAME
4. publish-report --scenario NAME

Environment overrides:

- TB3_FIXTURE_DIR replaces default /app/fixtures
- TB3_AUDIT_DATE replaces audit_date from scenario_meta (catalog year still from catalog_year column)
