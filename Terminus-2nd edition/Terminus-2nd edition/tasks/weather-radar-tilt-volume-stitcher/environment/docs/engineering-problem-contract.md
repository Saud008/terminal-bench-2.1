# Engineering problem contract — weather radar tilt volume stitcher

Task identity wradst8c. Reasoning pattern: spherical PPI geometry fusion with numeric tilt_rank, azimuth_wrap bridging on centidegree circles, per-channel dBZ calibration_offset application, hydrometeor quality_mask suppression, manifest coverage_fraction scoring.

Root cause classes: tilt_rank lexical scan_label sort, azimuth_wrap ignored at 360 degree boundary, calibration_offset subtracted instead of added, quality_mask not suppressing gated samples, coverage_fraction using tilt_count instead of manifest expected gate inventory.

Failure modes verified by pytest: wrong elevation_sequence arrays, azimuth_coverage_centideg collapsing on wrap bundles, mean_calibrated_dbz including masked gates, coverage_fraction inflated on sparse manifests, per-channel calibration_offset mismatch on surveillance versus reflectivity channels.
