# Clock skew normalization

Reference time comes from evaluate --now (UTC ISO-8601).

For each archive timestamp T and policy clock_skew_sec S:

- If T is strictly greater than reference_now + S seconds, treat the archive as clock-skewed.
- Normalized timestamp for bucket assignment becomes reference_now.
- Original timestamp remains stored in staging archives.
- clock_skew_adjustment_count in export equals the number of archives adjusted.

Archives at or before reference_now + S are not adjusted.
