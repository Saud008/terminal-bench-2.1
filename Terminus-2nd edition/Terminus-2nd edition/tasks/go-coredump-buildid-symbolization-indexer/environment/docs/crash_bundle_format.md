# Crash bundle format

Each file uses extension `.crash.jsonl`. One JSON object per line.

Required fields per crash record:

| Field | Type | Notes |
|-------|------|-------|
| crash_id | string | Stable identifier |
| timestamp | string | RFC3339 UTC |
| signal | int | Unix signal number |
| pid | int | Process id |
| threads | array | Each thread has name and frames |
| mmap | array | VMA entries with start, end, path, file_offset |

Each frame has `pc` as hex string with `0x` prefix and `module` basename.

Each mmap entry has `start` and `end` as hex strings, `path` absolute path to mapped file, and `file_offset` hex offset into the file.

## Bundled fixture identifiers

The verifier fixtures under `/app/fixtures/crashes/` include representative records such as:

| crash_id | Expected top symbol | Notes |
|----------|---------------------|-------|
| c-alpha-001 | main.worker | Stripped binary fallback via catalog |
| c-bravo-lib | helper.run | mmap tie-break inside libhelper |
| c-charlie-edge | main.crash | Half-open VMA boundary |
| c-hidden-delta | (TB3 bundle) | Hidden override via TB3_CRASH_DIR |

Catalog build IDs use uppercase hex without `0x`, for example `A1B2C3D4E5F60718` and `a1b2c3d4e5f60718` in source notes normalize to uppercase on export.
