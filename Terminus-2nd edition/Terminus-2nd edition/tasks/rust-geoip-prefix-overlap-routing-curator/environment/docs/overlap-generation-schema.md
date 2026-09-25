# Overlap-generation ledger schema

Path: /app/work/overlap-generation.json

active object fields:
- seed
- bundle
- reconcile_id formatted merge- plus first 12 hex chars of SHA-256 over seed:bundle:load_generation
- load_generation copied from feed-normalize cache

A new run-reconcile for the same seed replaces active even if bundle changes.
