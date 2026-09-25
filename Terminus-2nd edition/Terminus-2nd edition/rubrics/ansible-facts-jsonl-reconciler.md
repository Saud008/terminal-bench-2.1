# Platform rubric — ansible-facts-jsonl-reconciler

**Task folder:** tasks/ansible-facts-jsonl-reconciler/

Agent keys hosts and facts by inventory_uuid not hostname, +3
Agent applies latest collected_at merge with later line tie-break, +3
Agent validates JSONL records before any SQLite write for that line, +2
Agent writes staging snapshot only after schema validation succeeds, +2
Agent records fact_diffs with stringified JSON scalar old and new values, +3
Agent sets changed_key_count to distinct diff keys not snapshot row total, +2
Agent computes changed_keys_digest as sorted uuid tab key SHA-256, +2
Agent uses INSERT OR IGNORE so second reconcile does not duplicate diffs, +2
Agent exports diff_rows sorted by inventory_uuid then fact_key, +2
Agent uses hostname as inventory_uuid breaking distinct host identity, -3
Agent writes facts.staging.json when stage validation fails, -3
Agent exports null old_value on changed numeric or string facts, -3
Agent counts all fact_snapshots rows in changed_key_count, -2
Agent accepts invalid collected_at timestamps during reconcile, -2
