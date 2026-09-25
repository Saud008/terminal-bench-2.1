# Platform rubric — go-prometheus-remote-write-histogram-exemplar-staging

**Task folder:** tasks/go-prometheus-remote-write-histogram-exemplar-staging/

Agent validates remote-write block CRC before JSON decode, +3
Agent persists accepted writes to /app/data/ingest/SEED.json staging records, +3
Agent preserves native histogram schema version 2 through staging writes, +2
Agent applies relabel deduplication during snapshot export not during write handling, +3
Agent binds exemplar trace IDs to buckets with matching le labels, +3
Agent drops exemplars for counter reset series before export binding, +2
Agent increments staging sequence on repeated accepted writes for the same seed, +2
Agent reads staging from disk during snapshot export instead of in-memory shortcuts, +3
Agent rebuilds promingest with go build before serving remote-write requests, +2
Agent ignores experimental normalize helper on the production export hot path, +1
Agent patches only exemplar bind while leaving staging schema downgrade in place, -3
Agent fixes relabel dedup but skips staging persistence and sequence tracking, -3
Agent accepts blocks with invalid body checksum without returning HTTP 400, -2
Agent binds exemplars by bucket index order instead of le label matching, -2
Agent overwrites the first __name__ label during duplicate label deduplication, -2
