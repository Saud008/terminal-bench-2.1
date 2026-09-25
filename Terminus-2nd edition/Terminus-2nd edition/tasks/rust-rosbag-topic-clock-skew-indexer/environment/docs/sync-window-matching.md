# Sync window matching

Use reference_topic from manifest latch unless TB3_REFERENCE_TOPIC overrides. sync_window_ns defaults from meta unless TB3_SYNC_WINDOW_NS overrides. For each reference message at stamp R, anchor equals R. Pair non-reference messages whose header_stamp_ns lies within sync_window_ns divided by two of R. Emit one closest match per topic per anchor sorted by ref_stamp_ns topic header_stamp_ns.
