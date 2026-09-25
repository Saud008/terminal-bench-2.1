# VolumeSnapshot retention report contract

volsnap-audit-report.json fields: scenario, protected_count, deletable_snapshot_uids[], quota_violations[], report_digest.

deletable_snapshot_uids sorted lexicographically ascending.

Empty deletable_snapshot_uids and quota_violations emit JSON `[]`, never null.

publish-audit requires audit_pass_seq greater than zero.

report_digest is SHA-256 hex of compact JSON (separators `,` and `:`) over keys deletable_snapshot_uids, protected_count, quota_violations, and scenario. The sealed scenario value is always the empty string `""`, not the published scenario field on the report.
