# TTL window

Given ttl_seconds and as_of_ts, an event is TTL-eligible when as_of_ts minus event_ts is less than or equal to ttl_seconds and event_ts is less than or equal to as_of_ts.

TB3_TTL_BIAS adds to ttl_seconds when set for hidden scenarios.

Events outside the TTL window are excluded from join selection and counted in ttl_filtered_count.
