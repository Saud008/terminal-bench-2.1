# Enforcement report schema for witness-bound authorization exports.

`/app/output/enforce-report.json`:

```json
{
  "model": "rbac_domains_priority",
  "bundles": ["bundle-b", "bundle-a", "bundle-c"],
  "results": [
    {
      "sub": "alice",
      "dom": "tenant1",
      "obj": "records",
      "act": "write",
      "decision": "deny",
      "match_count": 2
    }
  ],
  "stats": {
    "requests": 10,
    "allows": 4,
    "denies": 6,
    "policies_loaded": 35,
    "groupings_loaded": 14
  },
  "audit_digest": "a1b2c3..."
}
```

`results` preserve request input order. `match_count` is the number of policies matching the request.

`bundles` lists bundle directories actually loaded for the config `seed` (subset and order of config candidates).

`audit_digest` is a lowercase SHA-256 hex digest binding the staged policy snapshot to the exported results and stats. The exact line order, field separators, and hashing rules are defined under **Audit digest canonical form** in `/app/docs/policy-snapshot.md`.
