# Inventory JSONL format

One JSON object per line. Fields:

- bucket (string)
- key (string)
- version_id (string)
- is_delete_marker (boolean)
- size_bytes (integer, 0 for delete markers)
- storage_class (string)
- last_modified (ISO-8601 UTC)
- tags (object string to string)
- legal_hold (boolean)
- retention_mode (GOVERNANCE, COMPLIANCE, or null)
- retention_until (ISO-8601 UTC or null)
- multipart_id (string or null)
- multipart_complete (boolean, true when not multipart)

Blank lines and lines starting with # are ignored. Duplicate version_id for the same key: last line in file order wins. Verifier duplicate-line probes use /app/state/dup.jsonl and /app/state/dup.stage.json.

Example seed keys: logs/2024/access-01.json, archive/report-Q1.pdf, legal/prefix/secret.dat, drafts/tmp.txt. Example timestamps: 2024-01-01T00:00:00Z, 2024-02-01T00:00:00Z.
