# tf-tag-sentinel CLI

Binary: /app/bin/tf-tag-sentinel

## ingest

```
tf-tag-sentinel ingest --plan PLAN.json --policy POLICY.json --staging STAGING.json
```

Reads the Terraform plan JSON and tag policy file. Normalizes resource changes, resolves moved lineage, provider aliases, module inheritance, and unknown tag keys. Writes the staging snapshot to STAGING.json and updates /app/state/run-registry.json with the plan digest.

Exit codes:
- 0 on success
- 1 when --plan or --policy is missing or unreadable
- 2 when plan JSON has no resource_changes array

## audit

```
tf-tag-sentinel audit --staging STAGING.json --policy POLICY.json --out REPORT.json
```

Reads only the staging snapshot and policy file. Evaluates deny rules and waivers. Writes the violation report to REPORT.json.

Exit codes:
- 0 when deny_count is zero
- 1 when staging or policy is missing
- 2 when deny_count is greater than zero

## run

Convenience wrapper that runs ingest then audit with the same paths.

```
tf-tag-sentinel run --plan PLAN.json --policy POLICY.json --staging STAGING.json --out REPORT.json
```

Exit code matches audit.
