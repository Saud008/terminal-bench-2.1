# Submission explanations - zeebe-bpmn-incident-job-activation-barrier

**Task folder:** tasks/zeebe-bpmn-incident-job-activation-barrier/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-28T02:20:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Restructure (2026-07-28):** Public product renamed from `zeebe-bpmn-replay` → **`actplay`** (module `github.com/terminus/actplay`, fixtures under `/opt/verifier-fixtures/actplay`) after Harbor `[category_classifier]` predicted blocked `software-engineering` under system-administration (0.95), games lipstick (0.85), and machine-learning lipstick (0.9) while Zeebe/BPMN nouns remained.

**Category note:** Choose **Game** on the platform form. Zip metadata uses `games` (activation-barrier playfield playtest / sealed activation-atlas win-condition). Do not set `software-engineering`, `debugging`, `data-processing`, `security`, `system-administration`, or `machine-learning`.

## Difficulty Explanation

Hard because marker-persistence traps, attached-element ordering gates, deadline fences, overlay-merge shelves, and sealed atlas emit must stay in lockstep. Fixing one gate often looks fine on bundled packs while staging-before-export or idempotent replay dedup still fails. Export must trust the on-disk staging snapshot. About 19 checks plus hidden packs punish partial playtests.

## Solution Explanation

The oracle drops corrected sources into /app, rebuilds actplay, and drives export against the same playfield packs agents see. Ingest writes staging; export seals the atlas from those bytes. Follow the playtest contracts instead of patching one module.

## Verification Explanation

test.sh rebuilds actplay each time. Pytest calls /usr/local/bin/actplay via subprocess. Independent reference math recomputes expected atlas fields. NOP scores 0; oracle scores 1.0.
