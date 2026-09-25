# Source freshness windows

Age-window policy applies to source nodes using loaded_at timestamps compared against the pack evaluated_at clock.

For each source row compute minutes_elapsed as whole minutes between evaluated_at and loaded_at. When TB3_FRESHNESS_BIAS_MINUTES is set, add that integer bias to minutes_elapsed before classifying status.

Status classification uses strict greater-than boundaries:

  ok when minutes_elapsed is less than or equal to warn_after_minutes
  warn when minutes_elapsed is greater than warn_after_minutes and less than or equal to error_after_minutes
  error when minutes_elapsed is greater than error_after_minutes

A boundary minute equal to warn_after_minutes remains ok. A boundary minute equal to error_after_minutes remains warn.

Each freshness row appears in export bundles and contributes to summary stale_source_count when status is warn or error.

SOURCE_STALE alerts (one per non-ok freshness row):

  - alert_code: SOURCE_STALE
  - severity: the freshness status (`warn` or `error`)
  - subject_id: the seed-scoped source unique_id
  - message: exactly `source stale {minutes_elapsed} min` using the integer minutes_elapsed after bias (for example `source stale 180 min`, never `… minutes` or a message that embeds the source unique_id)
