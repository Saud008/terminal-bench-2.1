# Platform rubric — go-river-job-attempt-heartbeat-scheduler-repair

**Task folder:** tasks/go-river-job-attempt-heartbeat-scheduler-repair/

Agent rebuilds riverbench with go build after editing internal Go modules, +2
Agent dequeues pending jobs by priority then lexicographic id per scheduler contract, +3
Agent clears active lease rows when a worker acks a claimed job, +3
Agent applies failure backoff from attempt exponent not wall-clock hour buckets, +3
Agent transitions jobs to poison state once attempts reach max_attempts, +3
Agent extends heartbeat only for the requested job id and matching worker, +3
Agent derives procedural seed payloads and priorities from the seed string, +2
Agent honors admin inject-heartbeat expiry overrides for stuck leases, +2
Agent fixes dequeue order alone while ack still leaves stale lease rows, -3
Agent fixes backoff alone while ack still leaves stale lease rows, -3
Agent fixes heartbeat alone while poison cap still allows endless retries, -3
Agent fixes poison handling alone while claim order still violates priority, -3
Agent introduces new exported scheduler symbols that break downstream compilation, -3
