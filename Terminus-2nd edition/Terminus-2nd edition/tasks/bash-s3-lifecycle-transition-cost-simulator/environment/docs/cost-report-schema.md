# Monthly cost report

Fields: bucket, window_start, window_end, total_usd (string with 2 decimals), by_storage_class (map of class to gb_months and usd strings), multipart_pending_usd, suppressed_by_legal_hold_count, delete_marker_orphan_versions, report_digest.

GB-months prorate using actual calendar days in window_start month: charge = size_gb * rate_per_gb_month * (billable_days / days_in_month).

report_digest is sha256 hex over window_start, window_end, sorted by_storage_class JSON, and multipart pending USD string. Reference helper: /app/scripts/contract_digest.py (hashlib).

JSON keys sorted, compact separators, trailing newline.
