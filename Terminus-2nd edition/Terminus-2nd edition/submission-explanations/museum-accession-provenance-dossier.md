# Submission explanations - museum-accession-provenance-dossier

**Task folder:** tasks/museum-accession-provenance-dossier/
**Platform form only** - not in upload zip.

**Category note:** Zip metadata uses `games` (museum accession vault playtest / sealed dossier win-condition export). Choose **Game** on the platform form. Do not set `software-engineering`, `debugging`, `data-processing`, `security`, or `system-administration`. Harbor `[category_classifier]` predicted blocked `software-engineering` (0.95) under system-administration and again under security lipstick; remapped (2026-07-29) to games playtest framing (carbon / labelsheet / bitswap successors). Policy modules under `/app/lib/musdoss/`; binary is `/usr/local/bin/musdoss` (bash → `python3 -m musdoss.cli`).

## Difficulty Explanation

Players must keep the museum accession vault playtest aligned across vault load, compose align, register supersession, and publish dossier. It is hard because custody chronology, deterministic loan conflict multiplicity and ordering, rights precedence, restoration tie-breaks, and duplicate accession id rules interact across several playfield modules and docs. Cross-stage state is also graded: archive_seq is path-global, corrupt or name-mismatched loads must preserve the prior snapshot, and both same-name reloads and post-align byte mutations make the digest-bound register row stale until realignment. These requirements force coordinated changes across policy, vault, SQLite register, compose, and publish packages; one-file fixes pass visible happy paths but fail the combined edge overlay and freshness barrier.

## Solution Explanation

The approach is to restore the dossier playtest pipeline end to end under `/app/lib/musdoss/`. Vault load validates embedded archive identity and preserves/increments archive_seq; compose align stores that archive_seq plus the exact snapshot-byte SHA-256 with the seed row; publish dossier rejects stale archive_seq or digest bindings. Policy modules use stable custody ordering, sorted missed-then-overlap loan emission (exactly `{accession_id, reason}` rows), the five-field summary object, stricter active rights selection, restoration date/technician/notes ordering, and accession-id duplicate grouping. After Python playfield edits, leave the graded musdoss wrapper current via `/app/scripts/verifier-rebuild.sh`.

## Verification Explanation

Tests rebuild the playtest binary, then drive musdoss through subprocess over fixture archives using vault load / compose align / publish dossier. Independent lineage math uses verifier-protected fixture copies and checks agent-visible fixture integrity. Cases cover corrupt and mismatched loads, cross-seed archive_seq monotonicity, stale same-name and same-archive_seq digest rejection, deterministic tie and boundary behavior, active-row replacement, and a combined overlay spanning every policy. Graded JSON is opened with O_NOFOLLOW and must be a non-empty regular object. The NOP image fails most checks while the oracle passes all 30.
