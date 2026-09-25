# Event order contract

Events sort by timestamp_ms ascending. When timestamp_ms ties, sort by event_id ascending, then seq ascending. Ingest must not rely on fixture file line order alone.
