# Infeasible job reporting

Jobs with no feasible region and start slot appear in blocked_jobs sorted by job_id. reason is RESIDENCY when no allowed region exists, DEADLINE when no start meets the inclusive deadline, QUOTA when residency and deadline pass but quota blocks all placements.
