# Policy trust contract

Security attestation contract for offline tenant policy evaluation. This workspace treats each enforce run as a trust decision pipeline that must produce tamper-evident artifacts auditors can verify without live identity providers.

## Trust objectives

| Objective | Artifact |
|-----------|----------|
| Prove which policy bundles were active | policy-snapshot.json bundles and fingerprints |
| Record every access decision | enforce-report.json results rows |
| Bind decisions to staged policy state | audit_digest witness hash |

## Access-decision guarantees

1. **Deny-overrides-allow** — any matched deny policy overrides allow matches for the same request.
2. **Domain isolation** — policies and role inheritance never cross tenant domain boundaries.
3. **Transitive roles** — grouping edges compose within a domain before rule evaluation.
4. **Deterministic bundle selection** — config seed selects and shuffles bundle subsets reproducibly.
5. **Witness binding** — audit_digest hashes snapshot fingerprints, bundle order, every result row, and summary stats per /app/docs/policy-snapshot.md.

## Attestation deliverables

| Path | Trust role |
|------|------------|
| /app/state/casctl/policy-snapshot.json | Staged policy trust metadata |
| /app/output/enforce-report.json | Default witness-bound decision ledger |

Detailed effect and binding rules remain in /app/docs/access-decision-contract.md. Operator steps are in /app/docs/casctl-operator-commands.md.
