# Submission explanations — caddy-http-route-matcher-simulator

**Task folder:** tasks/caddy-http-route-matcher-simulator/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement caddyctl offline route matching on a partial Go baseline without a live Caddy server. The work spans ingest staging, matcher simulation, and export, with rules split across matcher-specificity-order.md, path-regexp-anchors.md, and header-case-contract.md. Fixing only regexp anchoring or header folding leaves bundled GET passing while method plus header combos and nested handle_path routes still fail. Export must use stable handler ids from the staging ledger, not array indices. Hidden overlap fixtures under /opt/verifier-fixtures require specificity tie-breaks that broad prefix routes miss.

## Solution Explanation

The oracle copies corrected staging, match, and export modules into /app and rebuilds caddyctl. Ingest must flatten nested routes into /app/state/route-stage.json before match reads that snapshot. Match applies most-specific-wins ordering, anchored path_regexp, header value folding, and terminal isolation. Export resolves handlers only through the handler_map keyed by @id. The key insight is that staging shape and matcher semantics are independent layers that must agree before export can be trusted.

## Verification Explanation

test.sh seeds the reward file, rebuilds the Go binary, and runs 25 pytest cases via subprocess on /app/bin/caddyctl. Tests include an independent reference matcher that recomputes winners from fixtures instead of golden files. Cases assert both /app/state/route-stage.json and /app/output/handler.json paths. Hidden probes use /opt/verifier-fixtures with overlapping matchers. The broken baseline fails most behavioral tests. After the oracle patches and rebuild, the full suite passes with reward 1.
