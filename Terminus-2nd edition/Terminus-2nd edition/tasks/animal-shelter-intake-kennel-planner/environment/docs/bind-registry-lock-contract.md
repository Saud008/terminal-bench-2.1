# Bind registry lock digest

Ingest bind stage writes /app/state/intake-bind-clean-intake.json for the bundled clean-intake scenario including registry_digest witness, kennel_count, quarantine_count, and priority_scores. Other scenarios use the same basename pattern with the run-id argument replacing clean-intake.

bind copies the scenario registry.sqlite to /app/state/registry-clean-intake.sqlite before digest computation.

registry_digest is sha256 hex over sorted kennel_id:species_code pairs joined by pipe, then pipe catalog_seed, then pipe sorted quarantine rows formatted as kennel_id:start:end.

Quarantine window rows belong in the digest payload. Weave staging must not run until bind ingest completes.
