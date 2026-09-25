# atlasd glyph atlas bleed admission control plane

Host-local atlasd admits catalog pack sets, applies pad-bleed / UV / rotation / scale gates, and seals atlas PNG plus checksum manifest exports. Ops contracts live under `/app/docs/`.

```bash
atlasd pack --catalog /app/fixtures/catalog.json --sprites /app/fixtures/sprites \
  --set core-glyphs --seed 7 --atlas-out /app/output/atlas.png --manifest-out /app/output/manifest.json

atlasd probe --atlas /app/output/atlas.png --manifest /app/output/manifest.json \
  --glyph arrow --frame 0 --u 0.0 --v 0.0
```

CLI path: `/app/bin/atlasd` after `bash /app/scripts/rebuild-atlas.sh` from `/app`.
