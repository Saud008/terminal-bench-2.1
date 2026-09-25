# Compression filters

Filter chains are identified by a SHA-256 hex digest of the filter names joined with pipe characters in catalog order. Do not reorder or sort filter names when computing the hash.

filter_chain_id in the binary index is informational only; staging and export must emit filter_chain_hash derived from the catalog filter list.

compression_totals.filter_usage counts how many chunks reference each filter name (a chunk with filters [shuffle, gzip] increments both shuffle and gzip by one).
