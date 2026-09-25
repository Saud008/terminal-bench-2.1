# Pytest verifier primitives

Bundled pytest uses hashlib.sha256 hex digests when recomputing report_digest from station_id, valid_gate_total, mean_calibrated_dbz, and coverage_fraction JSON.

Anti-hardcoding traps clone bundles into rnd-station-trap and rnd-elev-trap scratch directories with random.Random seeds documented in tests/stitch_volume_verifier.py.

Contract helpers live in tests/stitch_volume_verifier.py alongside the vrstctl subprocess driver.
