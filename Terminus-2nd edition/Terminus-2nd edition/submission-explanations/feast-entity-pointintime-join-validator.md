# Submission explanations - feast-entity-pointintime-join-validator

**Task folder:** tasks/feast-entity-pointintime-join-validator/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-27T17:40:00Z

**Category note:** Zip metadata uses `machine-learning` (feature-store point-in-time join + online/offline parity eval). Choose **ML** on the platform form. Do not set data-processing, debugging, software-engineering, security, system-administration, or build-and-dependency-management.

> Agent scaffold only - rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Hard because feastctl must align point in time selection,inclusive TTL bounds,composite device keys,backfill partitions,duplicate seq ties,and rounded online offline parity while the baseline breaks those edges across packages.Held out packs plus TTL bias and a required global parity wipe stop constant tables and partial fixes from clearing the suite.

## Solution Explanation

The oracle replaces join,TTL,partition,compare,dedup,and export with inclusive point in time and TTL bounds,full composite key equality,active partition scoping,max seq dedup,rounded parity,and a canonical audit digest.Rebuild feastctl after the copies and keep the global parity table reset that validate join performs before insert.

## Verification Explanation

The verifier rebuilds feastctl then runs pytest on load validate and export against an independent reference from fixtures.Held out scenarios stage only at grade time and row level seed checks block empty joins while NOP scores zero and oracle scores one.
