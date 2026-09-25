# atlasd / atlaspack

Host-local glyph atlas bleed session control plane. Ops contracts live in `/app/docs/`.

```bash
atlaspack pack --catalog /app/fixtures/catalog.json --sprites /app/fixtures/sprites \
  --set core-glyphs --seed 7 --atlas-out /app/output/atlas.png --manifest-out /app/output/manifest.json

atlaspack probe --atlas /app/output/atlas.png --manifest /app/output/manifest.json \
  --glyph arrow --frame 0 --u 0.0 --v 0.0
```

Release binary path: `/usr/local/bin/atlaspack` after `cargo build --release --locked -p atlaspack` from `/app`.
