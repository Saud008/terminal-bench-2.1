# Parse ledger staging

`kh-normalize` uses a **two-stage** pipeline:

1. **Ingest** — parse each input line → append to `/app/state/kh-ledger.jsonl`
2. **Export** — verify sealed manifest → merge ledger records → write normalized output

## Ledger file (`kh-ledger.jsonl`)

UTF-8 JSON Lines. One object per successfully parsed record, in ingest order:

```json
{"seq": 1, "record": "<internal record string>"}
```

`seq` starts at `1` and increments by `1` for each appended record.

## Manifest (`kh-manifest.json`)

Written after ingest completes, **before** merge/export:

```json
{
  "input_sha256": "<SHA-256 hex of raw input file bytes>",
  "record_count": <number of ledger lines>,
  "ledger_sha256": "<SHA-256 hex of kh-ledger.jsonl file bytes>"
}
```

`kh-normalize` must call ledger verification after sealing. Export proceeds only when:

- `record_count` equals the number of lines in `kh-ledger.jsonl`
- `ledger_sha256` matches the current ledger file digest
- `input_sha256` matches the `--input` file bytes read during this run

A new run clears prior ledger state under `/app/state/` before ingest.
