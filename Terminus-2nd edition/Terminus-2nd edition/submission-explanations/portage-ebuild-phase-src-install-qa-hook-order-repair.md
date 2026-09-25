# Submission explanations - portage-ebuild-phase-src-install-qa-hook-order-repair

**Task folder:** tasks/portage-ebuild-phase-src-install-qa-hook-order-repair/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-19T16:47:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is marked hard because install order QA setuid survival and merge ledger rules span several bash libraries so a partial patch can look fine on public fixtures while full runs still swallow die or write bad ledger rows.

## Solution Explanation

The oracle replaces broken phase libraries then the driver follows contract docs so normalize runs before QA fperms beat dosbin and full runs write a merged record only after a clean test.

## Verification Explanation

Pytest drives the phase CLI via subprocess and recomputes expected trace and ledger status from an independent reference so pasted goldens cannot pass.
