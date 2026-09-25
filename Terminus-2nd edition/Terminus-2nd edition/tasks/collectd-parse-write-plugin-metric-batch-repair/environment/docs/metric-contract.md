# Metric ingest contract

Authoritative behavioral rules for `collectdctl ingest`, `collectdctl stage`, and `collectdctl export`. Export field names and types are in `export-schema.md`. Staging snapshot layout is in `staging-contract.md`.

## Config fields

- `types_db`: maps type name → data source name → kind (`gauge`, `derive`, `counter`, `absolute`)
- `epoch_origin`, `flush_interval_sec`, `time_skew_sec`
- `seed`, `batches`

## Export `value_kind` values

`gauge`, `derive_rate`, `counter_delta`, `absolute`

## Series key

`(canonical_identifier, ds_name)`

## Parsing

- Parse each non-empty, non-comment line as PUTVAL with optional `interval=` and **every** epoch:value group on the line (not just the first group).
- Canonical identifiers: unquoted paths pass through; quoted paths strip quotes and turn `\/` into `/`.
- Resolve the collectd type from the third slash-separated identifier component, before any `-` suffix (for example `alpha/df-root/df_complex` → `df_complex`).
- Map colon-separated values to data-source names in alphabetical order within the matching `types_db` entry. Assign each value kind from config and export as `gauge`, `derive_rate`, `counter_delta`, or `absolute`.

## Derive and counter normalization

For derive and counter series, use the last two accepted points per `(canonical_id, ds)`:

- derive rate is `(v2-v1)/(t2-t1)` with negative deltas wrapped by adding 2³² before dividing
- counter delta is `v2-v1`, or `2³²-v1+v2` when `v2 < v1`

## Flush assignment

- Drop readings with epoch below `epoch_origin`.
- For each accepted reading, compute window bounds from config:

  - `flush_index = floor((epoch - epoch_origin) / flush_interval_sec)`
  - `start_epoch = epoch_origin + flush_index * flush_interval_sec`
  - `end_epoch = start_epoch + flush_interval_sec`

- Assign the reading to that `flush_index`. Windows are half-open: `start_epoch <= epoch < end_epoch`. The exported `end_epoch` is always `start_epoch + flush_interval_sec` (not the last inclusive epoch in the window).

## Time skew

Within each batch file, use one anchor for the whole file — the epoch of the first accepted reading in file order. Later readings in that file are accepted only when `abs(epoch - anchor) <= time_skew_sec`; the anchor never moves. Rejected readings increment `stats.rejected` only (ingest still exits 0).

## Stats accounting

Increment `stats.accepted` and `stats.rejected` once per expanded data-source reading (each epoch:value group crossed with each mapped data-source name after type lookup). Count `stats.lines` as PUTVAL lines only (non-empty, non-comment).

Example: one PUTVAL line with two epoch groups and two mapped DS values yields `stats.lines` = 1 and `stats.accepted` = 4 when all four readings pass filters.

## Multi-batch ingest

When `--text` is omitted, `collectdctl ingest` reads `seed` and `batches` from config, selects a subset of batch files, permutes them deterministically, ingests them in that order, and lists the filenames in export `batches` in the same order.

Implement selection and permutation in `internal/config.SelectBatches(seed, batches)` using this algorithm:

1. Let `digest` be the 32-byte SHA-256 hash of `seed` encoded as UTF-8.
2. **Bitmask selection:** `bits = digest[0] | (digest[1] << 8)` (16-bit). Consider only the first `min(len(batches), 16)` entries of the config `batches` array in listed order. Include `batches[i]` when bit `i` of `bits` is set (`(bits >> i) & 1`).
3. **Fallback:** If the bitmask selects no files, include exactly one batch: `batches[digest[2] % len(batches)]`.
4. **Permutation:** Fisher–Yates shuffle the working set from the last index down to 1. For each `i` from `len-1` down to `1`, swap `out[i]` with `out[j]` where `j = digest[i % 32] % (i + 1)`.
5. Ingest batch files in the final permuted order without re-sorting filenames.

The same ordered list must appear in export `batches`.

## Export ordering

Sort flushes by `flush_index` ascending; within each flush sort metrics by `canonical_id`, then `ds`, then `epoch`.
