# Normalize export sequence

Each normalize run for a given `--fixture` and `--seed` pair is numbered with a monotonic `export_seq` stored in the sealed ledger and a marker file under `/app/state/srtctl/<fixture>-<seed>/`.

## Marker file

- Path: `/app/state/srtctl/<fixture>-<seed>/export-seq.marker`
- Content: single decimal integer followed by newline (no JSON)
- Meaning: count of successful normalize exports completed for this fixture-seed pair

## Ledger field

`normalize-ledger.json` includes:

| Field | Type | Meaning |
|-------|------|---------|
| `export_seq` | u32 | `1` on the first successful normalize after reset; each later successful normalize for the same fixture-seed increments by `1` |

Stage 2 (`publish.rs`) must reject a ledger whose `export_seq` does not equal the next expected value derived from the marker file (treat a missing marker as `0`, so the first run expects `export_seq == 1`).

## Export bytes vs sequence

Repeat normalize with the same inputs must emit **identical** export JSON bytes even as `export_seq` increments. Sequence tracks completed exports; it must not change cue math or stats.

## Sealed snapshot digest

`normalize-ledger.json` field `snapshot_digest` must be the lowercase hex FNV-1a64 digest of the **raw bytes** of `normalize-snapshot.json` on disk after stage 1 writes it. Stage 2 must verify this digest before reading staged cues.
