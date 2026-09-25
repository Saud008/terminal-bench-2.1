# Normalize snapshot contract

Temporal closure stage boundaries for host-local caption normalize ops. Reference gates and tolerance rules: `/app/docs/srtctl-ops-workflow.md`.

`srtctl normalize` is a **two-stage** pipeline. Stage boundaries are mandatory — export must not rebuild cues from the source SRT on disk.

## Stage graph

| Stage | Steps | Responsibility |
|-------|-------|----------------|
| **Stage 1** | parse → seed offset → overlap resolve → ruby shifts → write snapshot → write ledger | ingest and persist staged cues |
| **Stage 2** | validate ledger → read snapshot cues → roll-up export | publish staged state only |

Stage 1 order is fixed: overlap resolution runs **before** ruby shifts so ruby segment caps use overlap-trimmed cue ends. Export JSON shape and roll-up rules: `/app/docs/normalize-contract.md`.

## Snapshot and ledger artifacts

Stage 1 writes:

- `/app/state/srtctl/<fixture>-<seed>/normalize-snapshot.json`
- `/app/state/srtctl/<fixture>-<seed>/normalize-ledger.json`

Cross-run `export_seq` rules: `/app/docs/normalize-export-seq.md`.

## `normalize-snapshot.json` schema (version 1)

| Field | Type | Meaning |
|-------|------|---------|
| `version` | u32 | always `1` |
| `fixture` | string | `--fixture` argument |
| `seed` | string | `--seed` argument |
| `input_path` | string | absolute path to the source SRT read in stage 1 |
| `input_digest` | string | lowercase hex FNV-1a64 over raw fixture bytes |
| `seed_offset_ms` | u32 | computed per `/app/docs/normalize-contract.md` |
| `parsed_count` | u32 | cues read from the file after parse |
| `overlap_trims` | u32 | overlap end-time trims applied in stage 1 |
| `ruby_shifts` | u32 | ruby segment end extensions applied in stage 1 |
| `cues` | array | post-ruby cue rows (pre roll-up); each object has `source_index`, `start_ms`, `end_ms`, `text`, `ruby_segments`, `rolled_up` |

Snapshot `cues` are **post-ruby** and **pre-roll-up**.

## `normalize-ledger.json` schema (version 1)

| Field | Type | Meaning |
|-------|------|---------|
| `version` | u32 | always `1` |
| `fixture` | string | must match the snapshot `fixture` |
| `seed` | string | must match the snapshot `seed` |
| `input_digest` | string | must match the snapshot `input_digest` |
| `snapshot_digest` | string | lowercase hex FNV-1a64 over the snapshot file body bytes |
| `export_seq` | u32 | per `/app/docs/normalize-export-seq.md` |

## Coupled fixture behaviors

| Surface | Bundled example | Coupled seed | Gap |
|---------|-----------------|--------------|-----|
| Overlap + ruby in one file | `overlap-merge`, `ruby-an8` (separate) | `srt-combo-07` | Stage-1 must trim overlaps **before** ruby caps segment ends; snapshot must record both counters |
| Roll-up + ruby preservation | `rollup-chain`, `ruby-an8` (separate) | `srt-rollup-ruby-23` | Roll-up space join must retain ruby segments on the merged export row |
| Staged export path | snapshot artifacts | coupled seeds above | Export must consume staged snapshot cues, not re-read the source SRT |

Coupled seeds are listed in `/app/docs/fixture-catalog.md`.
