Task identity 7ed40b5571 defines the engineering problem for libp2p bitswap wantlist cancel reconciliation. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.



Implement the bswapd bitswap session driver on the working Go baseline under /app. The tool ingests JSONL traces from /app/fixtures/bitswap/, writes a normalized staging snapshot at /app/state/bitswap-snapshot.json, replays wantlist and block exchange events in memory, and exports a session report to the path given by --output on the pipeline subcommand. Metrics export uses a separate subcommand and schema in /app/docs/bitswap-metrics-export.md.



Cancel ordering, multihash want deduplication, peer delivery credits, idle session cleanup, and priority scheduling after merged cancels must match /app/docs/bitswap-contract.md, /app/docs/bitswap-trace-events.md, /app/docs/bitswap-display-cid-rules.md, /app/docs/bitswap-staging-snapshot.md, /app/docs/bitswap-session-export.md, /app/docs/bitswap-cancel-inflight-guard.md, and /app/docs/bitswap-session-idle-limits.md. Every cid field in staging and export rows is a display CID from the trace registry; canonical multihash hex keys are internal only and never appear in snapshot or export JSON.



bswapd pipeline --log /app/fixtures/bitswap/001-basic-wants.jsonl --session demo --output /app/output/session-report.json



bswapd metrics --log /app/fixtures/bitswap/006-priority-cancel.jsonl --session demo --output /app/output/metrics-report.json



Fixture roles are listed in /app/docs/bitswap-fixture-roles.md. Runtime path defaults are in /app/docs/bitswap-runtime-paths.md. The tool is rebuilt from /app sources before checks. Optional environment overrides TB3_SESSION_PREFIX, TB3_FIXTURES_DIR, and VERIFIER_SEED when documented in the contract docs.



Do not edit /app/docs/, files under /app/fixtures/, or files under /tests/.

