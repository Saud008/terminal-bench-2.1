# Balance closure schema

emit-closure writes JSON with trial_id, protocol_digest, run_id, per_stratum rows with active arm counts, max_skew as the maximum absolute arm difference across strata, venues_at_cap sorted, open_slots with remaining slots in the current incomplete block, and closure_digest sha256 over closure body fields. Verifier negative probes may target /app/output/blocked.json for emit-closure calls that lack a prior run-balance run_id.
