Implement the fitlap activity FIT lap boundary decoder and two-stage export pipeline on the working Rust baseline under /app. The fitlap CLI at /app/crates/fitlap reads activity FIT streams from /app/fixtures/fit and writes lap boundary JSON. The fitcore library at /app/crates/fitcore must provide ingest, staging, and export stages: stage 1 writes /app/state/lap-staging/<stem>.json, stage 2 emits export JSON from that staging file only.

Build fitlap from /app with cargo build --release --bin fitlap after Rust changes (Rust is on PATH via /usr/local/cargo/bin). Subcommands and flags are defined in /app/docs/cli-reference.md. FIT message layout, lap start_time endianness, alignment rules, trigger classification, and developer string resolution are defined in /app/docs/fit-lap-contract.md. Staging snapshot schema, digest rules, and export JSON shape are defined in /app/docs/lap-staging.md and /app/docs/export-guard.md. Bundled and catalog fixtures are listed in /app/docs/fixture-catalog.md.

Your implementation must satisfy every contract above. The decoy module at /app/crates/fitcore/src/decoy/legacy_merge.rs is not on the export hot path and must not be edited for a correct export. merge.rs is a legacy helper and is not authoritative for export.

fitlap decode must validate message-stream CRC and apply decode-only lap/record alignment rejection before lap parsing. fitlap laps --export must write staging then export JSON matching the schemas without applying the decode alignment rejection path. Lap start_time is little-endian per fit-lap-contract.md and is read through /app/crates/fitcore/src/lap_time.rs (read_lap_start_time). Export must read the on-disk staging snapshot only and must not re-parse the FIT file when staging already holds lap rows. Staging digest must be computed over start_time-ordered lap rows. Developer UTF-8 notes must bind to original lap index, not sorted row position.

Public fitcore API surface (keep these module paths, names, and signatures; do not rename or relocate):

  STAGING_VERSION: u32 constant in the staging module; must match the staging_version field written to lap-staging JSON.

  struct LapStaging in the staging module with at least these public fields:
    source: String — absolute path to the FIT file ingested for this staging snapshot
    stem: String — fixture stem used for /app/state/lap-staging/<stem>.json and export output naming
    staging_version: u32 — equals STAGING_VERSION
    laps: Vec<LapRow> — lap rows in start_time sort order for digest and export

  stage_laps(source: &Path, stem: &str) -> Result<LapStaging, FitError>
  build_lap_staging(source: &Path, stem: &str) -> Result<LapStaging, FitError> — writes /app/state/lap-staging/<stem>.json and returns the in-memory snapshot
  export_from_staging(source: &str, stem: &str) -> Result<ExportReport, FitError> — reads staging from disk for source/stem; does not re-parse the FIT file
  export_laps(source: &Path, stem: &str) -> Result<ExportReport, FitError> — orchestrates staging then export
  build_export(staging: &LapStaging) -> Result<ExportReport, FitError> — builds export JSON from an in-memory staging snapshot

Field-level staging and export JSON schemas remain authoritative in /app/docs/lap-staging.md and /app/docs/export-guard.md. Hidden verifier fixtures may supply additional FIT streams under /opt/verifier-fixtures/fit and alternate fitcore module trees under /opt/verifier-broken-fit for partial-path traps.

Do not edit /app/docs/, /app/fixtures/, or /tests/.
