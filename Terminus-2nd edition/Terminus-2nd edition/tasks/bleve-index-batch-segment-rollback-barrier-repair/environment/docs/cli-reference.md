# CLI Reference

Binary: /usr/local/bin/blevectl

Ingest:
blevectl ingest --index NAME --batch PATH

Export:
blevectl export --index NAME --out PATH

Environment override:
- TB3_INDEX_PREFIX: optional index root directory prefix. Default root is /app/state/indexes when unset.
- Verifier runs set TB3_INDEX_PREFIX to /app/state/tb3-indexes so per-index artifacts (root-map.json, meta.json, merge-plan.json, segments) are isolated under that prefix.
