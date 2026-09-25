Ingest export pipeline

Replay: load JSONL, apply VERIFIER_INITIATOR_OFFSET to ike_unique_id and child_unique_id in ingest, run event FSM, write /app/state/rekey-snapshot.json and manifest. Export: read manifest only, write report JSON. Agents must fix ingest normalization, replay FSM, uid map, selector merge, sequence tracker, and export publish together; ingest-only fixes fail export and hidden traces.
