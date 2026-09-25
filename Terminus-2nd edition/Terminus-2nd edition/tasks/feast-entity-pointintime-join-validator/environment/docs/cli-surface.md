# feastctl CLI surface

load --seed --scenario reads scenario JSON, materializes seed-scoped entity identifiers, writes /app/state/pit-staging.json, bumps ingest_seq.

validate join --seed --scenario reads staging, executes point-in-time joins per as_of_entries, deletes all existing rows from parity_runs, parity_rows, and parity_summary, then inserts the new run, rows, and summary into /app/work/parity.db. Prior runs for other seeds or scenarios are not retained across a validate join call.

export report --seed --scenario --output writes summary JSON under /app/output/ after validate join for the same seed and scenario, using the latest remaining run for that seed and scenario.

Fixture directory defaults to /app/fixtures/scenarios unless TB3_FIXTURE_DIR is set.
