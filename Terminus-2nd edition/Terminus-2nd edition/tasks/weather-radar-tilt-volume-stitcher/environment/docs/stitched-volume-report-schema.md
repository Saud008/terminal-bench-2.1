# Stitched volume report schema

vrstctl stitch --dest emits a JSON report with run_token, bundle_id, station_id, elevation_sequence array, tilt_count, valid_gate_total, mean_calibrated_dbz, coverage_fraction, azimuth_coverage_centideg, report_digest.

report_digest is sha256 hex of compact JSON for station_id, valid_gate_total, mean_calibrated_dbz, coverage_fraction keys in that order. Example pytest destination /app/output/subproc-check.json.
