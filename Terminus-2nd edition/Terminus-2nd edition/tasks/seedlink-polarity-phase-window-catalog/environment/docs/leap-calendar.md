# Leap-second chronology calibration

UTC leap-second table membership adjusts pick center times during waveform calibration closure. See `/app/docs/scientific-computing-workflow.md` for chronology stage ordering.

Leap tables live under /app/config/leap/leap-epochs.json as:

```json
{ "positive_leap_epochs": [ <utc_epoch_int>, ... ] }
```

When leap_marker is 1 on a snippet, add 1_000_000 microseconds to every pick center time if either:

- epoch_sec is listed in positive_leap_epochs, or
- epoch_sec + 1 is listed in positive_leap_epochs

This models the extra UTC second inserted at the end of a leap day. Hidden verifier deployments may supply alternate leap tables under /opt/verifier-fixtures/leap/ — seedcat must read leap-epochs.json from /app/config/leap at export time unless TB3_LEAP_ROOT is set to an absolute directory path.

When TB3_LEAP_ROOT is set, load leap-epochs.json from that directory instead of /app/config/leap.
