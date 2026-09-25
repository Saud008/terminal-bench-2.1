# Submission explanations — sqlite-rtree-bbox-spatial-repair

**Task folder:** tasks/sqlite-rtree-bbox-spatial-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a two-stage stationclos control-network workflow where materialize-hulls fuses datum residual subtraction, meridian wrap partition, microdegree quantization, and positive-area conflict rejection into one hull ledger, then certify-campaign ranks rows from that ledger alone. Six interacting defects span residual sign, quantization mode, wrap threshold, degenerate conflict gating, area-first rank order, and digest field layout. Fixing one module leaves partial certificates that pass some bundled cases but fail hidden verifier fixture traps or cross-run generation checks.

## Solution Explanation

The oracle copies six corrected modules under datum_delta, grid_trunc, meridian_split, hull_reject, atlas_order, and seal_digest, then rebuilds stationclos. Residuals subtract datum_offset, quantization truncates toward zero, wrap splits at longitude delta greater than 180, conflicts require positive area on both hulls, rows sort by ascending residual_area_u64, and closure_digest hashes ranked station_id|area|vertex_count lines. certify-campaign reads only the ledger path documented in station-hull-certificate.md.

## Verification Explanation

Pytest rebuilds stationclos from live sources, invokes materialize-hulls and certify-campaign through subprocess on every test, and compares certificate JSON to an independent Python reference in reference_stationclos.py. Bundled campaign bundles exercise conflict, wrap, and rank-ladder cases while hidden bundles under verifier fixture directories probe dateline wrap and live microdegree-scale environment overrides. Cross-run tests assert materialize_generation persistence and ledger-only certify after fixtures are moved aside.
