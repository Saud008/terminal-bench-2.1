# Lease contract

## Row lifecycle

A lease row exists only while a job is `running` and held by a worker. Creating a lease happens on successful `claim`. Heartbeat updates `expires_at_ms` and `heartbeat_at_ms` for the matching `job_id`.

## Completion cleanup

`ack` must leave no lease row for that job. Finished or poison jobs must not appear in `GET /admin/leases`.

Implement completion cleanup in the **store** layer: `MarkFinished` updates the job to `finished` **and** deletes the matching lease row. The scheduler `Ack` handler must delegate to `MarkFinished` and must **not** call lease deletion itself (including via helper wrappers).

## Expiry injection

`POST /admin/inject-heartbeat` updates `expires_at_ms` on an existing lease without changing the worker assignment. Used by the verifier to simulate stuck heartbeats.
