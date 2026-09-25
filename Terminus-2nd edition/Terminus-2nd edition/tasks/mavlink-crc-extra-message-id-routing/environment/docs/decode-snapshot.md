# Decode snapshot contract

After session filtering, dedup, and checkpoint merge, `mavctl decode` persists the accepted frame list before export.

## Path

Fixed path: `/app/state/decode.snapshot.json` (overwrite on every decode run).

## Pipeline flow

1. Ingest stream bytes, extract, permute, validate, session-filter, and dedup frames.
2. Merge checkpoint rows (resume) with newly accepted rows in checkpoint-first order.
3. Write the merged frame list and run counters to `/app/state/decode.snapshot.json`.
4. Publish reads the snapshot only — it must not re-parse input bytes or re-run session/dedup logic.

## Schema

```json
{
  "version": 1,
  "seed": "alpha01",
  "checkpoint_frame_count": 0,
  "deduped_count": 0,
  "stale_seq_dropped": 0,
  "changed_fact_count": 0,
  "diff_rows": [],
  "frames": [
    {
      "msg_id": 24,
      "name": "GPS_RAW_INT",
      "sysid": 1,
      "compid": 1,
      "seq": 10,
      "payload": [0, 1, 2, 255]
    }
  ]
}
```

- `frames`: merged accepted frames in checkpoint-first order before route/event decoding.
- `payload`: JSON array of integers from 0 through 255 (one entry per raw payload byte). Do not store hex strings or base64.
- Counter fields mirror export metadata (`/app/docs/export-schema.md`).
- `diff_rows` and `changed_fact_count` mirror export resume fact diffs.

Missing snapshot or publish invoked without a prior decode snapshot must fail with non-zero exit. Export must preserve frame-list order from the snapshot when building `gps_fixes` and route counts.

Implementation lives in `/app/crates/mav-core/src/snapshot.rs` and `/app/crates/mav-core/src/publish.rs`.

## CLI

```
mavctl publish --export PATH
```

Reads `/app/state/decode.snapshot.json` and writes export JSON. Used after decode for snapshot-bound export; must not re-decode streams.
