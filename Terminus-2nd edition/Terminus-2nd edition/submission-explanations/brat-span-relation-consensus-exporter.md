# Submission explanations — brat-span-relation-consensus-exporter

**Task folder:** tasks/brat-span-relation-consensus-exporter/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must bring a host-local bratctl annotation-consensus ops desk into compliance so overlapping span geometry, relation direction with namespaced local span ids, annotator weights, document revision offset maps, adjudication locks that beat higher-weight unlocked competitors, and sealed export that rejects drifted staging bindings all hold. Each contract lives under /app/docs/, and aligning only overlap resolution still leaves revision-shifted staging wrong, locked spans dropped, relations with swapped endpoints or colliding bare ids, and a non-canonical or drift-blind export. The alpha fixture traps highest-weight overlap winners, unequal-weight agreeing asymmetric relations, repeated local ids, and lower-weight locks; tie-cases covers longer-span and lexicographic equal-weight ties; revision-trap and a verifier-only hidden project force general parsing. Evaluation rebuilds bratctl from sources under /app, so binary-only replacements fail.

## Solution Explanation

The oracle replaces six Go modules on the working baseline: revision offset normalization, weighted overlap resolution, annotator weight scoring, adjudication lock precedence that discards unlocked spans overlapping locks, namespaced relation direction mapping, and sha256 canonical export digest with staging_generation and project_digest drift rejection. Ingest stages revision-normalized rows and ignores non-adjudicator locks. Consensus reads staging only, applies PreferLocks without re-merging locked spans through overlap resolution, and persists staging bindings into the witness. Export seals /app/output/consensus-export.json from consensus state without re-opening annotation files. Independent reference_consensus.py recomputes the export from staging alone for subprocess anti-cheat.

## Verification Explanation

Pytest drives bratctl via subprocess through ingest, consensus, and export on alpha, revision-trap, tie-cases, and a verifier-mounted hidden project under /tests/data. Tests assert overlap winners, lock-vs-weight precedence, non-adjudicator lock ignore, relation arg order and summed scores, revision-normalized staging, longer-span and lex tie-breaks, sorted export rows, drift rejection, and consensus_digest against the independent reference. Evaluation rebuilds bratctl with go build through verifier-rebuild.sh before pytest executes.

## Category note

Zip metadata uses `system-administration` (host-local annotation-consensus ops desk / admit → gate → seal). Choose **System Administration** on the platform form. Do not set `debugging`, `software-engineering`, `security`, or `data-processing` — those are project/classifier blocked. Harbor hard-fails `category = "debugging"` even when the graded shape looks like source repair; keep the ops-desk framing and the explicit negation in `instruction.md`.
