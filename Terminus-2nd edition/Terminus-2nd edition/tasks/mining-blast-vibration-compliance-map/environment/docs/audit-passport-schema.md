# Audit passport schema

Path: /app/work/audit-passport.json

active object fields:
- seed
- survey
- audit_run_id formatted audit- plus first 12 hex chars of SHA-256 over seed:survey:correlate_seq
- correlate_seq copied from peak correlation buffer

A new correlate pass for the same seed replaces active even if survey changes.
