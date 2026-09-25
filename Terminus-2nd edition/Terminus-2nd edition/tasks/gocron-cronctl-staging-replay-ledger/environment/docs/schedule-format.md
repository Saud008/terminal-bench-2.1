# Schedule format

Scenario files are JSON objects:

- window_start: RFC3339 UTC instant where replay begins
- window_end_ms: replay duration in milliseconds from window_start
- jobs: array of job objects with fields id (logical name before seed prefix), cron (5-field cron in job timezone), location (IANA zone name), tags (string map), singleton (boolean)
- events: optional timed injections with at_ms offset from window_start, job_id, action (reschedule or panic), panic (boolean legacy flag)

When seed S is provided, cronctl namespaces job ids to S:id before persistence.

Jobs sharing tags.singleton_group must not execute concurrently; at most one fire per group per instant.
