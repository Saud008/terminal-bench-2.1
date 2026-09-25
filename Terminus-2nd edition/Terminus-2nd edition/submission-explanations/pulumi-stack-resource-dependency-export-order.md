# Submission explanations — pulumi-stack-resource-dependency-export-order

**Task folder:** tasks/pulumi-stack-resource-dependency-export-order/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a six stage Go pipeline where snapshot validation, graph adjacency construction, ledger epoch persistence, Kahn topological ordering, and ledger backed export serialization each carry independent policy bugs. Fixing only graph build or only topological sort still fails merged catalog cases and hidden nested component delete before replace traps mounted under verifier fixtures. Cross run epoch monotonicity and adjacency digest fields punish export only patches that bypass staging. Documentation spreads edge rules, ledger schema, and epoch contracts across eight cited files without a single file recipe.

## Solution Explanation

The oracle copies golden modules into internal validate, ingest, graph build, graph topo, graph ledger, export serialize, and replay order packages then rebuilds the CLI. Graph build stops flattening component parents and emits prerequisite to dependent edges for dependencies, parents, providers, and delete before replace pairs. Topological sort tie breaks on snapshot index and enforces adjacent old new placement. Ledger write increments epoch and hashes canonical adjacency. Export loads ledger rows for ordering. Replay calls validation before staging.

## Verification Explanation

Pytest drives an independent Python reference graph that rebuilds adjacency and order from snapshot JSON and compares CLI stdout files via subprocess. Partial module swaps prove single layer fixes fail while hidden fixture stacks under opt verifier fixtures test different failure profiles than bundled catalogs. Tests cover ledger epoch bumps, validation exit codes, decoy wrap isolation, and instruction named output paths. test.sh rebuilds Go before pytest and writes Harbor reward files.
