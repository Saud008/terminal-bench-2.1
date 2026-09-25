# Casctl trust-admission gate

You need an offline access-decision admission tool that decides whether tenant policy bundles may be trusted for sealed audit export on this host. The tool stages a tamper-evident policy snapshot, applies deny-overrides authenticity and domain-scoped role-inheritance integrity gates over JSONL access-request batches, and publishes a digest-sealed enforce-report attestation with audit_digest only when those gates hold. There is no remote identity provider and no outbound network step.

casctl at /usr/local/bin/casctl is that tool. Operators run enforce to admit policy bundles, stage trust metadata, evaluate the request batch, and seal the attestation.

## Operator surface

CLI flags and defaults live in /app/docs/casctl-operator-commands.md.

casctl enforce --config PATH --requests PATH --output PATH must stage /app/state/casctl/policy-snapshot.json before evaluating requests, bind witness digests per the trust contracts, and refuse sealed export when authenticity gates are unset or drifted. Default output is /app/output/enforce-report.json.

## Integrity policy

Field-level trust rules live in the docs below. Admission must enforce every gate before sealing:

- trust admission workflow: /app/docs/trust-admission-workflow.md
- policy trust contract and audit witness binding: /app/docs/policy-trust-contract.md
- deny-overrides authenticity, domain-scoped role inheritance, and seed-bound bundle admission: /app/docs/access-decision-contract.md
- tamper-evident policy snapshot layout: /app/docs/policy-snapshot.md
- sealed enforce-report attestation schema: /app/docs/report-schema.md
- policy and model admission layouts: /app/docs/policy-format.md, /app/docs/model-format.md
- fixture catalog: /app/docs/fixture-catalog.md
- admission toolchain roles: /app/docs/admission-toolchain.md

## Paths and fixtures

Primary artifacts are /app/state/casctl/policy-snapshot.json (tamper-evident staging after admitted policy load) and /app/output/enforce-report.json (digest-sealed access-decision attestation with audit_digest). Bundled fixtures live under /app/fixtures. Hidden verifier trees may appear under /opt/verifier-fixtures. Do not edit /app/docs/, anything under /app/fixtures/, /app/config/casctl.json, or anything under /tests/.
