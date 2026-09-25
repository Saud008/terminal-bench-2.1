# Lap staging contract

Staging path: `/app/state/lap-staging/<stem>.json`

Public API in `fitcore`:

- `pub const STAGING_VERSION: u32`
- `pub struct LapStaging { source, stem, staging_version, laps, digest }`
- `pub fn stage_laps(source: &Path, stem: &str) -> Result<LapStaging, FitError>`
- `pub fn build_lap_staging(source: &Path, stem: &str) -> Result<LapStaging, FitError>`
- `pub fn export_from_staging(source: &str, stem: &str) -> Result<ExportReport, FitError>`
- `pub fn export_laps(source: &Path, stem: &str) -> Result<ExportReport, FitError>`
- `pub fn build_export(staging: &LapStaging) -> Result<ExportReport, FitError>`

`STAGING_VERSION` must equal `LapStaging.staging_version`.

`LapStaging` fields:

- `source`: absolute path to the source FIT-like file
- `stem`: output stem for staging/export files
- `staging_version`: `u32`
- `laps`: start-time sorted rows
- `digest`: digest computed over start-time ordered rows

Staging JSON schema:

```json
{
  "source": "/app/fixtures/fit/recovery.fit",
  "stem": "recovery",
  "staging_version": 1,
  "laps": [
    {
      "original_index": 0,
      "start_time": 3600,
      "end_time": 3660,
      "distance_m": 1000,
      "trigger": "time",
      "developer_note": "warmup"
    }
  ],
  "digest": "hex-string"
}
```
