# Diff export contract

xds-diff-report.json fields: scenario, change_count, changes[], report_digest.

Each change: path, change_type (added|removed|modified), optional left_value and right_value.

Route change paths use the /routes/{cluster} prefix. Examples include /routes/cc and /routes/cb for cluster identifiers in stable-diff-pair scenarios.

Changes sorted by path ascending.

emit-diff requires normalize_revision > 0.
