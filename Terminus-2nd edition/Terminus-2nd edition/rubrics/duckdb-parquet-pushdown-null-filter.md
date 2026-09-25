# Platform rubric — duckdb-parquet-pushdown-null-filter

**Task folder:** tasks/duckdb-parquet-pushdown-null-filter/
**Upload:** paste Agent criterion lines below into the platform rubric form (no milestone header; non-milestone flat list).

Agent honors null_count_omitted stats before pruning row groups for IS NULL pushdown, +3
Agent reads dictionary and null_bitmap pages in canonical order per column page_order, +3
Agent evaluates timestamp row-group stats without treating omitted null_count as zero, +3
Agent parses ts_gte bounds in UTC when catalog_tz is UTC regardless of process TZ, +3
Agent splits row groups into worker slices using catalog chunk_size and worker count, +3
Agent writes /app/state/pushdown-plan.json with selected_row_groups before filter output, +3
Agent rebuilds parquet-pushdown-scan after editing internal pushdown modules, +2
Agent matches independent reference matched_row_ids for merged predicate catalogs, +2
Agent ignores decoy ledger wrap helper on the export hot path, +1
Agent fixes only planner pruning while dictionary page decode stays broken, -3
Agent fixes page reader alone without null_count_omitted planner guard, -3
Agent applies timestamp bounds in local timezone when catalog_tz is UTC, -3
Agent emits filter output before staging plan is written to disk, -2
