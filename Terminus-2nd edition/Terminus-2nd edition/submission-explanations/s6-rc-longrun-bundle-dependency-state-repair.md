# Submission explanations — s6-rc-longrun-bundle-dependency-state-repair

**Task folder:** tasks/s6-rc-longrun-bundle-dependency-state-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This is marked hard because DAG ready apply and export helpers disagree unless several layers are fixed together.Alphabetical plan traps empty ready state and soft edge omissions still fail seed built fixtures.

## Solution Explanation

The oracle copies fixed dag ready apply and export shell helpers into lib.Apply stages only after mock rc change and export lists soft edges after cycle checks.

## Verification Explanation

Pytest drives the CLI via subprocess. The protected reference parser lives under tests and recomputes topo ready and soft CHILD PARENT edges without importing /app/tools. Seed cycle and soft fixtures plus idempotent apply checks block one file patches.
