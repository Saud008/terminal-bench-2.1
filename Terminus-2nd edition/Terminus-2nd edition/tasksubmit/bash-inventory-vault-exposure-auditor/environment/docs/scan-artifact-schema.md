# Staging schema

State directory: /app/state

scan-manifest.json fields:

- tree_id: manifest tree id
- tree_fingerprint: sha256 over manifest and inventory files
- staging_digest: sha256 over the raw /app/state/host-rows.ndjson bytes followed immediately by the raw /app/state/atlas-rows.ndjson bytes. Both files are UTF-8 NDJSON, each row is serialized with sorted JSON keys, each row ends with a single newline, and the final row also keeps its trailing newline. There is no extra separator beyond the bytes already present in those two files.
- host_count: number of hosts
- finding_count: number of findings rows
- merge_order: ordered section labels from hosts.ini

host-rows.ndjson: one JSON object per line with host, groups array, effective_vars object. Path: /app/state/host-rows.ndjson

atlas-rows.ndjson: one JSON object per line with category, host, var_key, severity, source_path. Path: /app/state/atlas-rows.ndjson
