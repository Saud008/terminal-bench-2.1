# Platform rubric — go-vault-token-lease-renewal-risk-auditor

**Task folder:** tasks/go-vault-token-lease-renewal-risk-auditor/

Agent implements vaultaud audit writing /app/state/lease_audit_buffer.jsonl with effective TTL and lineage fields, +3
Agent resolves policy inheritance using minimum max_ttl_sec along parent chains, +3
Agent applies TTL cap precedence as minimum across mount role policy and lease request, +3
Agent propagates mount and role non-renewable flags through renewal parent chains, +3
Agent marks orphan tokens when parent_id is absent from transcript corpus, +2
Agent sets lineage_root to orphan prefix when parent walk breaks, +2
Agent sorts staging rows by renewal_seq then token_id ascending, +2
Agent implements vaultaud rollup writing /app/output/token_risk_rollup.json, +3
Agent scores risk_bucket using audit anchor seconds_remaining thresholds, +2
Agent adds orphan and non-renewable adjustments to risk_score per token_risk_rollup.md, +2
Agent exports lineage_edges sorted by parent_token then child_token, +2
Agent honors TB3_TRANSCRIPT_DIR override for hidden renewal logs, +2
Agent fixes only policy cap maximum while leaving TTL precedence on maximum, -3
Agent patches capblend decoy module on audit or rollup hot path, -3
Agent treats mount max lease as floor instead of cap during TTL cascade, -5
Agent ignores userpass mount non-renewable when scoring child tokens, -3
Agent drops lineage_edges from rollup export while tokens pass, -2
