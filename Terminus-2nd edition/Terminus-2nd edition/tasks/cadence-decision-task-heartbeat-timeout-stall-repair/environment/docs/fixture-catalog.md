Scenario catalog under /app/fixtures/scenarios:

01-heartbeat-order.json — stale lower-seq heartbeat must not extend visibility.
02-timeout-grace.json — timeout check within heartbeat grace while heartbeats active.
03-query-reset-gate.json — reset query still requires progress gate.
04-sticky-refresh.json — sticky map generation bump before poll.
05-duplicate-event-id.json — duplicate event_id without cursor jump.
06-merged-stall.json — combined heartbeat, sticky, history, timeout, query timeline.

Verifier-only scenarios ship under /opt/verifier-fixtures/.
