# Trust witness format

After cip-tier merge and before emitting the ledger, slsacip persists /app/state/slsacip/trust-witness.json:

```json
{
  "seed": "...",
  "quorum_k": 2,
  "policy_packs": ["..."],
  "trust_fingerprint": "<hex>",
  "deny_fingerprint": "<hex>",
  "revoke_fingerprint": "<hex>",
  "predicate_fingerprint": "<hex>",
  "builder_fingerprint": "<hex>"
}
```

## Fingerprints

All fingerprints are lowercase hex SHA-256 of a canonical UTF-8 payload:

- trust_fingerprint — join root_id|issuer_glob|subject_glob lines for all loaded roots sorted by root_id, separated by \n, trailing newline omitted if empty.
- deny_fingerprint — join normalized deny digests sorted, \n-separated.
- revoke_fingerprint — join normalized_subject|start|end sorted lexicographically, \n-separated.
- predicate_fingerprint — join allow predicate types sorted, \n-separated.
- builder_fingerprint — join deny:+glob lines sorted, then require:+glob lines sorted, each group \n-separated; if both non-empty separate groups with \n.
