Timeline normalization converts capture timestamps into monotonic normalized nanoseconds anchored at zero on the first emitted packet.

For each packet, compute raw_ts_us = ts_sec * 1_000_000 + ts_usec using the endian-correct header fields from savefile-format.md.

After tolerance-window ordering (see tolerance-window.md), assign norm_ns for the first packet as 0. For each later packet i, let delta_us = raw_ts_us[i] - raw_ts_us[i-1] and delta_ns = delta_us * 1000 (microseconds to nanoseconds). Add the truncation penalty from packet i-1 (truncation-penalty.md) to delta_ns before accumulating: norm_ns[i] = norm_ns[i-1] + delta_ns + penalty_ns[i-1].

All norm_ns values are unsigned 64-bit integers.
