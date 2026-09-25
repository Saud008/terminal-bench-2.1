# Maxage window

All message internal_date values are UTC unix seconds.

Given reference_epoch (UTC), maxage_sec, tz_offset (minutes), and optional OI_MAXAGE_OFFSET_SEC (defaults 0):

    effective_ref = reference_epoch + (tz_offset * 60)
    cutoff_utc = effective_ref - maxage_sec + offset_sec

A manifest row syncs only when internal_date >= cutoff_utc and its folder passed folder filtering.

Broken simulators often compare local-midnight derived cutoffs against UTC message dates, or subtract maxage before applying tz_offset. The effective_ref form above is authoritative.

Per-run probes may set OI_MAXAGE_OFFSET_SEC to a positive integer to tighten the window without editing CLI flags.
