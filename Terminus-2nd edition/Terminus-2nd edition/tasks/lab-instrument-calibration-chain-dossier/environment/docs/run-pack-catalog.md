# Run pack catalog

Bundled calibration run packs live under /app/fixtures/cal_runs/ as JSON files.

| Pack name | Behavior exercised |
|-----------|-------------------|
| dual-channel-basic | Two channels within asymmetric tolerance, valid cert, complete standard chain |
| cert-expired-edge | Certificate expires on as_of_date boundary |
| asymmetric-oot | One channel fails upper tolerance only |
| trace-chain-deep | Three-link standard chain root resolution |
| tech-scope-miss | Technician qualified but missing instrument scope |
| rss-budget | Multiple uncertainty components requiring RSS |
| severity-ladder | Mixed cert, tech, and tolerance failures for dossier ranking |
| generation-advance | Used to test chain_generation increment across re-ingest |

Runtime overlays under TB3_FIXTURE_DIR follow the same JSON schema.
