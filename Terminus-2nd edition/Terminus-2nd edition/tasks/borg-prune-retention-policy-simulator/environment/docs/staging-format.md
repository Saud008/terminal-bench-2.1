# borg.stage.json staging snapshot

Written beside the list file as dirname(list)/borg.stage.json — not a global /app/state path.

After ingest:

```json
{
  "archives": [],
  "repo_id": "main"
}
```

Each archive entry:

```json
{"bytes": 0, "line": 1, "name": "host-2024-06-01", "segments": 3, "ts": "2024-06-01T12:00:00Z"}
```

After evaluate, an evaluation object is added:

```json
{
  "evaluation": {
    "bucket_hits": {"daily": [], "monthly": [], "weekly": [], "yearly": []},
    "clock_skew_adjusted": [],
    "kept": [],
    "legal_hold_kept": [],
    "pruned": []
  }
}
```

Keys are sorted. Trailing newline required. Export requires evaluation present.
