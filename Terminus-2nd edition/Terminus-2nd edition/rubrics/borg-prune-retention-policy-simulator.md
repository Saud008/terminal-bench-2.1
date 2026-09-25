# Platform rubric — borg-prune-retention-policy-simulator

**Task folder:** tasks/borg-prune-retention-policy-simulator/

Agent writes borg.stage.json beside dirname(list) not a global /app/state path, +3
Agent resolves duplicate archive_name lines by keeping the last file occurrence, +3
Agent clamps clock-skewed timestamps ahead of reference_now plus clock_skew_sec for buckets, +3
Agent applies legal prefix holds only when archive name starts with the prefix string, +3
Agent uses policy week_start monday for weekly bucket boundaries not sunday-only math, +3
Agent sums compaction_bytes_reclaimable from pruned archives only not kept archives, +3
Agent unions retention bucket survivors with legal holds before forming kept_archives, +2
Agent emits export JSON with sorted keys compact separators and trailing newline, +2
Agent requires evaluate to populate staging evaluation before export runs, +2
Agent drives subprocess CLI for every test case via independent reference_retention oracle, +2
Agent patches only export.sh while leaving ingest staging path and list parsing broken, -3
Agent keeps first duplicate list line instead of last occurrence winner semantics, -3
Agent matches legal prefix holds with substring anywhere in archive name, -3
Agent writes staging snapshot to /app/state/borg.stage.json for all list paths, -5
Agent skips clock-skew normalization and undercounts clock_skew_adjustment_count, -3
Agent computes weekly buckets with sunday start when policy week_start is monday, -2
