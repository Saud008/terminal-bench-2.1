# tscn-merge

Godot 4 `.tscn` UID remap and three-way merge helper. Contracts live in `/app/docs/`.

```bash
tscn-merge apply --tree /app/fixtures/trees/village-remap \
  --base base --left left --right right --seed 7 \
  --export /app/output/village-remap-7.json
```

Libraries are under `/app/lib/tscn/`. Run `/app/scripts/reset-state.sh` before local checks.
