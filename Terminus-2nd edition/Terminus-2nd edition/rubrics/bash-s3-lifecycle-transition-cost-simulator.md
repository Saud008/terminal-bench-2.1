# Platform rubric — bash-s3-lifecycle-transition-cost-simulator

**Task folder:** tasks/bash-s3-lifecycle-transition-cost-simulator/

Agent implements s3lc ingest writing staging JSON with inventory_fingerprint and object rows, +3
Agent deduplicates inventory version_id rows keeping last line per docs, +2
Agent marks current_version and noncurrent_since from greatest last_modified per key, +3
Agent picks highest lifecycle rule priority with tag_prefix key matching, +3
Agent applies storage-class transitions when age meets inclusive day thresholds, +3
Agent suppresses transitions and expiration when any version has legal_hold or retention_until, +3
Agent expires noncurrent versions under delete-marker current version per debug-short rule, +2
Agent bills incomplete multipart uploads separately in multipart_pending_usd, +2
Agent prorates monthly GB-month charges using actual window days over calendar month length, +3
Agent sorts cost report storage classes lexicographically and seals report_digest, +2
Agent honors TB3_INVENTORY_FILE TB3_RULES_FILE and TB3_HOLDS_FILE override paths, +2
Agent patches only tag_matcher while leaving rule precedence selecting lowest priority, -3
Agent wires decoy storage_class_sorter into lifecycle_simulator hot path, -3
Agent evaluates legal_hold on current version only ignoring sibling versions, -5
Agent uses strict greater-than for transition day thresholds excluding boundary day, -3
Agent hardcodes monthly proration to thirty days ignoring June window length, -2
