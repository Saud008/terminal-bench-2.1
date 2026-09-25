# Session index rules

Emit reads only the persisted session ledger and writes /app/output/session_index.json, and must not rescan raw capsule files or derive fresh intake state during emit.

The emitted report contains a sessions array and a totals object. Sessions are sorted by session_id ascending and each row preserves role_map, ja4, frame_count, unique_frames, and anomalies from the persisted inputs after JA4 derivation.

The totals.session_count field equals the number of session rows. The totals.anomaly_frames field equals the sum of per-session retransmit anomaly counters.
