Task identity 1469c830fd defines the engineering problem for ais voyage leg anomaly segmenter. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Operational workflow for coastal traffic analysts at the North Sea VTS desk: reconcile AIS position reports from Rotterdam and Hamburg approach corridors. Operators need a repeatable voyage leg atlas that survives mixed receiver bursts, duplicate MMSI coordinates, and overnight gaps without manual chart review.

Build the segment CLI on the working Rust baseline under /app. The feed subcommand normalizes each line-oriented stream into /app/state/track-snapshot.json per track-snapshot-schema. The atlas subcommand reads that snapshot and writes /app/output/voyage-atlas.json with leg boundaries, anomaly counters, and a stable leg_chain_digest.

Subcommand flags and exit codes are documented in /app/docs/aissegment-cli.md.

Feed applies MMSI coordinate collapse and base-station burst filtering while recording feed_stats per /app/docs/ais-stream-format.md, /app/docs/mmsi-coordinate-collapse.md, /app/docs/basestation-burst-collapse.md, and /app/docs/track-snapshot-schema.md.

Atlas applies impossible-speed gating, splits voyage legs on port transitions and draught deltas, and emits voyage_legs plus anomaly summaries per /app/docs/speed-anomaly-suppression.md, /app/docs/port-polygon-rules.md, /app/docs/draught-leg-boundaries.md, /app/docs/voyage-leg-rules.md, and /app/docs/voyage-atlas-fields.md.

When TB3_AIS_DIR points at an absolute directory, feed reads --input basenames only from that directory. Bundled streams live under /app/fixtures/streams/ and polygon fixtures under /app/fixtures/ports.geojson. Verifier-only hidden streams may appear under /opt/verifier-fixtures/ais.

Build the segment CLI from /app so the binary is available at /app/target/debug/aissegment. Implement feed and atlas behavior in the Rust sources wired into the workspace build. Do not edit /app/docs/, /app/fixtures/, or /tests/. The sort_lane helpers are not authoritative for atlas emission. Pytest loads tests/vts_leg_independent.py helpers that digest bundled streams and independently recompute atlas JSON.

See /app/docs/engineering-problem-contract.md for the maritime voyage analytics engineering objective.
