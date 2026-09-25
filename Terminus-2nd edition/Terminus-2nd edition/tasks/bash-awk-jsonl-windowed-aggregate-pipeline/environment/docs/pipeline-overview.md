# Pipeline overview

`agg-run` is a three-stage pipeline:

1. `/app/lib/ingest.awk` scans `*.jsonl` under `--stream-dir`, applies dedup and validation, writes `/app/state/accepted.ndjson` and `/app/state/ingest-stats.json` (see `staging-schema.md`).
2. The wrapper computes `/app/state/ledger-manifest.json` from accepted staging (see `manifest-schema.md`).
3. `/app/lib/bucket.awk` reads accepted staging only, buckets in UTC, writes `/app/state/bucket-rollup.ndjson`.
4. `/app/lib/export.awk` validates the manifest, reads rollup lines and ingest stats, and writes `/app/output/aggregate-report.json`. The wrapper then updates `/app/state/run-seq.json`.

The wrapper loads `window_sec` from `/app/config/window.json`, exports `TZ=UTC` for all gawk stages, and computes an input fingerprint from sorted stream file paths and contents.

## Wrapper-to-stage gawk interface

`agg-run` owns path wiring. It invokes each stage with gawk `-v` variables using the exact names below. Stages must read and write through these variables (not alternate hard-coded paths), because the wrapper may keep calling stages with this contract while individual stage files are replaced.

### Stage 1 — `/app/lib/ingest.awk`

- Input files: discovered `*.jsonl` paths as gawk ARGV.
- `-v accepted_path=<path>` — append accepted staging rows (`/app/state/accepted.ndjson`).
- `-v stats_path=<path>` — write ingest counters (`/app/state/ingest-stats.json`).

### Stage 2 — `/app/lib/bucket.awk`

- Input file: accepted staging path as gawk ARGV.
- `-v window_sec=<int>` — UTC tumbling window width in seconds.
- `-v rollup_path=<path>` — write rollup lines (`/app/state/bucket-rollup.ndjson`).

### Stage 3 — `/app/lib/export.awk`

- Input file: rollup path as gawk ARGV.
- `-v window_sec=<int>` — echoed into the report.
- `-v output=<path>` — write `/app/output/aggregate-report.json`.
- `-v stats_path=<path>` — read ingest counters for report `stats` / footer sum.
- `-v manifest_path=<path>` — read `/app/state/ledger-manifest.json` before publish.
- `-v accepted_path=<path>` — re-hash on-disk accepted staging for digest binding.
- `-v run_seq=<int>` — footer `run_seq` value chosen by the wrapper.

The wrapper (not an awk stage) writes `ledger-manifest.json` after ingest and maintains `run-seq.json` after a successful export.

## Run sequence persistence

`/app/state/run-seq.json`:

```json
{"seq": 1, "input_fingerprint": "hex sha256"}
```

The input fingerprint is a content-sensitive digest over the sorted `*.jsonl` paths under `--stream-dir` **and** each file's bytes. Changing bytes at an unchanged path must change the fingerprint (path-only hashing is not sufficient). When the fingerprint matches the stored value, `seq` stays unchanged on success. When the fingerprint changes, `seq` increments by one. The export footer `run_seq` field mirrors the stored `seq` after a successful run.

Each run replaces prior staging, rollup, manifest, and report files except `run-seq.json`, which persists until reset.

Legacy modules `/app/lib/window_legacy.awk` and `/app/lib/prefilter.awk` are not invoked.
