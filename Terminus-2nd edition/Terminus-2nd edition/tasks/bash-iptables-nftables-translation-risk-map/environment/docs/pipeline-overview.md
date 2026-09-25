# Translation risk pipeline overview

fw-risk-map is a two-stage Bash and AWK pipeline:

1. **ingest** — parse iptables-save and nftables excerpt files named in a pair manifest, normalize matches, compute policy precedence ranks, bind counters, detect unsupported iptables modules, and write `/app/state/iptables-tuples.ndjson`, `/app/state/nft-tuples.ndjson`, and `/app/state/staging-meta.json`.
2. **export** — read staging artifacts only and emit `/app/output/translation-risk-report.json`.

Export must never open the original iptables or nft source paths listed in the pair manifest. Tests poison those files after ingest to enforce this boundary.

## CLI surface

```
fw-risk-map ingest --pair <manifest.json>
fw-risk-map export --pair <pair_id> --output <path>
```

The pair manifest provides `pair_id`, `iptables_path`, `nft_path`, and optional `notes`.

## Cross-run ledger

`/app/state/run-seq.json` holds `run_seq` (monotonic integer) and `last_pair_fingerprint` (sha256 of manifest bytes plus both source file bytes). When ingest sees the same fingerprint as the last successful ingest, `run_seq` must not increment.

## Staging digest

`staging_digest` in staging-meta is sha256 of the concatenation of iptables-tuples.ndjson bytes, nft-tuples.ndjson bytes, and the canonical JSON serialization of the policy_precedence array (compact keys, no spaces).

Export must echo `staging_digest` and `pair_id` in the risk report header.
