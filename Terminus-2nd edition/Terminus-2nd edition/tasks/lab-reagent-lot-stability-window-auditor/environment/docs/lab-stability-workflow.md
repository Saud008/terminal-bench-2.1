# Lab stability workflow

Phase A — correlate: read one session bundle JSON, compute per-lot thermal and calendar fields, persist /app/work/stability-correlation/<session-id>.json. When a correlation file already exists for the session id, read its correlate_generation and write correlate_generation as prior value plus one.

Phase B — publish-closure: read only the correlation JSON for the session id. Do not reopen bundle fixtures. Emit ranked closure rows and summary counters to the caller output path.

Quarantine is true when excursion_minutes is positive. publish-closure must not re-derive excursion math from bundle telemetry.
