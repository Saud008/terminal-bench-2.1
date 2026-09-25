# Path-scoped resume

POST /v1/resume receives a JSONL resume_path. Each record has line, now_unix, machine_id,
client_seq, and payload. /app/state/srcursor-by-path.json records applied lines by source path:
a restart or repeated path skips its own applied lines, while a different path with equal line
numbers remains eligible.

Crash JSONL inputs for resume live under /app/work/jsonl-resume; each file path is the cursor scope key.
