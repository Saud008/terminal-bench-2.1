# Platform rubric — rust-midi-tempo-map-quantization-auditor

**Task folder:** tasks/rust-midi-tempo-map-quantization-auditor/

Agent lowercases chart_id on load-chart per chart JSON grammar, 3
Agent orders tempo ledger rows by ascending tick not microseconds_per_quarter, 3
Agent accumulates tick_to_seconds across tempo map segment boundaries, 3
Agent computes ticks_per_beat as ppq times four divided by active denominator, 3
Agent snaps note ticks to nearest quantization grid multiple, 3
Agent rejects same-lane notes whose tick intervals overlap, 3
Agent excludes rejected overlap notes from grid_consistency_score, 2
Agent exports beat-grid audit with audit_digest over sorted source_ids, 2
Agent increments manifest_revision on repeated load-chart for same run id, 2
Agent rebuilds midgrid in test.sh before pytest subprocess verification, 2
Agent uses TB3_CHART_DIR overlay roots for hidden chart bundles, 2
Agent honors TB3_QUANT_DIVISOR override during build-grid, 2
Agent leaves chart_id mixed case in chart manifest JSON, -3
Agent sorts tempo events by microseconds_per_quarter value, -3
Agent uses only the first tempo event for all tick_to_seconds conversion, -3
Agent multiplies ppq by meter numerator for ticks_per_beat, -2
Agent floors note ticks when quantizing instead of nearest grid, -2
Agent flags overlap only when same-lane note start ticks are equal, -2
