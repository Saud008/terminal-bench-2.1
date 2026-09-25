Implement the Borg prune retention policy simulator at /app/bin/borg-prune-sim: a three-stage workflow that ingests tab-separated borg list fixtures, evaluates retention buckets with legal holds and clock-skew normalization into a staging snapshot beside the list file, and exports a dry-run prune report with compaction estimates. Wire ingest, evaluate, and export to match /app/docs/list-format.md, /app/docs/staging-format.md, /app/docs/retention-buckets.md, /app/docs/legal-holds.md, /app/docs/clock-skew.md, and /app/docs/export-format.md.

For any --list path, the staging snapshot is always dirname(list)/borg.stage.json. Example: --list /app/fixtures/seed/repo.list writes /app/fixtures/seed/borg.stage.json. Export refuses to run until evaluate has populated the evaluation block in that staging file.

List ingest rules: fields are tab-separated archive_name, utc_timestamp, original_size_bytes, segment_count per /app/docs/list-format.md. Lines beginning with # and blank lines are ignored. When the same archive_name appears on multiple lines, the last line in file order wins.

Clock skew: when an archive timestamp is strictly greater than reference_now plus clock_skew_sec from the policy, normalize that archive to reference_now for bucket assignment only and count it in clock_skew_adjustment_count. See /app/docs/clock-skew.md.

Legal holds: exact names and prefix rules in the holds JSON are never pruned. Prefix patterns match only when the archive name starts with the prefix string.

Retention buckets: after duplicate resolution and clock-skew normalization, apply daily, weekly, monthly, and yearly keep counts from the policy. Weekly bucket boundaries follow week_start in the policy (monday or sunday). Union bucket survivors with legal holds forms kept_archives; all other archives are pruned.

Export report fields: kept_archives and pruned_archives are sorted lexicographically. compaction_bytes_reclaimable and compaction_segments_reclaimable sum original_size_bytes and segment_count for pruned archives only. JSON keys are sorted with compact separators and a trailing newline.

Example workflow:

/app/bin/borg-prune-sim ingest --list /app/fixtures/seed/repo.list --repo-id main
/app/bin/borg-prune-sim evaluate --list /app/fixtures/seed/repo.list --policy /app/policy/default.json --holds /app/holds/empty.json --now 2024-07-01T00:00:00Z
/app/bin/borg-prune-sim export --list /app/fixtures/seed/repo.list --out /app/output/prune-report.json
