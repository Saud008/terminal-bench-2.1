# Sample hash deduplication

Within each asset_id and rule_name group, only the first occurrence of a sample_sha256 is actionable.

First is defined by the lowest detected_ms; ties break on lowest event_id lexicographically.

Later events with the same sample_sha256 are retained in incidents with suppressed true, actionable false, and suppression_reason duplicate_sample.

Dedupe applies only among events that pass rule revision validation.
