# Risk report schema

Output path: /app/output/hosts-atlas-report.json

hosts-atlas-report.json fields:

- schema_version: always 1
- tree_id
- staging_digest
- run_seq
- summary: counts for critical, high, medium, low
- findings: sorted by category, host, var_key
- group_lineage: host to groups array
- merge_order: from staging

Finding categories: vault_exposure, plaintext_secret, precedence_shadow, ignored_file_leak.

Severity mapping is defined in /app/config/severity-weights.json.
