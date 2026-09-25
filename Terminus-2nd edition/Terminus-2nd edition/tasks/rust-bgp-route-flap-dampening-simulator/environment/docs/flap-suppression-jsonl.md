# Flap suppression JSONL

One JSON object per line for prefixes where flap_count positive or suppressed true at end or peak_penalty at or above reuse_threshold.

Fields: peer_id, prefix, final_penalty, suppressed, flap_count, peak_penalty, stable_at_ms.

Sort output by peer_id then prefix.

stable_at_ms comes from ledger stable_at_ms, not last event event-time unless that is when post-event stability began. It stays null when no event left the slot withdrawn with penalty below reuse_threshold after its advertised-state update (for example decay-reuse: the final announce re-installs before a stability stamp).
