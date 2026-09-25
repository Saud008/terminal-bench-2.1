# CLI surface

Binary /app/bin/sipcdrctl

ingest-transcript --tenant ID --scenario SLUG [--fixture-dir DIR]
compile-dialogs --tenant ID --scenario SLUG [--fixture-dir DIR]
rate-billing --tenant ID --scenario SLUG
export-cdr --tenant ID --scenario SLUG [--db PATH] [--seal PATH]

Fixture dir defaults to /app/fixtures. TB3_FIXTURE_DIR overrides for hidden scenarios.
