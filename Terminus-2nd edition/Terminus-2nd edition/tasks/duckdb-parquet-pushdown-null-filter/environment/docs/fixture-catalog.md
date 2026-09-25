# Fixture catalog

Bundled catalogs live under /app/fixtures/catalog/. Each file describes one logical Parquet table with row groups, column stats, page order metadata, and materialized rows used by the pushdown simulator.

| File | Focus |
|------|-------|
| 01-baseline.json | IS NULL on sensor_id with honest null_count stats |
| 02-null-stats-omitted.json | null_count_omitted on sensor_id with real null rows |
| 03-dictionary-page-order.json | dictionary page listed before null_bitmap |
| 04-timestamp-utc-bound.json | measured_at min/max with null_count_omitted |
| 05-parallel-chunk-split.json | chunk_size=2 parallel read with null rows on chunk edges |
| 06-merged.json | Combined pushdown traps across modules |

Hidden verifier catalogs are not shipped under /app/fixtures/.
