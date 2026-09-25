# Export Manifest

The export command writes a JSON manifest at the caller-provided output path.

Manifest schema:
- index: string
- doc_count: integer
- segments: array of segment file names
- ordered_keys: array of key strings in configured collator order

doc_count reflects only committed and checksum-valid records currently visible from root mapping.
