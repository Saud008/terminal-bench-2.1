Export schema

Report path defaults to /app/output/rekey-report.json. Export reads /app/state/rekey.manifest only (export_source staging_manifest). Fields mirror the snapshot verdict list plus report_version 1. active_spi_out must equal the snapshot active_spi_out (active non-deleted child). rekey_violation_count must match snapshot. Export must not re-parse JSONL traces or re-run replay.
