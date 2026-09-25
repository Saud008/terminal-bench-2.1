# atlaspack

CLI sprite atlas packer for 2D glyph sheets. Contracts live in `/app/docs/`.

```bash
atlaspack pack --catalog /app/fixtures/catalog.json --sprites /app/fixtures/sprites \
  --set core-glyphs --seed 7 --atlas-out /app/output/atlas.png --manifest-out /app/output/manifest.json

atlaspack probe --atlas /app/output/atlas.png --manifest /app/output/manifest.json \
  --glyph arrow --frame 0 --u 0.0 --v 0.0
```

Rebuild after source edits:

```bash
cargo build --release --locked -p atlaspack
install -m 0755 /app/target/release/atlaspack /usr/local/bin/atlaspack
```
