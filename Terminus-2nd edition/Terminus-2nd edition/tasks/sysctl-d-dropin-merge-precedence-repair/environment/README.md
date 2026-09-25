# sysctlmerge

Merge sysctl.conf with sysctl.d drop-ins. Read `/usr/local/bin/sysctlmerge` and `/app/docs/merge-contract.md` (library entrypoints) before editing `/app/lib/`.

```bash
sysctlmerge apply --tree /app/fixtures/bundles/<name> --seed <seed> --output /app/output/out.json
```

Contracts: `merge-contract.md`, `sysctl-format.md`, `export-schema.md`.
