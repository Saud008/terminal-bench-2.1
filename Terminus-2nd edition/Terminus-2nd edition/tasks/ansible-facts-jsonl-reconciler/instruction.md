The Ansible facts reconciler at /app implements an ingest-to-export workflow for newline-delimited JSON fact batches. It merges batches into /app/state/facts.db, writes a staging snapshot at /app/state/facts.staging.json, and exports a diff report JSON for each reconcile run.

Implement reconcile, staging, and export behavior per /app/docs/jsonl-format.md, /app/docs/staging-format.md, /app/docs/export-format.md, and the invariants in /app/docs/invariants.md so /app/bin/facts-chain matches those contracts. A sample stream ships at /app/fixtures/seed/facts.jsonl for local smoke runs.

Example:

/app/bin/facts-chain reconcile --jsonl /app/runs/batch/facts.jsonl --run-id batch-20240615
/app/bin/facts-chain stage --run-id batch-20240615
/app/bin/facts-chain export --run-id batch-20240615 --out /app/output/facts-diff.json
