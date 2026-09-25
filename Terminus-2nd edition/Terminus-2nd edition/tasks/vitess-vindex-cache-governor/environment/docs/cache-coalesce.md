# Lookup cache and coalesce

The in-memory lookup cache stores entries with vindex_name, key_hex (typed cache key from vindex-contract.md), shard, and generation.

Coalesce merges an optional seed cache into the active store when ingest runs (see cli-surface.md ingest --cache-seed). Only entries whose generation equals the shard map generation being ingested may survive coalesce. Entries from older or newer generations are dropped; ingest records how many were removed in the snapshot coalesce_dropped field. Export copies that count into routing-audit.json.

Put replaces an entry with the same typed key_hex. Lookup returns a hit only when key_hex and entry generation match the requested routing generation.

Flush clears all entries on migration rollback.
