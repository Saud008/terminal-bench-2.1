# Session staging schema

Staging file path: /app/state/mqtt-journal-staging.json

Fields: engine, broker, scenario, event_count, events[], staging_digest.

Events preserve journal order by seq. staging_digest is sha256 over broker, scenario, and events array JSON.
