# Sheet runtime paths

| Path | Role |
|------|------|
| `/app/fixtures/catalog.json` | Admitted label catalog policy and impose sets |
| `/app/fixtures/marks/` | Admitted mark roster PNGs |
| `/app/fixtures/seeds.json` | Bundled seed roster for ops checks |
| `/app/output/` | Sealed sheet PNG and ledger JSON exports |
| `/app/bin/sheetd` | Installed control-plane CLI |
| `/app/lib/sheet/` | Admission library modules |
| `/app/docs/` | Normative ops contracts |

Rebuild from `/app` with `bash /app/scripts/rebuild-sheet.sh` (or `make rebuild-sheet`), which reinstalls `/app/bin/sheetd` from `/app/scripts/sheetd`.
