# Submission explanations - scene-uid-admission-seal-ledger

**Task folder:** tasks/scene-uid-admission-seal-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-19T17:00:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses system-administration for the host-local scene UID admission seal ledger. Do not set software-engineering, debugging, or data-processing on the platform form.

## Difficulty Explanation

This task is marked hard because UID-admission overlays, packed-scene conflict gates, graph-cycle barriers, orphan reporting, and LF ledger checksums span several modules and scene packs so a partial change looks fine on village-remap while cycle-trap or orphan-trap still fails elsewhere.

## Solution Explanation

The oracle installs golden overlay conflict graph ledger and orphan libraries then exercises scenectl apply on the same scene-pack fixtures agents see. Key insight is follow the ops contracts for seed overlay formula caller-resolved base and LF normalization instead of hard coding one village pack.

## Verification Explanation

Pytest drives the CLI via subprocess and recomputes expected JSON from an independent reference so pasted goldens cannot pass. NOP on the baseline should score zero and the oracle libraries should clear the suite.
