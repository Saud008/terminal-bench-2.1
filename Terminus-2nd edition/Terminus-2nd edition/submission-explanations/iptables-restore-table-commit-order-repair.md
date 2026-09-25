# Submission explanations — iptables-restore-table-commit-order-repair

**Task folder:** tasks/iptables-restore-table-commit-order-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

Agents must align ten Bash libraries under /app/lib/ with seven contract documents that split parsing, kernel table commit order, phase configuration, staging digests, and snapshot-only export. The iptctl CLI simulates multi-table iptables-restore through ingest then export, and fixing one module is rarely enough: wrong commit order in commit.sh breaks mangle-to-nat mark activation even when parse.sh looks correct, and a working ingest path still fails if export.sh re-parses restore files instead of frozen phase_config. Verifier seeds deterministically shuffle only -A lines within each table block, so agents must separate per-table stable rule ids from the global rules index in the export schema. Export guard checks plan_digest and merge-staging sibling digests, and partial-fix traps prove that policy counter mode, rule counter mode, conntrack ordering mode, and mark linkage mode must all be wired consistently across phase modules and staging.sh.

## Solution Explanation

The oracle copies ten golden Bash modules from solution into /app/lib/, normalizes line endings, and runs reset-state.sh. parse.sh materializes restore tables; commit.sh, policy.sh, counters.sh, deps.sh, and match.sh resolve frozen phase_config during ingest; bind.sh computes plan_digest and staging.sh writes the merge-staging sibling with aligned digests. guard.sh validates binding and merge-staging presence before export, and export.sh simulates from the snapshot alone using the frozen tables and phase_config. Kernel commit order is mangle then nat then filter regardless of file block order, seed shuffle keys use per-table rule indices, and NAT mark rules activate only after matching mangle MARK rules are committed. Missing restore files exit 2; guard or digest failures exit 4 without writing a report.

## Verification Explanation

Pytest runs after test.sh resets /app state and invokes iptctl through subprocess for simulate, ingest, and export. Every catalog restore in /app/fixtures/seeds.json is crossed with all verifier seeds and compared to reference_ipt.py, an independent Python reimplementation that does not import /app/lib/. Tests assert process exit codes match export exit_code, full JSON report equality, staging schema fields, ingest-then-export chaining, and fixture byte immutability. Golden-ingest plus broken-export traps catch export paths that read live modules or re-parse restores, while guard tests reject missing merge-staging siblings or tampered plan_digest values. Hidden runtime restores with reversed table blocks verify kernel commit order for cross-table mark visibility, and per-module broken_* trap injections confirm that a single patched module still fails the relevant behavioral probe.
