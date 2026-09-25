# Curtailment mask contract

Curtailment windows in scenario JSON use start_utc and end_utc RFC3339 timestamps.

A reading aligned to interval_start_utc is curtailed when it falls inside any window using half-open interval semantics:

active when start_utc <= interval_start_utc < end_utc

The end_utc boundary is excluded. A reading aligned exactly to end_utc is not curtailed.

Curtailed readings produce settlement lines with skipped_curtail true, zero market and settlement cents, and amount_cents zero. They still appear in settlement-lines.jsonl for audit.

Non-curtailed readings proceed to market lookup and strike settlement math.
