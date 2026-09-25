# History staging schema

Staging file path: /app/state/wf-history-staging.json

Fields: engine, namespace, scenario, event_count, max_run_generation, events[], staging_digest.

Events preserve canonical workflow order. staging_digest is sha256 over namespace, scenario, max_run_generation, and events array JSON using /app/fixtures/digest_util.py sha256_canonical_json.
