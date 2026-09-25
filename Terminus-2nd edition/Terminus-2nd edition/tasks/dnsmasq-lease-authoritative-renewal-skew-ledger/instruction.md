Task identity da1915b923 anchors this DHCP authoritative renewal skew ledger workflow. Implement catalog and replay behavior on the working dnsmasqledger CLI under /app so bundled JSONL logs produce contract-compliant exports. See /app/docs/ledger-replay-contract.md for identity tuple keys, renewal skew anchoring, and DNS forward invalidation rules.

The dnsmasqledger command at /app/cmd/dnsmasqledger ingests JSONL dhcp event logs, maintains authoritative lease rows and tentative offers, and writes lease-report.json plus SQLite rows at /app/work/leases.db. The scaffold under /app/internal/ already parses logs, stages snapshots, and exports reports; you must implement the authoritative renewal skew ledger rules in internal packages so replay output matches:

- /app/docs/dhcp-replay-schema.md
- /app/docs/lease-contract.md
- /app/docs/dns-forward-cache.md
- /app/docs/staging-schema.md
- /app/docs/ingest-export-pipeline.md
- /app/docs/fixture-catalog.md

Each replay run must write /app/state/lease-snapshot.json during ingest, persist leases to /app/work/leases.db, and emit /app/output/lease-report.json that an independent reference can recompute from the same log. DNS forward entries must reflect only current authoritative bindings after IP changes.

Example:

dnsmasqledger replay --log /app/fixtures/replay/001-base.jsonl --output /app/output/lease-report.json --db /app/work/leases.db

When TB3_REPLAY_DIR is set to an absolute directory, replay logs are read from that directory instead of /app/fixtures/replay/. VERIFIER_SEED may be set for procedural MAC mutation tests; when unset the verifier uses dnsmasq-lease-seed-8. Rebuild dnsmasqledger from /app after editing sources before validating replay output. Do not edit /app/docs/, /app/fixtures/, or /app/cmd/.

Structural edit constraints required by verification:

- Keep the exported PersistBeforeDNSInvalidation function in /app/internal/checkpoint/store.go.
- Keep the exported dns.Bind and dns.Invalidate functions in /app/internal/dns/cache.go with the same names.
- Do not add new Go source files under /app/internal/lease/. Implement contract behavior in the existing lease package files (ack.go, decline.go, offer.go, renew.go) plus identity/key.go and internal/replay/driver.go as needed.
