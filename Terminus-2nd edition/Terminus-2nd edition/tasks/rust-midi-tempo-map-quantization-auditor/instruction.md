Rhythm chart playfield puzzle

Build the rhythm chart playfield puzzle, an offline arcade chart playtest planner for MIDI-like tempo-map beat-grid simulation on the working baseline under /app. The planner loads arcade chart fixtures, materializes tempo maps and meter timelines on disk, converts ticks to wall-clock seconds, snaps note lanes to beat subdivisions, rejects overlapping notes on the same lane, and seals a beat-grid playtest audit when the chart consistency win condition is met.

midgrid is available at /app/bin/midgrid. Subcommands and flags are cataloged in /app/docs/fixture-chart-catalog.md:

  load-chart
  stage-tempo
  build-grid
  quantize-notes
  emit-audit

Chart JSON grammar, field normalization, and chart_id casing follow /app/docs/chart-json-grammar.md. Tempo event sequence and microseconds-per-quarter semantics follow /app/docs/tempo-map-sequence.md. Tick to second conversion across tempo boundaries follows /app/docs/tick-clock-conversion.md. Active meter selection and ticks-per-beat math follow /app/docs/meter-timeline-contract.md. Quantization windows, nearest-grid snapping, and divisor overrides follow /app/docs/quantize-window-policy.md. Same-lane overlap rejection and lexicographic tie breaks follow /app/docs/overlap-rejection-policy.md. Stored chart JSON field names and manifest_revision persistence appear in /app/docs/chart-manifest-schema.md. Tempo ledger JSONL headers and tempo rows appear in /app/docs/tempo-ledger-schema.md. Beat grid ledger rows and note ledger rows appear in /app/docs/beat-grid-ledger-schema.md and /app/docs/lane-note-ledger-schema.md. Beat-grid playtest audit field sequence, grid_consistency_score rules, and audit_digest rules appear in /app/docs/beat-grid-audit-fields.md.

load-chart reads the chart path, normalizes identifiers, and writes /app/state/chart-manifest/<run-id>.json.

stage-tempo reads chart ledger for the run id, orders tempo events, and writes /app/work/tempo-ledger/<run-id>.jsonl with a header line followed by tempo rows.

build-grid reads chart and tempo ledger, applies meter timelines, converts tick markers to seconds, and writes /app/work/beat-grid-ledger/<run-id>.jsonl.

quantize-notes reads chart ledger and grid ledger, snaps note ticks to the active quantization grid, flags overlaps on the same lane, and writes /app/work/lane-note-ledger/<run-id>.jsonl.

emit-audit seals the beat-grid playtest audit JSON per /app/docs/beat-grid-audit-fields.md. The output file name ends with -beat-grid-audit.json.

Bundled arcade charts live under /app/fixtures/charts/. The bundled inventory and behaviors each chart exercises appear in /app/docs/fixture-chart-catalog.md. Chart overlays honor TB3_CHART_DIR when that environment variable is present. Quant divisor overrides honor TB3_QUANT_DIVISOR per /app/docs/fixture-chart-catalog.md and /app/docs/quantize-window-policy.md.

The harmony decoy module stays outside the load-chart, stage-tempo, build-grid, quantize-notes, and emit-audit playtest path. Beat-grid audit digest rules live only in /app/docs/beat-grid-audit-fields.md together with /app/scripts/audit_digest_ref.py for verifier reference checks.
