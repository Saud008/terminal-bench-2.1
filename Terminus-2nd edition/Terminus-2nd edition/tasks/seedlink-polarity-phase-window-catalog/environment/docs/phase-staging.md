# Phase staging schema — numeric closure snapshot

Staging artifacts seal pick chronology before catalog export. Digest closure rules use reference math defined here and in `/app/docs/scientific-computing-workflow.md`.

Staging files are written to /app/state/phase-staging/<stem>.json.

## Fields

| Field | Type | Meaning |
|-------|------|---------|
| source | string | Absolute path to ingested SLWS |
| stem | string | Catalog stem |
| staging_version | u32 | Must equal STAGING_VERSION (1) |
| network | string | Network code |
| station | string | Station id |
| epoch_sec | u32 | Snippet epoch |
| leap_marker | u8 | Leap marker byte |
| sample_count | u16 | Sample count |
| rate_mhz | u32 | Rate millihertz |
| effective_polarity | i8 | Resolved polarity |
| picks | array | Pick rows sorted by sample_idx ascending |
| digest | string | 16-hex digest |

## Digest

Digest is computed over picks sorted by sample_idx (not file order). For each pick: xor sample_idx, multiply by 1099511628211, xor phase_code, multiply, xor effective_polarity byte, multiply. Initial accumulator 1469598103934665603. Format as 16 lowercase hex digits.

Export must load staging from disk and must not recompute picks by reparsing SLWS when staging already exists.

When staging on disk is edited between export invocations, export must read the current on-disk pick rows and digest values without reparsing the source SLWS file.

## Calibration kernel surface

Keep these laboratory kernel paths, names, and signatures under `/app/crates/slcore` (do not rename or relocate):

- `STAGING_VERSION: u32` in the staging module; must match the `staging_version` field written to phase-staging JSON.
- `PhaseStaging` public fields: `source`, `stem`, `staging_version`, `network`, `station`, `effective_polarity`, `picks` (sample_idx sort order for digest and export).
- `stage_snippet(source, stem)`, `build_phase_staging(source, stem)` (writes `/app/state/phase-staging/<stem>.json`), `export_from_staging(source, stem, msg_path)` (reads staging from disk; does not re-parse SLWS for pick rows), `export_catalog(source, stem)`, `build_export(staging, msg_path)`.
