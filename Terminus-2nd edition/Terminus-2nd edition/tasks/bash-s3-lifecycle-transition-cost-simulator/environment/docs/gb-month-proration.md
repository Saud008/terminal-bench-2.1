# GB-month proration

Monthly charges use calendar-month divisors, not a flat thirty-day month.

billable_days = inclusive day count from window_start through window_end.

days_in_month = actual calendar days in the month containing window_start.

Per-class charge in USD:

  (size_bytes / 1073741824) * rate_per_gb_month * (billable_days / days_in_month)

Incomplete multipart bytes bill at STANDARD rate using the same proration factor in multipart_pending_usd.

report_digest seals window bounds, sorted by_storage_class JSON, and multipart_pending_usd at ten decimal places.
