# Fixture chart catalog

Charts under /app/fixtures/charts/ supply bundled arcade charts with randomized ppq drift on arcade-04. Hidden overlays under /opt/verifier-fixtures/midgrid/charts/ supply alternate charts for verifier probes. When TB3_CHART_DIR is set in the environment, midgrid resolves bundled chart paths from that directory instead of /app/fixtures/charts/. Values derive from seed 8823 at image build time.

## CLI flags

load-chart: --run-id, --chart (path to chart JSON)

stage-tempo: --run-id

build-grid: --run-id, --quant (optional override; TB3_QUANT_DIVISOR env wins when set)

quantize-notes: --run-id

emit-audit: --run-id, --output (path ending with -beat-grid-audit.json)

## Release build

Playtest binary path: /app/bin/midgrid (release artifact from the /app Cargo workspace).
