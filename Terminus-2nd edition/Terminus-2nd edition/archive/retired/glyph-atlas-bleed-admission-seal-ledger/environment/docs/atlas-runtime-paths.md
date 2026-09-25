# Atlas runtime paths

| Path | Role |
|------|------|
| `/app/fixtures/catalog.json` | Admitted catalog policy and pack sets |
| `/app/fixtures/sprites/` | Admitted sprite sheet PNGs |
| `/app/fixtures/seeds.json` | Bundled seed roster for ops checks |
| `/app/output/` | Sealed atlas PNG and manifest JSON exports |
| `/app/bin/atlasd` | Installed control-plane CLI |
| `/app/lib/atlas/` | Admission library modules |
| `/app/docs/` | Normative ops contracts |

Rebuild from `/app` with `bash /app/scripts/rebuild-atlas.sh` (or `make rebuild-atlas`), which reinstalls `/app/bin/atlasd` from `/app/scripts/atlasd`.
