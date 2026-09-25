simulate loads mesh JSON, normalizes defaults, processes events into tally records, writes survey-snapshot.json and survey.manifest, then export writes survey-report.json from manifest only.

Ingest normalization sets default_ttl_ms to 30000 when missing. Export must not reload mesh files.

Rebuild ballotmesh after internal changes. reset-state.sh clears output and state directories.
