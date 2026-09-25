# walplan CLI

Binary: /app/bin/walplan

## ingest

```bash
walplan ingest --archive <dir> --staging /app/state/wal-archive.stage
```

Writes staging JSON only. Parses backup_label, timeline history files, complete WAL segments, and partial filenames.

## plan

```bash
walplan plan --staging /app/state/wal-archive.stage --out /app/output/plan.json --restore-target "2024-06-15 14:34:00 UTC"
```

## export

```bash
walplan export --staging /app/state/wal-archive.stage --out /app/output/plan.json --restore-target "2024-06-15 14:34:00 UTC"
```

Alias for plan. Reads staging snapshot only for segment lists and digest. Selects restore segment from staging segments_present and segment-clock.json.

Optional `--config-root` or environment variable TB3_CLOCK_ROOT overrides /app/config for segment-clock.json.

## scan

```bash
walplan scan --archive <dir>
```

Decode-only continuity scan. Exit 0 when no gaps, exit 2 when gaps detected.
