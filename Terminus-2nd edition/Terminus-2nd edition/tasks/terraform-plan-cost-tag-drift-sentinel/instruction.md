Implement the tf-tag-sentinel cost-tag drift analyzer on the working Bash and jq baseline under /app. The tf-tag-sentinel CLI at /app/bin/tf-tag-sentinel ingests Terraform plan JSON, writes a normalized staging snapshot, and audits that snapshot against FinOps tag policies to emit a structured violation report. Libraries under /app/lib implement plan parsing, moved-resource lineage, computed-unknown exemption, provider alias resolution, module tag inheritance, deny and waiver precedence, staging serialization, and report export.

Build tf-tag-sentinel by ensuring /app/bin/tf-tag-sentinel and /app/lib modules remain executable after edits. Subcommands and flags are defined in /app/docs/cli.md. Terraform plan field semantics, move actions, and unknown tag literals are in /app/docs/plan-semantics.md. Tag policy inheritance, deny rules, and waiver precedence are in /app/docs/tag-policy.md. Staging snapshot schema is in /app/docs/staging-format.md. Violation report fields and sorting rules are in /app/docs/violation-report-schema.md.

Your implementation must satisfy every contract above. The decoy helper at /app/lib/decoy/legacy_flatten.sh is not on the sentinel hot path. Policy reasoning combines provider alias scopes, module default inheritance, computed-unknown exemptions, and waiver-over-deny precedence. tf-tag-sentinel ingest must write /app/state/plan-tag.stage (or the --staging path) before tf-tag-sentinel audit reads that snapshot. tf-tag-sentinel audit must evaluate violations from the staging snapshot and policy digest recorded at ingest and must not re-read the raw plan JSON file.

Moved resources with a move action must inherit effective before tags from the previous address entry in the same plan when present. Tag values equal to the literal (known after apply) are unknown and must not produce missing-tag or drift-remove denials for that key. Waivers matching an exact resource address outrank module_prefix waivers. Valid waivers suppress deny violations only for their listed keys. Expired waivers use the evaluated_on date from policy config.

Public workflow:

  tf-tag-sentinel ingest --plan PLAN.json --policy /app/config/tag-policies.json --staging /app/state/plan-tag.stage
  tf-tag-sentinel audit --staging /app/state/plan-tag.stage --policy /app/config/tag-policies.json --out /app/output/tag-violations.json

Hidden verifier fixtures may supply alternate plan JSON under /opt/verifier-fixtures/tf-plans/ and mutated policy files under /opt/verifier-fixtures/tf-policies/. Alternate broken modules may appear under /opt/verifier-broken-sentinel/ for partial-path traps.

Do not edit /app/docs/, /app/fixtures/, /app/config/tag-policies.json, or /tests/.
