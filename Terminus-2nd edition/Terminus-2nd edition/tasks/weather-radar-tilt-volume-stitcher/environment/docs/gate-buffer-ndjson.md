# Gate buffer NDJSON

Stitch fusion writes /app/var/gate-buffer-{token}.ndjson with one gate record per line. Sidecar /app/var/gate-buffer-{token}.meta.json stores run_token, bundle_id, row_count, ledger_fingerprint as sha256 of NDJSON bytes.

Each record carries scan_label, tilt_deg, azimuth_centideg, bridged_azimuth_centideg, range_bin, raw_dbz, calibrated_dbz, quality_mask, included boolean.
