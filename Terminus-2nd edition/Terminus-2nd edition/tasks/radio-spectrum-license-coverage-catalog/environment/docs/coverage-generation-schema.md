# Coverage generation schema

Path: /app/work/rf-atlas-generation.json

active object fields:
- seed
- bundle
- atlas_seq_id formatted atl- plus first 12 hex chars of SHA-256 over seed:bundle:load_generation
- load_generation copied from WAL grant frame

A new synthesize-atlas for the same seed replaces active even if bundle changes.
