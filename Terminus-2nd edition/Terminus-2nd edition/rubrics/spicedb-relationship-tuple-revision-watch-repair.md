# Platform rubric — spicedb-relationship-tuple-revision-watch-repair

**Task folder:** tasks/spicedb-relationship-tuple-revision-watch-repair/
**Written:** 2026-07-28T03:15:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent advances watch next_cursor only for namespace-filter-matched events, +3
Agent applies tombstone_revision before caveat JSON so deleted tuples deny after tombstone, +3
Agent encodes and decodes zed tokens as eight big-endian revision bytes, +3
Agent uses stale snapshot summaries when lag is less than or equal to watch_stale_lag_threshold, +3
Agent recomputes revision-snapshot check_summaries from live probe evaluation after each write, +3
Agent invalidates closure cache entries on namespace prefix delete so later checks deny, +2
Agent exports authz-report with snapshot_revision, namespace_counts, and allowed/denied probes, +2
Agent applies DirectTupleLookup tombstones on export probes so deleted direct tuples deny despite group paths, +2
Agent rebuilds relationwatchd via verifier-rebuild.sh without network package installs, +2
Agent leaves /app/docs, /app/config, /app/fixtures, main.go, and server.go unchanged, +1
Agent aligns only the zed token encoder while snapshot lag policy stays wrong, -3
Agent hardcodes check_summaries instead of evaluating alice and bob probes, -3
Agent treats export DirectTupleExists misses as allow when transitive group membership remains, -2
Agent edits protected docs, fixtures, or verifier math under /opt to force a pass, -5
