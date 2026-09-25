# Proxy flush queue ordering

When a flush batch is emitted, order entries by session_start_ts ascending, then by seq ascending within the same session_start_ts.

Arrival seq alone must not determine flush order when multiple sessions share the proxy buffer. Older sessions (earlier session_start_ts) flush before newer sessions even if their interim packets arrived later.

After flush, update last_flush_ts on each affected session to the flush now_ts.

Pending entries that are not yet due remain in flush_queue on the snapshot sorted by session_start_ts then seq.
