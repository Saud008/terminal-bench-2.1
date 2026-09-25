# Breach seal

A discontinuity opens exactly one breach seal spanning the missing inclusive range.

## Fields

| Field | Meaning |
|-------|---------|
| `from_seq` | First missing sequence (`last_seq + 1` at discontinuity) |
| `to_seq` | Last missing sequence (`jump_seq - 1`) |
| `missing_span` | `uint32(jump_seq - from_seq)` count of missing sequences |
| `opened_mono_ms` | Monotonic open time |
| `closed` | True when every seq in the span has been repaired |

## Ban seal

Opening a breach issues one ban seal tied to that breach (`active=true`).

## Grace revoke

When a breach closes, if `(now_mono - breach_opened_mono) <= grace_ms`, deactivate the ban seal. Otherwise the ban remains active after closure.

`grace_ms` defaults to `5000` from config.
