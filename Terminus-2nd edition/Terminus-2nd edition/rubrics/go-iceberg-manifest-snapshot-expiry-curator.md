# Platform rubric — go-iceberg-manifest-snapshot-expiry-curator

**Task folder:** tasks/go-iceberg-manifest-snapshot-expiry-curator/

Agent walks snapshot ancestry chains from branch and tag ref heads to build protected snapshot closure, +3
Agent traverses manifest lists recursively including nested manifest paths for reachability, +3
Agent applies inclusive delete-file retention floor from current snapshot timestamp minus retention hours, +3
Agent protects every ancestor snapshot for each branch and tag ref per branch-tag contract, +3
Agent excludes deleted manifest entries from live file reachability accounting, +3
Agent computes staging digest with snapshots sorted by id and manifests in numeric meta load order, +3
Agent increments analyze_revision only after analyze pass writes findings under work, +2
Agent blocks emit-plan until analyze_revision is strictly greater than zero, +2
Agent sorts expired snapshot ids ascending in expiry plan output, +2
Agent seals plan_digest over scenario protected_count and expired_snapshot_ids keys, +2
Agent honors TB3_DELETE_RETENTION_HOURS override on hidden delete boundary scenarios, +2
Agent rebuilds iceexpctl via verifier-rebuild.sh before subprocess CLI checks, +2
Agent loads meta manifest shards using lexicographic string sort instead of numeric meta order, -3
Agent uses strict greater-than retention floor instead of inclusive delete eligibility, -3
Agent omits tag ref snapshots from protected closure set, -3
Agent treats nested manifest paths as unreachable during manifest walk, -3
