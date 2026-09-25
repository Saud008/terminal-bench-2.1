# Platform rubric — ais-voyage-leg-anomaly-segmenter

**Task folder:** tasks/ais-voyage-leg-anomaly-segmenter/
**Written:** 2026-07-28T18:00:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements RFC3339 ts_epoch parsing with fractional truncation toward zero, +3
Agent applies MMSI dedupe on rounded coordinates within AIS_MMSI_DEDUPE_SEC ignoring station, +3
Agent keeps lowest seq when collapsing MMSI and burst duplicates, +3
Agent collapses base-station burst duplicates during ingest per AIS_BURST_MS window, +3
Agent uses ray-casting port polygons with edge and degenerate ring handling, +3
Agent suppresses impossible-speed points via haversine nautical miles on export, +3
Agent segments voyage legs on port transitions including none labels draught delta and max gap, +3
Agent writes stable staging sorted by mmsi ts_epoch seq with feed_stats out_of_order, +2
Agent exports voyage atlas sorted by mmsi then numeric leg ordinal with leg_chain_digest, +2
Agent rebuilds aissegment after editing ingest staging and export modules, +2
Agent resolves TB3_AIS_DIR basename inputs for hidden AIS streams, +2
Agent ignores latitude sort helper on the atlas ordering hot path, +1
Agent patches parse only while burst collapse stays disabled in ingest, -3
Agent uses bounding-box port checks instead of polygon ray casting, -3
Agent applies MMSI dedupe with station in the duplicate key, -3
Agent keeps highest or first-seen seq on duplicate collapse discarding lower seq, -3
Agent skips impossible-speed suppression but fixes leg segmentation only, -2
Agent sorts voyage_legs by lexicographic leg_id string instead of numeric ordinal, -2
Agent emits voyage legs without anomaly summary counters, -2
