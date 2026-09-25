# Federation atlas contract

federation-atlas.json fields: scenario, change_count, changes[], report_digest.

Each change: path, change_type (added|removed|modified), optional left_value and right_value.

SVID delta paths use the literal prefix `/x509_svid/` followed by the full SPIFFE ID string (no JSON Pointer escaping of `/` or `:`). Example:

```json
{
  "path": "/x509_svid/spiffe://example.org/workload/b",
  "change_type": "added",
  "right_value": "abc0:spiffe://example.org/workload/b"
}
```

left_value and right_value are compact strings `serial:spiffe_id`, not JSON objects.

Trust-domain field deltas use path `/trust_domain`.

When there are no deltas, `changes` must be a JSON empty array `[]` (never `null`).

Changes sorted by path ascending.

emit-atlas requires seal_counter > 0.
