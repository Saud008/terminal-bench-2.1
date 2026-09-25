The `geojson-fix` CLI under `/app/crates/geojson-fix` reads polygon and multipolygon fixtures from `/app/fixtures/geojson/` and writes a repair report to `/app/output/repair-report.json`. The library is supposed to sanitize rings, normalize closure, assign correct exterior and hole nesting, enforce winding, handle multipolygon members, and publish results through a staged snapshot — but several modules under `/app/crates/geojson-core/src/` do not agree with what the verifier expects today.

Repair the Rust sources so this command succeeds for every bundled fixture and produces `"valid": true` geometries with a consistent report:

```text
geojson-fix repair --input /app/fixtures/geojson --output /app/output/repair-report.json
```

Fixture intent is summarized in `/app/docs/fixture-catalog.md`. `/app/crates/geojson-core/src/ring_audit.rs` is diagnostic-only and not on the repair export path (`/app/docs/ring-audit.md`). Rebuild with `cargo build --locked --release -p geojson-fix` after changes. Do not change the public function signatures of `area.rs`, `close.rs`, `sanitize.rs`, `orient.rs`, `nest.rs`, `multi.rs`, `export.rs`, or `staging.rs`. Do not edit `/app/docs/`, `/app/fixtures/geojson/`, or `/tests/`.
