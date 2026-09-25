# zonefrag workspace

The zonefrag CLI under /usr/local/bin merges BIND-style zone trees with $INCLUDE fragments. Authoritative contracts live in /app/docs/. Bundled public fixtures are under /app/fixtures/bundles/. Verifier-only hidden bundles are installed at /opt/verifier-fixtures/ during image build.

Implement the Bash modules under /app/lib/ so ingest, export, verify, and compile emit contract-aligned snapshots and exports. Do not edit /app/docs/, public bundles under /app/fixtures/bundles/, or verifier-only bundles under /opt/verifier-fixtures/.
