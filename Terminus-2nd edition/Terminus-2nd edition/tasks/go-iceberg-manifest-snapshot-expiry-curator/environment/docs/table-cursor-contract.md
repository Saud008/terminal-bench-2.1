# Table cursor snapshot

Path: /app/state/table-cursor.json

Fields: engine, scenario, table, manifests, cursor_seal.

The on-disk cursor file uses two-space indent and a trailing newline. cursor_seal itself is independent of that formatting.

## cursor_seal digest

cursor_seal is lowercase hexadecimal SHA-256 (64 characters) over UTF-8 bytes of one compact JSON payload built exactly as follows:

1. Start with the literal bytes `{"manifests":{`.
2. For each manifest map key in numeric ascending meta_N load order (NumericMetaSort on meta_N.json filenames), append:
   - a comma before every entry except the first,
   - compact JSON for the manifest key string,
   - a colon,
   - compact JSON for the manifest row array value.
3. Append the literal bytes `,"table":`.
4. Append compact JSON for the table object after sorting table.snapshots by snapshot_id ascending. All other table fields keep the key order produced when unmarshaling table.json.
5. Close with `}`.

Compact JSON means no insignificant whitespace: only comma and colon separators between tokens, no ASCII space characters. Use encoding/json Marshal semantics for manifest rows and table fields, including omitempty omission of empty optional manifest entry fields.

Manifest map key order is numeric meta_N suffix ascending, not lexicographic string order.

The digest input must match lakehouse_expiry_ref reference_cursor_snapshot byte construction for bundled fixtures.
