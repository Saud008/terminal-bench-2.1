Out-of-order timestamps within a capture must be stabilized before normalization.

Default tolerance window WINDOW_US is 5000 microseconds unless PCAP_JITTER_WINDOW_US is set to a positive integer.

When reordering, compare packets by their original capture index (file order). Two packets A and B may be swapped only if abs(raw_ts_us[A] - raw_ts_us[B]) > WINDOW_US and the swap moves later timestamps earlier. Equivalently: perform a stable ordering where packets whose raw timestamps differ by at most WINDOW_US keep their original file order relative to each other; only pairs more than WINDOW_US apart may be sorted by increasing raw_ts_us.

Do not apply a full global sort by timestamp alone.
