# Platform rubric — weather-radar-tilt-volume-stitcher

**Task folder:** tasks/weather-radar-tilt-volume-stitcher/

Agent sorts elevations numerically before materializing gate rows, +3
Agent stages gate-buffer NDJSON with bridged_azimuth_centideg per gate, +3
Agent applies per-channel calibration addends from station manifest, +3
Agent suppresses quality_mask one gates from mean_calibrated_dbz aggregates, +3
Agent computes azimuth_coverage_centideg with wrap bridging past 360 degrees, +3
Agent scores coverage_fraction from manifest ray and gate inventory, +2
Agent writes deterministic report_digest over coverage and aggregate fields, +2
Agent drives vrstctl stitch via subprocess after rebuild script, +2
Agent binds site snapshot under /app/var during stitch with bundle token, +2
Agent separates surveillance versus reflectivity calibration offset channels, +2
Agent honors VRST_FIXTURE_ROOT for alternate PPI bundle roots, +2
Agent resets /app/var scratch state before cross-run stitch cases, +1
Agent sorts tilt scans by scan_id string instead of elevation_deg numerically, -3
Agent subtracts calibration offset instead of adding per channel table, -3
Agent computes azimuth coverage without bridging past 360 degrees, -3
Agent leaves elevation_sequence in lexical scan_id order, -3
Agent includes quality-masked gates in mean_calibrated_dbz, -2
Agent uses tilt_count alone as coverage_fraction denominator, -2
Agent applies reflectivity offset to surveillance channel gates, -2
Agent publishes coverage_fraction above one on sparse ray bundles, -2
Agent writes volume report without gate-buffer NDJSON staging file, -2
Agent emits stitched report missing report_digest field, -2
Agent omits valid_gate_total from stitched volume report, -2
Agent implements doppler_alias folding on stitch export hot path, -2
Agent runs stitch without cargo rebuild in verifier path, -1
