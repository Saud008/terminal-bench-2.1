The pulumi-dep-export CLI under /app/cmd/pulumi-dep-export ingests mock Pulumi stack snapshot JSON, validates it, stages a dependency ledger at /app/state/dep-ledger.json, and writes a dependency-ordered export report. Rollout automation reports resource order drift versus engine expectations when validation, graph construction, ledger persistence, topological ordering, or export serialization diverge from policy.

Implement the Go packages under /app/internal/ so the order pipeline matches /app/docs/validate-contract.md, /app/docs/dependency-contract.md, /app/docs/ledger-schema.md, /app/docs/epoch-persistence.md, /app/docs/export-schema.md, /app/docs/module-api-contract.md, /app/docs/stack-snapshot-format.md, and /app/docs/fixture-catalog.md. Keep the export entry point BuildReport(snap, ledgerPath) documented in module-api-contract.md unchanged while completing validation, graph build, ledger staging with epoch and adjacency digest, topological sort, and ledger-backed serialization.

Example command:

pulumi-dep-export order --stack /app/fixtures/stacks/07-merged.json --output /app/output/merged-order.json

After a successful run on the merged catalog snapshot, /app/output/merged-order.json and /app/state/dep-ledger.json must exist. Verifier cases may also write /app/output/pulumi-export-order.json for other catalog snapshots.

Rebuild with go build -mod=readonly -o /usr/local/bin/pulumi-dep-export ./cmd/pulumi-dep-export from /app. Do not edit /app/docs/, /app/fixtures/, /app/config/, or /tests.
