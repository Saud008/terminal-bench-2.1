# Platform rubric — go-graphql-persisted-query-cache-governor

**Task folder:** tasks/go-graphql-persisted-query-cache-governor/

Agent normalizes GraphQL query_text whitespace before sha256 operation hash binding during ingest, +3
Agent validates manifest schema_hash against tenant schemas.json not manifest_version alone, +3
Agent writes pq-staging.json as compact JSON with sorted operation_id rows and staging_digest, +2
Agent evicts stale persisted queries using last_seen_ms TTL anchor from expiry.json, +3
Agent enforces tenant max_active by evicting oldest last_seen_ms LRU active rows under quota cap, +3
Agent increments apq_audit_seq by one on each successful reconcile pass, +2
Agent blocks audit export when apq_audit_seq is zero, +2
Agent exports pq-audit.sqlite meta active_count and evicted_count from ledger not staging length, +3
Agent honors TB3_QUOTA_BIAS when tightening hidden tenant quota trap scenarios, +2
Agent applies TB3_COMPOUND_SCHEMA compound schema_hash binding on hidden schema-trap ingest, +2
Agent patches only manifestload while leaving expiry eviction on registered_at anchor, -3
Agent uses decoy legacywrap hash path on ingest or export hot path, -2
Agent exports audit rows from staging manifests without reading pq-ledger.db, -3
Agent skips apq_audit_seq advance allowing export without reconcile barrier, -3
Agent weakens quota enforcement by counting evicted rows toward max_active headroom, -2
