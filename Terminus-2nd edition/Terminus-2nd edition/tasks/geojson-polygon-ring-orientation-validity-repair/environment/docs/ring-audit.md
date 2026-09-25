# Ring audit helpers (legacy)

`/app/crates/geojson-core/src/ring_audit.rs` exposes perimeter and compactness metrics for ad-hoc diagnostics.

These helpers are **not** on the repair export hot path. `geojson-fix repair` does not call `ring_audit`; export and staging do not read compactness scores. Do not route repaired coordinates through this module.

Repair correctness is enforced by the verifier against bundled fixtures and the staged repair report output.
