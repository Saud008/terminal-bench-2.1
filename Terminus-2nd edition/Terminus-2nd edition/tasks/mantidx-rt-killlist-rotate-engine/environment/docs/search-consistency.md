# Search consistency

search writes search-report.json with query, hit_count, and doc_ids sorted ascending.

A document is searchable only when killed=0 in the docs table.

Killed documents must never appear in doc_ids even if update-attr was attempted on them.

Search scans all tiers (ram and disk). Rotate does not revive killed documents on disk chunks.
