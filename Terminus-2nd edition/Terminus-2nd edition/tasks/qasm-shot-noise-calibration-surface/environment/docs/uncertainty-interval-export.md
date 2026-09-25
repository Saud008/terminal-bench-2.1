# Uncertainty interval export

Uncertainty intervals quantify shot-noise envelope width per qubit bin using Wilson score half-width on mitigated probabilities.

For each qubit, use total shots equal to the sum of raw histogram counts for that qubit. For each bin i, let p be the mitigated probability after matrix application, n the total shots, and z = 1.96.

Compute Wilson half-width: z/(2n) * sqrt(4*n*p*(1-p) + z*z) / (1 + z*z/n).

Store lower = max(0, p - half) and upper = min(1, p + half) rounded to six decimal places in the ledger intervals map.

Wilson intervals must use mitigated probabilities. Using pre-mitigation normalized or drift-only probabilities produces invalid export envelopes.

## Export digest payload

The report export digest is lowercase hex SHA256 over a canonical JSON payload. The payload contains exactly four top-level fields and no others:

1. experiment_id (string)
2. selected_matrix_id (string)
3. envelopes (object)
4. provenance (object with chain and digest)

There is no top-level intervals field. Intervals and total_shots live only inside each qubit entry under envelopes.

Build the digest payload from the same logical content written to shot-noise-envelope.json: experiment_id, selected_matrix_id, envelopes, and provenance. Do not add ledger-only fields such as normalized_probs or drift_corrected.

### envelopes object

envelopes maps qubit label strings to per-qubit objects. Before serialization, sort envelope keys alphabetically ascending (for bundled data the order is q0 then q1).

Each per-qubit envelope value has exactly three fields in this order:

1. mitigated (array of floats rounded to six decimals)
2. intervals (array of objects, one per mitigated bin, each with lower and upper rounded to six decimals)
3. total_shots (integer)

### provenance object

Copy the full provenance block from the ledger unchanged: chain (sorted string array) and digest (lowercase hex SHA256 of the compact JSON encoding of chain alone).

## Canonical JSON serialization

Serialize the digest payload as compact JSON with no insignificant whitespace:

- Comma separator with no following space
- Colon separator with no surrounding spaces
- Equivalent to Python json.dumps(payload, separators=(",", ":"))

Top-level field order in the serialized object is experiment_id, selected_matrix_id, envelopes, provenance.

Inside each envelope value, field order is mitigated, intervals, total_shots.

Inside each interval object, field order is lower then upper.

Hash the UTF-8 bytes of the compact JSON string with SHA256. Encode the digest as lowercase hexadecimal. Write envelope-digest.txt as that hex string followed by a single newline.

## Bundled data example

After ingest and compute on /app/data/, the digest payload for report export looks like this (pretty-printed for readability; the hash uses the compact form shown on the next line):

```
{
  "experiment_id": "bell-readout-v2",
  "selected_matrix_id": "M_alpha",
  "envelopes": {
    "q0": {
      "mitigated": [0.424, 0.584],
      "intervals": [
        {"lower": 0.393427, "upper": 0.454573},
        {"lower": 0.553507, "upper": 0.614493}
      ],
      "total_shots": 1000
    },
    "q1": {
      "mitigated": [0.538, 0.458],
      "intervals": [
        {"lower": 0.507158, "upper": 0.568842},
        {"lower": 0.427178, "upper": 0.488822}
      ],
      "total_shots": 1000
    }
  },
  "provenance": {
    "chain": ["M_alpha", "bell-readout-v2", "cal-a-02", "cal-m-03", "cal-z-01"],
    "digest": "af5bfe42cab58d27c72d1001285f7fd350d381a59324669601f047370acbcea8"
  }
}
```

Compact serialization (UTF-8 input to SHA256):

```
{"experiment_id":"bell-readout-v2","selected_matrix_id":"M_alpha","envelopes":{"q0":{"mitigated":[0.424,0.584],"intervals":[{"lower":0.393427,"upper":0.454573},{"lower":0.553507,"upper":0.614493}],"total_shots":1000},"q1":{"mitigated":[0.538,0.458],"intervals":[{"lower":0.507158,"upper":0.568842},{"lower":0.427178,"upper":0.488822}],"total_shots":1000}},"provenance":{"chain":["M_alpha","bell-readout-v2","cal-a-02","cal-m-03","cal-z-01"],"digest":"af5bfe42cab58d27c72d1001285f7fd350d381a59324669601f047370acbcea8"}}
```

Expected envelope-digest.txt for bundled data:

```
ae5b871870359f9dcee3912708cb0750dd3d934cbf1bb388f16821e37afb941c
```
