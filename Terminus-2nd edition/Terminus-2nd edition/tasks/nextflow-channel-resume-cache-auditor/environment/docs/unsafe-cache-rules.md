# Unsafe cache rules

Audit evaluates each staged task and emits findings sorted by task_id then rule name.

## digest_drift

When cached is true and prior_digest is non-empty, normalized container_digest must equal prior_digest. Otherwise emit digest_drift with detail:

`cached digest {container_digest} != prior {prior_digest}`

## glob_expansion_mismatch

When expansion_hash is non-empty and differs from computed_expansion_hash, emit glob_expansion_mismatch with detail:

`recorded {expansion_hash} computed {computed_expansion_hash}`

## lineage_break

Recompute lineage_digest as root-first parent_hashes then task hash (NUL-separated SHA-256). When it differs from the staged lineage_digest claim, emit lineage_break with detail:

`staged {lineage_digest} expected {recomputed}`

When a trace task record includes lineage_digest, ingest admits that value as the staged claim; otherwise ingest computes it.

## retry_stale_cache

When attempt is greater than one, cached is true, and prior_exit_status is non-null with value not equal to zero, emit retry_stale_cache with detail:

`attempt {attempt} cached after prior exit {prior_exit_status}`

## provenance_crossrun

When run resumed is true, task cached is true, cache_session_id is non-empty, and cache_session_id differs from staging session_id, emit provenance_crossrun with detail:

`cache session {cache_session_id} != run session {session_id}`

Findings persist to /app/work/audit-findings.json. audit_generation in /app/state/audit-generation.json must match staging audit_generation before export.
