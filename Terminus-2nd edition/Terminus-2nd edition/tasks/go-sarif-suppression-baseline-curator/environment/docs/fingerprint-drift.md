# Fingerprint drift

Physical fingerprint hashes location identity. SARIF partial fingerprint strings detect content drift against baseline.

## Physical fingerprint

physical_fingerprint = lowercase hex sha256 of UTF-8 body:

lower(uri) + "|" + rule_key + "|" + start_line + ":" + start_column

Use remapped uri and canonical rule_key.

## Drift flag

drift_from_baseline is true when a baseline row shares rule_key, remapped uri, and start_line but the scan partial fingerprint string differs from the baseline fingerprint string.

Both strings must be non-empty for drift to be true.
