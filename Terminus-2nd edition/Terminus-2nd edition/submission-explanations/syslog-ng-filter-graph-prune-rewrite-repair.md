# Submission explanations — syslog-ng-filter-graph-prune-rewrite-repair

**Task folder:** tasks/syslog-ng-filter-graph-prune-rewrite-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked hard because the syslogctl replay driver chains five interacting Bash modules whose contracts are split across /app/docs/filter-graph.md, boolean-precedence.md, rewrite-order.md, branch-fallback.md, and reload-cache.md. A single-file fix rarely survives: wrong boolean parsing misroutes dest_ops and dest_group, pruning drops rewrite-referenced dead routes, and branch.sh can strip fallback routes that must stay active. Replay order matters too—rewrites run before the facility gate in the broken baseline, so dropped messages still get rewrite_applied counts wrong. Partial reload must compare config hashes, not blindly reuse cache files, which only shows up after editing filters and graph.conf mid-run. Hidden configs under /tests/hidden_configs prevent hard-coded delivery JSON from passing bundled fixtures alone.

## Solution Explanation

The oracle replaces five library scripts under /app/lib with golden implementations: boolean.sh parses facility, level, and program atoms with correct AND-over-OR precedence and parenthesis handling; prune.sh retains dead routes referenced by rewrites.conf and honors fallback flags; branch.sh passes the pruned graph through without dropping fallback dead branches; cache.sh rebuilds the pruned graph whenever partial reload sees a hash change; replay.sh applies facility gate filtering before rewrite templates, then evaluates active routes. solve.sh copies those golden files, resets state, and leaves syslogctl to write routing-snapshot.json and the export report per report-schema.md. The key insight is that graph load, cache invalidation, message preprocessing, and route evaluation are separate stages that must agree on the same active_routes set.

## Verification Explanation

Pytest runs ten behavioral cases that shell out to /app/bin/syslogctl replay with fresh export paths and reset-state.sh between runs where needed. An independent reference_syslog module recomputes delivery reports and routing snapshots from the same config and message inputs, so agents cannot pass by echoing fixture JSON. Tests cover base and alt fixtures, facility-gate ordering, prune and fallback retention, partial reload after config edits, boolean precedence without extra parentheses, byte-identical determinism for repeated seeds, and a hidden config/message pair outside bundled trees. Assertions compare full report objects and active_routes lists, not single counter fields.
