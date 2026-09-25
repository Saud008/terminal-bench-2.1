# Staging snapshot schema

Path: /app/state/lease-snapshot.json

Fields:
- now_sec: simulated clock after replay
- active_count: count of authoritative leases in catalog (including expired until expire pass — count is pre-export expire sweep in replay driver final pass)
- dns_forward: map hostname to ip string
- checkpoint_seq: last replay_checkpoint through_seq applied

Written once per replay before lease-report.json export.
