# Admission toolchain roles

The casctl trust-admission tool composes integrity modules under /app/internal/authzkernel/ with supporting parsers and export writers. Modules cooperate to stage policy trust metadata, evaluate access requests, and emit witness-bound attestations.

## Module trust roles

| Module | Trust responsibility |
|--------|---------------------|
| load | Seed-driven bundle subset selection and merge order |
| staging | Policy and grouping fingerprint snapshots for audit binding |
| match | Domain-scoped subject/object/action binding with role inheritance |
| effect | Deny-overrides-allow aggregation on matched policies |
| audit | audit_digest witness serialization over snapshot and results |
| enforce | Attestation pipeline orchestration for casctl enforce |

Supporting packages under /app/internal/parse/, /app/internal/model/, /app/internal/config/, and /app/internal/export/ provide CSV ingestion and report emission. The casctl entrypoint at /app/cmd/casctl/ invokes the admission attestation pipeline.

Attestation semantics are defined in /app/docs/policy-trust-contract.md and /app/docs/trust-admission-workflow.md. This document describes module trust roles only.
