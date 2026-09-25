# Tilt scan bundle format

Each bundle directory under the fixture root contains bundle.json with bundle_id, station metadata, manifest counters, and tilt_scans array. Each tilt scan includes scan_id, elevation_deg as a JSON number, channel string keying calibration_offsets_dbz, and rays with azimuth_centideg integer hundredths of a degree and gates with range_bin, dbz, and quality_mask where zero means valid and one means suppressed.

Station station_id strings are opaque identifiers echoed in volume metadata. Manifest expected_ray_count and expected_gate_bins define the inventory denominator for completeness scoring multiplied by tilt_count.
