# Submission explanations — kong-route-plugin-precedence-chain-repair

**Task folder:** tasks/kong-route-plugin-precedence-chain-repair/
**Platform form only** — not in upload zip.
**Zip:** `tasksubmit/kong-route-plugin-precedence-chain-repair.zip`

**Category note:** Zip metadata uses `security` (JWT and plugin-precedence admission security control plane / scope trust gates / route authenticity / sealed OpenAPI attestation). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior upload failed Harbor `[category_classifier]` as blocked `software-engineering` when the prompt read as API-gateway engineering; keep the authorization / attestation framing.

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Rated **medium** in zip metadata (`task.toml`). Measured agent pass rates sit in the medium band: agents often land bundled ingest, matching, and JWT cases but miss hidden route matrices, additive response-transformer merge in OpenAPI staging, or rate-limit header suppression at the authorization boundary. Agents must align a Go API-gateway admission plane with security contracts spread across ingest integrity, route authenticity, plugin-precedence trust gates, JWT scope checks, and sealed OpenAPI export. Longest-prefix authenticity with a method gate at that prefix and atomic ingest that clears prior deck state on failure are common trip points; scope field renames on JWT modules can surface from compiler errors and are somewhat easier to recover.

## Solution Explanation

The oracle installs corrected authorization modules for ingest, match, merge, chain, jwt, and openapi into `/app/internal/`, then rebuilds kongadmit. Ingest validates before any store write and always reports routes_loaded zero on failure. Matching picks the longest path prefix then requires a method match at that length without falling back. Merge combines response-transformer header lists from service and route levels. JWT checks scope_tags only. Rate-limit refusals suppress response-transformer headers.

## Verification Explanation

Pytest modules `test_m1.py`, `test_m2.py`, and `test_m3.py` each run against a rebuilt binary started as a local daemon. Tests ingest decks through the admin API and call the proxy with subprocess HTTP clients. Reference helpers recompute expected route matches and plugin chain headers independently from fixtures. Hidden decks are generated per seed so agents cannot hardcode paths. Oracle must pass all verifier modules while NOP stays at zero on the broken baseline.
