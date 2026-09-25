# Staging ledger

irfs-stage uses ingest then export:

1. Ingest scans the rootfs, resolves hooks, modules, and firmware, appending rows to /app/state/irfs-ledger.jsonl
2. Export seals /app/state/irfs-manifest.json, verifies the seal, then writes the sorted manifest

## Ledger file (irfs-ledger.jsonl)

UTF-8 JSON Lines in ingest order:

```json
{"seq": 1, "kind": "hook", "name": "base", "path": "hooks/10-base.sh", "hook_rank": 1}
```

seq starts at 1 and increments by one per appended row.

## Manifest seal (irfs-manifest.json)

Written after ingest completes, before export emission:

```json
{
  "rootfs_sha256": "<SHA-256 digest of sorted rootfs file walk>",
  "entry_count": <ledger line count>,
  "ledger_sha256": "<SHA-256 hex of irfs-ledger.jsonl bytes>",
  "hook_order": ["base", "udev", "modules", "firmware"]
}
```

rootfs_sha256 is computed by walking every regular file under the rootfs in LC_ALL=C sorted relative path order, hashing each relative path UTF-8 bytes followed by raw file bytes into one SHA-256 digest.

Verification must fail export when counts, ledger digest, or rootfs digest mismatch the current run.
