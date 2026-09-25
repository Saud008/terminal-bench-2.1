Task identity 0ead005a84 defines the engineering problem for fishery quota landing reconciliation map. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Task identity fqlrec7a defines the engineering problem for fishery quota landing reconciliation map. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Coastal fishery compliance officers must implement a numerical quota reconciliation workflow with reference math that closes landing reports against vessel permits, species conversion tables, closed-area schedules, and seasonal carryover pools. Build fqrctl on the working Rust baseline under /app/environment to publish a species quota reconciliation atlas from landing reports, permit registries, allocation ledgers, live-weight conversion factors, and spatial closure polygons. fqrctl reads season packs from /app/fixtures/seasons/, materializes a JSONL landing ledger under /app/var/, and writes a deterministic quota atlas JSON to a caller-provided path under /app/output/ in one emit pass.

Install fqrctl at /app/bin/fqrctl with this subcommand:

  fqrctl --season <name> --token <id> --dest <path>

Species code normalization and alias resolution follow /app/docs/species-alias-lexicon.md. Product-weight to live-weight conversion follows /app/docs/live-weight-conversion.md. Vessel permit validity windows follow /app/docs/permit-validity-window.md. Closed-area spatial and temporal exclusions follow /app/docs/closed-area-polygon-contract.md. Quota allocation plus prior-season carryover follow /app/docs/quota-carryover-pool.md.

Each emit pass writes one JSON object per landing line at /app/var/quota-ledger-{token}.jsonl plus a header at /app/var/quota-ledger-{token}.header.json with ledger_fingerprint. Line schema and fingerprint rules appear in /app/docs/landing-ledger-jsonl.md. The atlas JSON includes species quota rows sorted by species code, landing audit rows sorted by landing_id, summary counters, and atlas_fingerprint per /app/docs/quota-atlas-schema.md. Atlas and ledger header run_token fields echo the --token argument. Pytest subprocess checks may write sample atlases under /app/output/ such as /app/output/tok-subproc.json as named in /app/docs/quota-atlas-schema.md.

Bundled season scenarios live under /app/fixtures/seasons/. Hidden alias-mix-trap packs ship under /opt/verifier-fixtures/fqr per /app/docs/hidden-trap-fixtures.md. Pytest contract math and hashlib fingerprint rules appear in /app/docs/pytest-verifier-primitives.md and tests/quota_atlas_verifier.py. Pytest invokes fqrctl through subprocess after cargo rebuild.
