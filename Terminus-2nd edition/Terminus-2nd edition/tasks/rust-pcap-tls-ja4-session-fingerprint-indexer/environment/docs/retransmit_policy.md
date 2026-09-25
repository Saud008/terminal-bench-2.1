# Retransmit deduplication policy

Intake must remove later frames that repeat evidence already captured for the same session. Two retransmit cases are treated as duplicates.

The first duplicate case is a repeated `(session_quad, seq)` pair. The second duplicate case is a later frame whose TLS payload bytes hash to the same value as an earlier frame in that session, even if the sequence number differs.

The earliest frame wins in both cases. Frame count is measured on the raw session frame list before deduplication, while unique_frames is measured after both duplicate filters have been applied.

The emitted `anomalies.retransmit` counter counts only raw pre-dedupe frames whose retransmit flag byte is non-zero. Frames removed solely because they duplicate an earlier `(session_quad, seq)` pair or payload hash do not increment this counter unless their own retransmit flag is set.

`totals.anomaly_frames` is the sum of per-session `anomalies.retransmit` values across all emitted sessions.
