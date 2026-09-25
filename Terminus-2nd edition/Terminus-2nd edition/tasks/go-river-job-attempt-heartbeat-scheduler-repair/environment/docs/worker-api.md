# Worker HTTP API

Base URL: configured listen address (default `127.0.0.1:8092`).

## POST /worker/claim

Body: `{"worker_id": "w1"}`

Returns the claimed job JSON. Creates a running job and lease row.

## POST /worker/{job_id}/heartbeat

Body: `{"worker_id": "w1"}`

Extends the lease for **that job id** when the worker id matches the lease owner. Must not refresh a different job held by the same worker.

## POST /worker/{job_id}/ack

Body: `{"worker_id": "w1"}`

Marks the job `finished` and removes its lease row via store `MarkFinished` (see `/app/docs/lease-contract.md`).

## POST /worker/{job_id}/fail

Body: `{"worker_id": "w1", "error": "message"}`

Applies failure policy (backoff or poison), deletes the active lease for that job.

## Admin

- `POST /admin/seed` — body `{"seed": "..."}` optional `jobs` override
- `GET /admin/jobs?state=pending|running|finished|poison`
- `GET /admin/leases` — active lease rows only
- `POST /admin/inject-heartbeat` — body `{"job_id","worker_id","expires_at_ms"}` or `expires_at_delta_ms` sets lease expiry for test injection
- `POST /admin/force-ready` — body `{"job_id"}` sets `available_at_ms` to now for a pending job (verifier retry pacing only)
