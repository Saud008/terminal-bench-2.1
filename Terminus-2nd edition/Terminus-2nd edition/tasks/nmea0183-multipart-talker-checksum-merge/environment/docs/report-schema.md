# Report schema (`/app/output/merge-report.json`)

```json
{
  "groups": [
    {
      "merge_key": "GN:GSV:2",
      "talker": "GN",
      "sentence": "GSV",
      "multipart_total": 2,
      "fragments_merged": 2,
      "payload_fields": ["..."],
      "utc_iso": "2024-01-01T00:00:01Z"
    }
  ],
  "rejected": [{"line": "...", "reason": "checksum"}],
  "snapshot_digest": "<sha256 hex>"
}
```

Groups appear in first-seen stream order of their merge keys. `utc_iso` may be `null` when no RMC context applies.
