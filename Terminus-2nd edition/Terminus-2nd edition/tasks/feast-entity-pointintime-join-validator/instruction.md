Machine-learning feature-store operators need feastctl for point-in-time feature join validation and online/offline parity eval on the working Go baseline under /app. The tool loads JSON scenarios from /app/fixtures/scenarios/, writes a normalized join staging snapshot at /app/state/pit-staging.json, validates temporal entity-key point-in-time joins under TTL window constraints and backfill partition rules, persists parity rows in /app/work/parity.db with canonical summary digests, and writes a summary report JSON to the path given by --output under /app/output/. This is a machine-learning feature-join and parity-eval workflow.

Your work must satisfy every contract cited below. The internal/decoy package is not on the load, validate, or report hot path and must not be edited for a correct export.

Build feastctl at /usr/local/bin/feastctl from /app. Subcommands:

  feastctl load --seed <seed> --scenario <name>
  feastctl validate join --seed <seed> --scenario <name>
  feastctl export report --seed <seed> --scenario <name> --output <path>

After load, /app/state/pit-staging.json must include ingest_seq, entity_keys, ttl_seconds, as_of_entries, and materialized events with seed-scoped entity identifiers.

Point-in-time event selection must follow /app/docs/point-in-time-join.md. Composite entity matching must follow /app/docs/entity-key-contract.md. TTL filtering must follow /app/docs/ttl-window.md. Backfill partition scoping must follow /app/docs/backfill-partition.md. Online versus offline value comparison must follow /app/docs/online-offline-parity.md. Duplicate event timestamp resolution must follow /app/docs/duplicate-event-ts.md.

validate join must erase every existing row in parity_runs, parity_rows, and parity_summary inside /app/work/parity.db before inserting the new run for the requested seed and scenario. export report then reads staging and the latest run for that seed and scenario and writes summary JSON under /app/output/ per /app/docs/parity-report-schema.md including audit_digest.

Bundled scenarios and seeds live under /app/fixtures/. Hidden verifier scenarios may appear under TB3_FIXTURE_DIR with TB3_TTL_BIAS second offset when set.

Rebuild feastctl from /app after changing Go sources. Do not edit /app/docs/, /app/config/, /app/fixtures/, or anything under /tests/.
