# Apply export schema

`sysctlmerge export` reads an ingest snapshot per `/app/docs/snapshot-schema.md`, validates the sibling merge-staging file per `/app/docs/merge-staging.md`, and writes the apply JSON below. `sysctlmerge apply` chains ingest then export.

Top-level fields (all required on success):

| Field | Meaning |
|-------|---------|
| `apply_version` | Schema version (`1`) |
| `tree` | Bundle directory name |
| `seed` | Seed string passed to `apply` |
| `processing_order` | Parsed file paths: `main` first, then drop-ins in merge order |
| `effective` | Final sysctl key → string value map |
| `sources` | Winning `file` and 1-based `line` per key |
| `stats` | `keys` (effective count) and `files_processed` (every parsed file including `main`) |
| `apply_digest` | Lowercase hex digest from `canonical_snapshot_digest` per `/app/docs/digest-contract.md` |

Each bundle tree includes `manifest.json` with `main` and `drop_ins`. Drop-in order comes from `drop_in_order` in `/app/docs/merge-contract.md`.

Illustrative successful export for `layered-precedence` / `base`:

```json
{
  "apply_version": 1,
  "tree": "layered-precedence",
  "seed": "base",
  "processing_order": ["sysctl.conf", "sysctl.d/99-override.conf"],
  "effective": {
    "net.ipv4.ip_forward": "1",
    "vm.swappiness": "30"
  },
  "sources": {
    "net.ipv4.ip_forward": {"file": "sysctl.d/99-override.conf", "line": 1},
    "vm.swappiness": {"file": "sysctl.conf", "line": 2}
  },
  "stats": {"keys": 2, "files_processed": 2},
  "apply_digest": "a1b2c3..."
}
```

`effective` maps sysctl keys to string values. `sources` records the winning file and 1-based line number per key. `processing_order` lists every parsed file path in merge order: `main` first, then drop-ins in `drop_in_order` per `merge-contract.md` (seed-keyed digest sort, not lexicographic).
