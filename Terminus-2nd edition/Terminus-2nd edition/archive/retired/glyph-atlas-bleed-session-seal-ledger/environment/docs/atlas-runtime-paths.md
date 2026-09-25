# Atlas runtime paths

| Path | Role |
|------|------|
| `/app/fixtures/catalog.json` | Admitted catalog policy and pack sets |
| `/app/fixtures/sprites/` | Admitted sprite sheet PNGs |
| `/app/fixtures/seeds.json` | Bundled seed roster for ops checks |
| `/app/output/` | Sealed atlas PNG and manifest JSON exports |
| `/usr/local/bin/atlaspack` | Installed control-plane binary |
| `/app/docs/` | Normative ops contracts (do not edit) |

Rebuild from `/app` with `cargo build --release --locked -p atlaspack`, then install the release binary to `/usr/local/bin/atlaspack`.
