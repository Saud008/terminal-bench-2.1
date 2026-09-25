# Staging snapshot

Ingest writes /app/state/incident-snapshot.json before export output.

The snapshot lists incident_marker_persisted_ms per incident_key, pending_job_keys blocked on markers, boundary_events_fired ids, dedup_pairs seen as batch_id:job_key strings, and staging_written false on the final persisted file.

Handlers must not flip staging_written during replay; only the final ingest write persists the snapshot once.
