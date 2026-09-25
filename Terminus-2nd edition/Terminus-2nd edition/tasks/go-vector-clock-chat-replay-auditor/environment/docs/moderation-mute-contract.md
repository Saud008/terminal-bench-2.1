# Moderation and mute contract

## Moderation payload

| Field | Type |
|-------|------|
| action | ban, kick, mute, warn |
| target | user id |

## Precedence rank

Higher rank wins when two moderation actions target the same user and are concurrent:

| action | rank |
|--------|------|
| ban | 4 |
| kick | 3 |
| mute | 2 |
| warn | 1 |

When actions are causally ordered, later actions apply normally. When concurrent, only the highest rank action is effective for findings and timeline visibility.

## Mute window

mute_start and mute_end events define an interval per target user.

Active mute interval is half-open: timestamp_ms >= start_ms and timestamp_ms < end_ms.

A message from a muted target during an active interval produces finding code mute_leak.

## Moderation conflict finding

When a lower-rank moderation action is concurrent with a higher-rank action on the same target, emit moderation_conflict with detail lower_rank_suppressed.
