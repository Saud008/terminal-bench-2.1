# Bundle catalog

Policies under /app/registry/policies/ include enterprise-strict (required UV, reject duplicates).

- enterprise-trust: two valid packed transcripts with distinct credential ids
- uv-required-trap: transcript with UV false under required policy
- duplicate-credential-batch: duplicate credential_id across transcripts
- broken-chain: invalid cert chain linkage
