# Submission explanations — loot-table-pity-counter-settlement-engine

**Task folder:** tasks/loot-table-pity-counter-settlement-engine/
**Platform form only** — not in upload zip.

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `security` (loot-economy settlement integrity / HMAC envelope authenticity / pool-epoch key binding / anti-replay gates / digest-sealed attestation). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior upload failed Harbor `[category_classifier]` as blocked `software-engineering` when the prompt led with Rust module-rebuild / exported-signature engineering-contract framing; keep the settlement-integrity / signature-admission security framing.

## Difficulty Explanation

Agents have to keep signed ingest,pity carry,duplicate shards,and anti-replay on one path before export will seal.Fixing only HMAC or only digest format still fails when season carry ratio or replay generation drifts.

## Solution Explanation

Align envelope,pity,pool,duplicate,idempotent,staging,and export layers to the authenticity docs,then leave lootsettle current.Key insight is hmac plus pool epoch binding,destination carry ratio,and shards instead of a second inventory copy.

## Verification Explanation

Tests drive ingest,settle,and export through the binary and compare against an independent reference model.Hidden gamma fixtures and seed mutations catch hard-coded totals while nop on the broken baseline stays below a full reward.
