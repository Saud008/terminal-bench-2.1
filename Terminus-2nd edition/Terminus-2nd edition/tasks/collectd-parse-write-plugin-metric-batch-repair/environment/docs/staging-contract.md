# Collectd ingest staging contract

`collectdctl stage` and `collectdctl export` split metric normalization from JSON export using `/app/state/collectd-ingest.snapshot.json`.

## Snapshot envelope

Written on every successful `stage` (and on the stage phase of `ingest`):

| Field | Meaning |
|-------|---------|
| `report` | Full flush report before export serialization |
| `ingest_binding` | Fingerprint over the staged report payload |

## ingest_binding

Compute lowercase SHA-256 hex over UTF-8 `"\n".join(parts)` where `parts` are, in order:

1. `report.seed`
2. Each batch filename joined with `"\n"` (empty string when none)
3. `report.pipeline_version` as decimal string
4. `report.stats.lines`, `accepted`, `rejected` as decimal strings
5. For each flush in order: `flush_index`, `start_epoch`, `end_epoch` as decimal strings
6. Each metric in flush order as `json.Marshal` compact JSON (default key order)

Store the digest in `ingest_binding` on write. On `export`, recompute from the envelope and fail if it does not match.

## Export rules

- `export` reads **only** the staging snapshot — it must not re-run PUTVAL parsing or flush assignment.
- `pipeline.Export` must call `export.Write` with the verified staged envelope; see `/app/docs/pipeline-api-contract.md`.
- `ingest` performs stage then export in one process.
- Export must preserve staged flush and metric order verbatim when writing stdout JSON.
