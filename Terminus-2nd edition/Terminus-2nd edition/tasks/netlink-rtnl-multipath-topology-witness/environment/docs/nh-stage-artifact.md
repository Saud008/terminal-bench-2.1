# NH snapshot artifact (stage 2a)

After stage 1 bind writes a JSON file under /app/state/bind-snapshots named dump-filename-pid.json, stage 2a (export_nh.rs) reads that bind snapshot, normalizes nexthops per /app/docs/export-digest-schema.md, and writes a matching JSON file under /app/state/nh-snapshots using the same dump-filename-pid basename.

dump-filename is the dump path final component (including .bin). pid is the process id of the decode invocation.

Example: for --dump /app/fixtures/dumps/001-multipath-v4.bin the NH snapshot basename is 001-multipath-v4.bin-PID.json inside the nh-snapshots directory.

## Snapshot schema (version 1)

```json
{
  "version": 1,
  "seed": "nl-seed-6",
  "source_dump": "/app/fixtures/dumps/001-multipath-v4.bin",
  "bind_snapshot": "absolute path of the bind snapshot this stage read",
  "snapshot_routes": [ ... ],
  "routes": [ ... ]
}
```

| Field | Meaning |
|-------|---------|
| `version` | Always `1` |
| `seed` | Copied from bind snapshot |
| `source_dump` | Absolute `--dump` path from bind snapshot |
| `bind_snapshot` | Absolute path to the bind snapshot file this stage read |
| `snapshot_routes` | Copy of bind `routes` before stage 2a nexthop normalization (used for `export_digest` fingerprint) |
| `routes` | Export-ready route rows after stage 2a nexthop normalization |

Stage 2b (`export.rs`) must read the NH snapshot only. It must not re-open the dump, re-run bind, or re-read the bind snapshot for route assembly. Digest assembly uses fields from the NH snapshot per `/app/docs/export-digest-schema.md`.
