# Verifier reference contract

Pytest drives pqgov through gqlcache_verifier_harness subprocess helpers. gql_persist_independent implements staging digest, quota, expiry, schema, and audit export reference math independent of Go sources.

Before pytest, the verifier session rebuilds the binary with /app/scripts/verifier-rebuild.sh. Cross-run checks may clear /app/state, /app/work, and /app/output with /app/scripts/reset-state.sh.

Hidden traps under /opt/verifier-fixtures/pqgov follow the same /app/docs contracts as bundled fixtures.
