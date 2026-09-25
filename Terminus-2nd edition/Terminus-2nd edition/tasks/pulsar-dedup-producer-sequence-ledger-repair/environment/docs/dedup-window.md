# Dedup window

Out-of-order sequences may be accepted only when the sequence number was not previously accepted for that stream.

A duplicate sequence inside the dedup window increments dedup_miss and must not advance high_water or accepted_count.
