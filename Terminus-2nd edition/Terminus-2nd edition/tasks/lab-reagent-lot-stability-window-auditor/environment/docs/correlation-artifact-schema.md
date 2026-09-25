# Correlation artifact schema

Path: /app/work/stability-correlation/<session-id>.json

Fields:
- correlate_generation: monotonically increasing unsigned integer; first correlate for a session id writes 1
- session_id: opaque session identifier from CLI
- bundle: bundle name matching fixtures
- as_of_date: ISO date copied from bundle
- lots: correlated lot records with cert_digest, excursion_minutes, extended_expiry, severity, quarantine

Each correlate for the same session id increments correlate_generation even when the bundle name changes.
