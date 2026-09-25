# Submission explanations — inv-task-full

**Task folder:** tasks/inv-task-full/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a multi-stage Ansible inventory vault auditor where scan ingest precedence, ignore filters, vault marker parsing, and staging digest math all interact. Fixing only emit export while leaving group lineage or ignore patterns wrong still fails hidden trees under extra verifier fixture directories. Partial patches to one flag constant in inventory_engine.py leave nested vault and ignore bypass traps failing while bundled trees look almost correct.

## Solution Explanation

The oracle replaces inventory_engine.py with corrected CHILDREN_FIRST, HOST_BEFORE_GROUPS, USE_INVENTORY_IGNORE, DIGEST_FINDINGS, and EXPORT_REOPEN flags plus whitespace-aware vault detection. Scan writes host-rows.ndjson, exposure-rows.ndjson, and scan-manifest.json. Emit reloads those artifacts only and renders vault-exposure-report.json without reopening inventory paths.

## Verification Explanation

Pytest drives inv-vault-audit through subprocess CLI calls and compares outputs to vault_audit_oracle.py reference snapshots. Tests cover bundled fixture trees, hidden verifier trees, staging digest contracts, run_seq stability, partial emit reopen traps, and broken digest traps. test.sh rebuilds the CLI before pytest and writes Harbor reward from pytest exit code.
