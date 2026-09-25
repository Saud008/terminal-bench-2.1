# Ledger seal format

Default export path: /app/output/slsa-admission-ledger.json.

```json
{
  "schema": "slsacip.attest.v1",
  "seed": "...",
  "quorum_k": 2,
  "policy_packs": ["..."],
  "trust_fingerprint": "...",
  "deny_fingerprint": "...",
  "revoke_fingerprint": "...",
  "predicate_fingerprint": "...",
  "builder_fingerprint": "...",
  "results": [
    {
      "request_id": "...",
      "image": "...",
      "decision": "allow|deny",
      "reason": "...",
      "envelope_ids": []
    }
  ],
  "audit_digest": "<hex>"
}
```

Preserve pull request order. For denies, envelope_ids is []. For allows, sorted distinct contributing ids.

## audit_digest

SHA-256 hex of canonical JSON object (keys sorted, no insignificant whitespace) containing:

- seed
- quorum_k
- policy_packs
- trust_fingerprint
- deny_fingerprint
- revoke_fingerprint
- predicate_fingerprint
- builder_fingerprint
- results — array of {request_id, decision, reason, envelope_ids} in report order
