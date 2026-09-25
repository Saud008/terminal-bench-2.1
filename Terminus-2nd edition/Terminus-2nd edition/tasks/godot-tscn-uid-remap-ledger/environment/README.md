# Village scene-pack playfield puzzle

Offline packed-scene playtest planner for branched village scene packs. Playtest contracts live under `/app/docs/`.

```bash
sceneplay apply --tree /app/fixtures/trees/village-remap \
  --base base --left left --right right --seed 7 \
  --export /app/output/village-remap-7.json
```

Playtest libraries are under `/app/lib/tscn/`. The decoy sidecar is not on the apply playtest path.
