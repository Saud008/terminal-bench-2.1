# Deny ledger seal

`POST /gate/audit/commit` writes `/app/output/deny-ledger.json` for one
`(principal, session)`.

## Merge rule

Read `/app/state/chainhead.json`. It must match the requested `principal`
and `session` (mismatch, or a missing snapshot, is HTTP 400 — there is
nothing to seal). Every field below is copied from the snapshot
**unchanged**: `jkt`, `admitted_total`, `denied_total`, `deny_totals`,
`chain_seq`, `chain_head`. Sealing never recomputes these from any other
counter source, and never adjusts any individual `deny_totals` entry.

## Schema

```json
{
  "principal": "...",
  "session": "...",
  "jkt": "...",
  "admitted_total": 0,
  "denied_total": 0,
  "deny_totals": {
    "ticket_invalid": 0,
    "alg_rejected": 0,
    "bad_signature": 0,
    "jkt_mismatch": 0,
    "htm_mismatch": 0,
    "htu_mismatch": 0,
    "iat_skew": 0,
    "jti_replay": 0
  },
  "chain_seq": 0,
  "chain_head": "...",
  "seal_digest": "..."
}
```

No field outside this schema may appear in the sealed ledger — operational
or debug metrics (entropy scores, decoy counters, internal identifiers,
etc.) must never be copied into `/app/output/deny-ledger.json`.

## Seal digest

`seal_digest` is the lowercase hex SHA-256 of the canonical compact JSON
encoding of every field above except `seal_digest` itself, with object keys
sorted lexicographically (including within `deny_totals`).

Re-committing an unchanged chainhead snapshot must produce byte-identical
ledger JSON (idempotent seal).
