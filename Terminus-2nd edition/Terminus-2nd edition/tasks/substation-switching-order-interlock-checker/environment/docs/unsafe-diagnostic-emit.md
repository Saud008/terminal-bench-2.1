# Unsafe diagnostic emit

verify-order writes JSON with:

- seed, scenario, loto_ticket_id
- steps: array of per-step rows with step_index, action, breaker_id, safe (bool), reason_codes (sorted unique strings), energized_buses after the step (sorted)
- summary: total_steps, unsafe_count, final_energized_buses (sorted)
- audit_digest: sha256 hex of normalized summary + step_index list + reason code multiset

Reason codes: lockout_active, close_blocked_energized, open_parallel_risk, out_of_order, unknown_breaker
