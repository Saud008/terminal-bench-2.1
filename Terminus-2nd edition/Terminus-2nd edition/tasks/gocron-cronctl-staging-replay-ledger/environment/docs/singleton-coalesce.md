# Singleton lock

When singleton is true on a job, overlapping cron entries for the same job id must coalesce to one execution per fire instant.

When tags.singleton_group is set, all jobs sharing that tag value coalesce the same way even if cron expressions differ.

Coalesce keys are scoped to a single fire instant (`at_ms`). Distinct instants inside the same tick window (for example when TB3_TICK_MS spans multiple planned times) must each get their own execution; a hold from an earlier instant must not suppress a later instant.

Deduped attempts are recorded with status deduped and deduped true in the ledger.

Distributed lock leases gate execution independently per job id: acquiring or holding a lease for one job must not block a different job id. After a panic event for a job, that job's lease must be released (lock_held false on the panic row) and must not renew while that job's holder slot is empty.
