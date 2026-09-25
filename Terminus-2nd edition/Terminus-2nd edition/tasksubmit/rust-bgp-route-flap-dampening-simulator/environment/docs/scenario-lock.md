# Scenario lock

Path: /app/state/scenario-lock.json

Fields: scenario_id, feed_fingerprint, feed_relpath, line_count, peer_table

feed_fingerprint is lowercase hex sha256 of raw feed bytes. Verifier reference code uses hashlib sha256 over raw feed bytes when recomputing fingerprints.

Exponential half-life decay in reference math uses math.pow with factor 0.5 raised to elapsed over half_life_ms.

peer_table maps peer id to dampening record. line_count is deduplicated feed line count.

Ledger keys inside flap-ledger.json use peer_id:prefix form. Bundled scenarios include edge-a:192.168.10.0/24, edge-a:172.16.1.0/24, edge-a:203.0.113.0/24, edge-a:10.1.0.0/24, edge-a:10.20.0.0/24, and core-1:198.18.0.0/24.

The lock must not embed the events array. drive-feed re-reads feed bytes from fixtures using feed_relpath.
