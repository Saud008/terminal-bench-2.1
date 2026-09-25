# Continuity policy

Sequences are `uint32`. Arithmetic is modular.

## Admission rules

1. **First beat** on a session sets `last_seq` to that seq and records it as accepted. No breach.
2. **Continuous**: if `seq == last_seq + 1` (uint32 wrap), admit, advance `last_seq`, extend witness. Wrap from `MaxUint32` to `0` is continuous — no breach.
3. **Duplicate**: if `seq` was already accepted in this session, HTTP 409 and `duplicate_rejections++`. Duplicate scope is per `(token, session_id)`, not token-wide.
4. **Discontinuity** (seq is neither next nor a repair of an open breach):
   - Admit the jump beat
   - Open **one** breach seal with `from_seq = next`, `to_seq = seq - 1` (uint32), `missing_span = uint32(seq - next)`
   - Issue **one** ban seal for that breach
   - Set `last_seq = seq`
   - `breaches_opened++`, `missing_span_total += missing_span`
5. **Repair**: a beat whose `seq` lies in `[from_seq, to_seq]` of an **open** breach and is not yet repaired:
   - Mark that seq repaired; `repair_events++`
   - Do **not** advance `last_seq` solely because of a repair
   - When every seq in the span is repaired, close the breach (`breaches_closed++`) and apply grace revoke on the ban seal
6. **Skew**: if `|(client_ms - anchor_client) - (mono - anchor_mono)| > skew_tolerance_ms`, HTTP 409 and `skew_rejections++` (do not admit)
7. Unbound session or bad ticket → HTTP 400; missing required JSON fields → HTTP 400

## Order

Repair membership must be evaluated **before** duplicate / `seq <= last_seq` rejection so in-span repairs are admitted.
