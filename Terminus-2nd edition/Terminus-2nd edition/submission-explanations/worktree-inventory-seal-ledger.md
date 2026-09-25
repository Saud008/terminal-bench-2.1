# Submission explanations - worktree-inventory-seal-ledger

**Task folder:** tasks/worktree-inventory-seal-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-19T15:55:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses system-administration for the host-local worktree inventory seal ledger.Do not set software-engineering debugging or data-processing on the platform form.

## Difficulty Explanation

This task is marked hard because inventory admission and score gates span several library modules and catalog scenarios so a partial change looks fine on one stream while rename or unmerged holds still fail elsewhere.

## Solution Explanation

The oracle installs golden admission and gate libraries then exercises the inventory control plane CLI on the same catalog fixtures agents see.Key insight is follow the ops contracts for NUL admission score gates and gitlink holds instead of hard coding one scenario.

## Verification Explanation

Pytest drives the CLI via subprocess and recomputes expected JSON from an independent reference so pasted goldens cannot pass.NOP on the baseline should score zero and the oracle libraries should clear the suite.
