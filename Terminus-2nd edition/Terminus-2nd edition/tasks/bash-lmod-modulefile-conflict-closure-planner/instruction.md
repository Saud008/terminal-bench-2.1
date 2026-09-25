Implement an HPC Lmod load-plan planner under /app. The working baseline ships a Bash CLI at /app/sbin/lmodplan with three subcommands: ingest, resolve, and export. Your job is to complete the planner so it ingests a modulefile catalog, writes an intermediate staging artifact, resolves dependency closure with conflict precedence and family swaps, orders PATH mutations deterministically, and exports a reproducible load-plan manifest.

The planner must read module metadata from line-oriented catalog files described in /app/docs/catalog-format.md. Conflict resolution must follow numeric priority rules in /app/docs/conflict-precedence.md. Family exclusivity and swap unload semantics are defined in /app/docs/family-semantics.md. PATH prepend and append stacking rules live in /app/docs/path-mutation-rules.md. The exported JSON contract is specified in /app/docs/load-plan-schema.md.

CLI surface:
- lmodplan ingest --catalog DIR --out /app/state/catalog.snapshot
- lmodplan resolve --snapshot PATH --request FILE --staging /app/state/resolve.staging --run-id ID
- lmodplan export --staging PATH --out /app/output/load-plan.json

A non-authoritative optional wrapper helper lives in /app/lib/decoy/wrap_decoy.sh and must not be required for export.

Success criteria: ingest produces a catalog snapshot with schema version and catalog digest. resolve writes staging containing unload sequence, load sequence, path mutation list, and run ledger metadata. export emits sorted JSON matching the schema with a stable plan digest. Re-running resolve with the same run-id on unchanged inputs must be idempotent. Cross-run replay must bump sequence only when the request file changes.

Tests invoke /app/sbin/lmodplan via subprocess and compare results to independent reference logic. Bundled catalogs live under /app/fixtures/catalogs. Hidden probe catalogs may appear only under extra fixture roots configured by the verifier.
