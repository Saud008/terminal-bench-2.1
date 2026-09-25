# Staging snapshot

Path default: /app/state/rule_staging.json

## Schema

```
{
  "schema_version": 1,
  "rules": [ { rule_id, priority, source_file, line_number, tokens... } ],
  "devices": [ input devices unchanged ],
  "match_edges": [ { "dev_id", "rule_ids": [] } ],
  "staging_digest": "64 lowercase hex"
}
```

rules array must follow effective order (ascending sort key).

## staging_digest

SHA-256 hex of a canonical string built as follows:

1. For each rule in effective order, append rule_id, priority, and sorted token key=value pairs joined with semicolons, one rule per line.
2. For each device sorted by dev_id, append dev_id and sorted inherited attrs as key=value pairs.
3. For each match_edges entry sorted by dev_id, append dev_id and comma-joined rule_ids.

Join all lines with newline. Hash with sha256sum and take the hex digest.

## replay.seq

Plain integer file at /app/state/replay.seq. Ingest increments by 1 when staging_digest differs from the digest in the previous staging file on disk (if any). When digest is unchanged, replay.seq and staging bytes must remain identical.
