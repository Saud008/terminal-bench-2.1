The ballotmesh CLI under /app/cmd/ballotmesh simulates nanomsg surveyor/respondent ballot collection over a scripted mesh and writes /app/state/survey-snapshot.json plus /app/output/survey-report.json. Mesh event layout is in /app/docs/mesh-event-format.md. Surveyor FSM transitions are in /app/docs/surveyor-fsm.md. Ballot sealing and deadline merge rules are in /app/docs/ballot-merge-deadline.md. Survey TTL and respondent reconnect behavior are in /app/docs/survey-ttl-reconnect.md. Message header survey id encoding is in /app/docs/message-header-layout.md. Star topology tally deduplication is in /app/docs/topology-star-dedup.md. Staging fields are in /app/docs/staging-snapshot.md and exported tally fields in /app/docs/export-schema.md. The ingest-to-export pipeline is summarized in /app/docs/ingest-export-pipeline.md.

Repair /app/internal/ so ballotmesh simulate succeeds for every JSON mesh under /app/fixtures/meshes/ and for any other valid mesh that conforms to /app/docs/mesh-event-format.md, persists a snapshot matching the simulated timeline, and exports a report whose tally records, sealed ballot flags, partial respondent lists, topology weights, and final weighted totals match the mesh events. Export must read the staged snapshot manifest only and must not re-parse mesh files or re-run simulation logic during export.

Example:

ballotmesh simulate --mesh /app/fixtures/meshes/001-star-complete.json --output /app/output/survey-report.json

Report table suffix follows VERIFIER_TABLE_SUFFIX when set, otherwise default. After Go changes, rebuild ballotmesh before grading. Do not edit /app/docs/, /app/fixtures/, or /app/config/, and do not replace the tool with a hardcoded report writer.
