# Trust admission workflow

Offline access-decision attestation for tenant policy bundles. Trust operators use casctl to publish tamper-evident trust artifacts and witness-bound access decisions before approving production policy changes.

## Trust and attestation model

Each enforce run binds three trust artifacts:

1. **Policy snapshot** — tamper-evident fingerprints of merged policy and grouping CSV rows plus seed-selected bundle order under /app/state/casctl/policy-snapshot.json.
2. **Decision ledger** — per-request allow or deny outcomes with match counts in the enforcement report.
3. **Audit witness** — audit_digest SHA-256 hex digest that binds snapshot fingerprints, loaded bundles, every result row, and summary stats per /app/docs/policy-snapshot.md.

Compromise of staged policy metadata or exported rows breaks witness verification. Attestation must refuse silent tamper by producing digest mismatches.

## Admission attestation pipeline

1. Load model name and bundle candidates from config.
2. Select and shuffle-merge policy bundles deterministically from config seed.
3. Stage policy snapshot with policy_fingerprint and grouping_fingerprint.
4. Evaluate each access request against domain-scoped policies with transitive role inheritance.
5. Apply deny-overrides-allow effect aggregation on all rule hits.
6. Emit enforcement report with witness-bound audit_digest.

Detailed effect and bundle rules are in /app/docs/access-decision-contract.md and /app/docs/policy-trust-contract.md. Module trust roles are in /app/docs/admission-toolchain.md.

## Attestation deliverables

| Path | Trust role |
|------|------------|
| /app/state/casctl/policy-snapshot.json | Staged policy trust metadata |
| /app/output/enforce-report.json | Default witness-bound decision ledger |

Report schema and digest serialization are in /app/docs/report-schema.md and /app/docs/policy-snapshot.md.
