# Verifier reference math contract

Pytest compares kcompactctl CLI output to independent reference math implemented in /tests/compact_segment_refmath.py.

The reference layer uses the same digest rules as frozen-segment-staging.md and the same normalization rules as key-normalize-contract.md. Digest computation uses hashlib.sha256 over canonical JSON. Key normalization uses unicodedata.normalize with NFC before user: prefix lowercasing.

Hidden scenarios may set TB3_TOMB_RETENTION_MS to override the default tombstone window. The retention-bias off-catalog scenario uses window 50000 ms when that variable is set.

Agents implement behavior in Go under /app/internal. The Python reference is verifier-only and is not part of the shipped binary.
