# Timezone rules

Resolve each job IANA zone from the location field only. Tags are metadata and must not override location for fire-time calculation.

When tags.tz disagrees with location, ignore tags.tz silently and keep location. Do not error at load or replay.

When location is empty, use the scheduler default from /app/config/scheduler.json.

All planned fire timestamps in /app/state/replay-snapshot.json must be computed with the same location rules used during replay export.
