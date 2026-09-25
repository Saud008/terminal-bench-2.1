# Stability closure atlas

rows sorted by severity descending, then lot_id ascending lexicographically.

Each row includes lot_id, severity, excursion_minutes, extended_expiry, cert_digest, quarantine.

summary includes total_lots, quarantined count, max_severity, excursion_events count where excursion_events counts lots with positive excursion_minutes.

closure_digest is SHA-256 hex over sorted-key JSON with keys excursion_events, max_severity, quarantined, total_lots in sorted key order.
