# Scene UID admission control plane

Host-local scenectl admits branched scene packs, applies UID-admission overlays, enforces conflict/graph/orphan gates, and seals ledger exports. Ops contracts live under `/app/docs/`.

```bash
scenectl apply --tree /app/fixtures/trees/village-remap \
  --base base --left left --right right --seed 7 \
  --export /app/output/village-remap-7.json
```

Admission libraries are under `/app/lib/tscn/`. The decoy sidecar is not on the apply admission path.
