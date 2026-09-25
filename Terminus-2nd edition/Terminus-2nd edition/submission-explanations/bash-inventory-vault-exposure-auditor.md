# Submission explanations - bash-inventory-vault-exposure-auditor

**Task folder:** tasks/bash-inventory-vault-exposure-auditor/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-28T17:45:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `games` (host-atlas layer-stack playtest / sealed atlas win-condition). Choose **Game** on the platform form. Do not set `machine-learning`, `security`, `software-engineering`, `debugging`, `data-processing`, or `system-administration`. Classifier history: `security` ↔ `software-engineering` under Ansible-inventory nouns; ML lipstick still predicted blocked `software-engineering` (0.9 then 0.95) while instruction/negation named inventory/Ansible paths. Remapped to games playtest framing (bitswap / geoboxplay / actplay shape) after public rename to `hostsatlas`. Keep playtest/win-condition language and the explicit “not a software-engineering / debugging / ML eval lab” negation — do not name Ansible/inventory/vault in `instruction.md`.

## Difficulty Explanation

This task is about implement the hostsatlas host-atlas playtest. I rated it hard because the behavior is split across docs and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and replay counters and commit files have to stay in sync across two CLI runs. With about 40 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected policy modules into /app, rebuilds hostsatlas, and exercises the CLI against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. A second run on unchanged inputs should stay idempotent.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest calls /usr/local/bin/hostsatlas via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math so expected JSON and side files are recomputed from fixtures. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
