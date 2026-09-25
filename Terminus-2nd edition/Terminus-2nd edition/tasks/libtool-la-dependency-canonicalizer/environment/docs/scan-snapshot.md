# Scan snapshot staging

`lt-canonicalize` is a **two-stage** pipeline:

1. **Scan** — walk `.la` files, break cycles, write `/app/state/lt-scan-snapshot.json`
2. **Publish** — read the snapshot only and emit `/app/output/libtool-manifest.json`

```text
lt-canonicalize <project-root> --out <manifest.json>
lt-canonicalize scan <project-root>
lt-canonicalize publish --out <manifest.json>
```

The full command runs scan then publish. **Publish must not re-walk `.la` files** on disk; it derives all library rows from the staged snapshot.

## Snapshot path

`/app/state/lt-scan-snapshot.json`

## Snapshot JSON

| Field | Meaning |
|-------|---------|
| `snapshot_version` | Schema version (`1`) |
| `scan_seq` | Monotonic counter starting at **1**, incremented on each successful scan |
| `snapshot_fingerprint` | SHA-256 digest of canonicalized library direct_deps plus broken edges (see `/app/docs/snapshot-validate.md`) |
| `project_root` | Absolute project directory |
| `libraries` | Parsed `.la` metadata: `id`, `la_relpath`, `fields`, `direct_deps` (in-project `lib*` ids only) |
| `broken_edges` | Cycle edges removed during scan |

Direct dependency ids in the snapshot use the **`lib` prefix** form (`libcore`, not `core`) matching manifest `dependency_order` entries.

See `/app/docs/manifest-schema.md` for the exported manifest shape.
