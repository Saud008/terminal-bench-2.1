# Point-in-time join

For each as_of_ts and feature, select the latest event where event_ts is less than or equal to as_of_ts after TTL and partition filters.

Ties on event_ts resolve using duplicate-event-ts.md before comparing online and offline values.
