# Query fingerprint export

Export reads /app/state/logql-stage.json only and writes /app/output/query-fingerprint.json.

Fingerprint is SHA-256 hex over the canonical query string, a pipe character, and comma joined selected group labels from the stage snapshot. Canonical query form is defined at parse time in the stage query.canonical field.

vector_checksum is the unsigned sum of per-vector checksum fields in the stage vectors array.

Export command: lokictl export [--pass N]
