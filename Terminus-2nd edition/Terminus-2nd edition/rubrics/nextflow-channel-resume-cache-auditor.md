# Platform rubric — nextflow-channel-resume-cache-auditor

**Task folder:** tasks/nextflow-channel-resume-cache-auditor/

Agent normalizes container digests by stripping case-insensitive sha256 prefix before staging, +3
Agent expands input globs in lexicographic order when computing expansion_hash, +3
Agent chains parent_hashes root-first then task hash into lineage_digest, +3
Agent writes resume-stage.json staging snapshot before audit evaluates cache rules, +2
Agent flags digest_drift when cached task container digest differs from prior_digest, +3
Agent flags glob_expansion_mismatch when recorded expansion_hash differs from recomputed, +3
Agent flags retry_stale_cache when attempt greater than one reuses cache after failed prior, +3
Agent flags provenance_crossrun when resumed run cache session differs from run session_id, +3
Agent persists audit findings and bumps audit-generation.json before export gate, +2
Agent exports unsafe-cache report matching sorted findings and audit_digest canonical hash, +2
Agent rebuilds nfresume-audit after editing ingest audit or export packages, +2
Agent patches glob sort only while leaving lineage digest child-first ordering, -3
Agent treats SHA256 uppercase prefix as normalized without lowercasing hex body, -3
Agent flags retry_stale_cache when prior_exit_status is zero instead of non-zero failure, -3
Agent skips provenance_crossrun when resumed run cache marker session mismatches, -3
Agent exports unsafe-cache report before audit-generation gate is satisfied, -2
