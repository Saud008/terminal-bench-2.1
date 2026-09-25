# Counter reset detection

Within each rollup window, examine samples in scrape_order ascending.

Whenever value decreases compared to the previous sample in the same window, treat as counter reset and restart the delta baseline from the new value.

Do not limit reset detection to only the first sample in the window.

After each reset, discard the prior delta segment. Do not accumulate partial deltas from earlier segments in the same window.

Rate per second is (last_value - baseline) / window_seconds where baseline is the value at the most recent reset in the window. If no reset occurred, baseline is the value at window start.
