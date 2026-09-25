APQ edge operators run the host-local pqgov persisted-query policy admission control plane at /app/bin/pqgov. Task identity gql-apq-cache-governor-v1 covers API-edge automatic persisted query (APQ) trust admission: operation manifests must bind authentic APQ hashes, schema fingerprints must match the tenant registry, tenant quota and TTL expiry gates must hold, and sealed audit evidence must publish only from the reconciled ledger. See /app/docs/engineering-problem-contract.md for the admission workflow, primary artifacts, and refusal-mode contracts.

pqgov stages a three-step integrity path on this host: operation manifest ingest with APQ hash binding, tenant quota and TTL expiry reconcile into SQLite, and APQ audit database export for edge compliance review. There is no outbound network step and no remote download.

Primary artifacts:

  /app/state/pq-staging.json — tamper-evident APQ staging snapshot after ingest
  /app/state/pq-ledger.db — tenant persisted-query ledger after reconcile
  /app/work/reconcile-report.json — reconcile attestation with apq_audit_seq advancement
  /app/output/pq-audit.sqlite — sealed APQ audit export backed by Python sqlite3 verifier checks

Integrity contracts cover hash authenticity, schema-hash binding, max_active eviction policy, TTL expiry anchors, compact staging_digest field order, audit sequence increments, and ledger-backed export counts. Operator surfaces and layout follow /app/docs/cli-surface.md, /app/docs/manifest-format.md, /app/docs/schema-hash-contract.md, /app/docs/tenant-quota-policy.md, /app/docs/expiry-eviction-contract.md, /app/docs/staging-snapshot.md, /app/docs/reconcile-report-contract.md, /app/docs/audit-export-schema.md, and /app/docs/verifier-refmath-contract.md.

Admission must keep those artifacts consistent across ingest, reconcile, and export. A partial path that only stages one command surface or skips cross-stage policy gates will miss the staging snapshot, tenant ledger, reconcile report, and sealed audit export contracts. Operation manifests under /app/fixtures carry APQ operation_hash bindings, schema_hash compatibility against the tenant schema registry, and registered_at_ms / last_seen_ms timestamps used by GraphQL cache eviction policy.

The verifier rebuilds /app/bin/pqgov from source via /app/scripts/verifier-rebuild.sh before each test, so swapping the binary or reimplementing in another language is not graded. ingest writes pq-staging.json. reconcile updates pq-ledger.db and reconcile-report.json while advancing /app/state/apq-audit-seq.json as the audit sequence counters. The audit verb in cli-surface.md writes pq-audit.sqlite for positive apq_audit_seq values.

The evaluation environment has no internet at build or test time. No new Go modules can be fetched. The only available SQLite driver is the pure-Go modernc.org/sqlite module already listed in /app/go.mod. CGo SQLite drivers such as github.com/mattn/go-sqlite3 will fail the offline readonly-module build.

Bundled scenarios under /app/fixtures include clean-tenant, schema-drift, quota-bound, expiry-stale, and hash-normalize. Apply the cited /app/docs integrity contracts for each scenario when producing staging, ledger, reconcile, and audit artifacts. Do not edit /app/docs/, /app/fixtures/, or anything under /tests. Independent pytest helpers gql_persist_independent and gqlcache_verifier_harness recompute admission digests and export counts against the sealed artifacts.
