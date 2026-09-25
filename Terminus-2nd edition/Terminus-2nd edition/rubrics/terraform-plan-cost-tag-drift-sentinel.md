# Platform rubric — terraform-plan-cost-tag-drift-sentinel

**Task folder:** tasks/terraform-plan-cost-tag-drift-sentinel/

Agent ingests Terraform plan JSON into /app/state/plan-tag.stage with plan and policy digests, +3
Agent resolves provider_key through provider_aliases before deny rule matching, +3
Agent applies module_prefix defaults to child resource effective tags during ingest, +3
Agent merges moved resource before tags from previous_address when change.before is sparse, +3
Agent records unknown (known after apply) tag keys in unknown_keys_after without deny drift, +3
Agent audits violations from staging snapshot only without re-reading plan JSON, +3
Agent applies resource-specific waivers before module_prefix waivers for the same tag key, +2
Agent emits TAG_DRIFT_REMOVE when update actions drop tags present in effective_tags_before, +2
Agent sorts violation rows by resource tag_key and code lexicographically in export report, +2
Agent honors expired waiver dates using policy evaluated_on before suppressing denies, +2
Agent updates /app/state/run-registry.json with plan digest on each ingest run, +1
Agent leaves legacy_flatten decoy off tf-tag-sentinel ingest and audit hot paths, +1
Agent patches alias mapping only while module inheritance still injects cost_center defaults, -3
Agent fixes ingest staging but audit reopens raw plan JSON instead of staging snapshot, -3
Agent treats (known after apply) as a literal tag value and emits false drift denies, -2
Agent applies module_prefix waivers before exact resource waivers for the same key, -2
Agent skips TAG_DRIFT_REMOVE detection on moved update resources losing inherited tags, -2
