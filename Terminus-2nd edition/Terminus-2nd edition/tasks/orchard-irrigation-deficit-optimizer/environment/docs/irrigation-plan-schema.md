# Irrigation plan schema

Output JSON contains run_id, assignments sorted by field_id then window_index, quota_ledger sorted by window_index, deficit_trace sorted by field_id then window_index, summary with assignment_count and total_liters, plan_digest as sha256 hex (sha256sum over canonical JSON) of assignments and deficit_trace arrays.
