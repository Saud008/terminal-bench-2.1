# Submission explanations — terraform-plan-cost-tag-drift-sentinel

**Task folder:** tasks/terraform-plan-cost-tag-drift-sentinel/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task asks agents to implement the tf-tag-sentinel Bash and jq pipeline that ingests Terraform show JSON, normalizes tag state into a staging snapshot, and exports a structured violation report against FinOps tag policies. Contracts span moved-resource lineage, computed-unknown exemptions, provider alias scopes, module default inheritance, deny rules, waiver precedence, and audit isolation from the raw plan file. The instruction cites five docs under /app/docs and requires audit to evaluate only /app/state/plan-tag.stage. Partial fixes pass simple creates but fail when move actions need previous_address tag merge, aws.east alias mapping, module.network defaults, bastion waivers, expired waiver dates, azurerm dual-key denies, and TB3 seeded plans with random addresses. Interactions between ingest normalization and export-only policy reasoning mean patching one lib module leaves staging correct but violations wrong or vice versa.

## Solution Explanation

The oracle copies golden Bash modules from solution patches into /app/lib and lib/export. Stage one tf-tag-sentinel ingest writes /app/state/plan-tag.stage with effective before and after tag maps, unknown key lists, provider scopes, and digests. Stage two tf-tag-sentinel audit reads that snapshot only, evaluates deny and waiver precedence, and writes /app/output/tag-violations.json with sorted rows and summary counts. Key insight is moved updates must inherit sparse before tags from the previous address entry, unknown after values must exempt both missing-tag and drift-remove checks, and valid waivers suppress denies only for their listed canonical keys without reopening the plan JSON during audit.

## Verification Explanation

test.sh runs pytest against tf-tag-sentinel via subprocess with an independent reference_sentinel.py oracle. Tests cover ingest staging equality, audit staging-only behavior, export report paths, move drift, unknown exemptions, waiver and expiry cases, TB3 hidden fixtures under /opt/verifier-fixtures, and partial module traps swapping broken copies from /opt/verifier-broken-sentinel. Default cli.md paths /app/state/plan-tag.stage and /app/output/tag-violations.json are exercised explicitly. Oracle patches nine golden lib modules plus export emit. NOP on the shipped broken baseline scores zero.
