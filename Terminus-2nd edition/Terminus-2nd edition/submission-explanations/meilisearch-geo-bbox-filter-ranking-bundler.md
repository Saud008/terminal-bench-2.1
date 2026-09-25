# Submission explanations — meilisearch-geo-bbox-filter-ranking-bundler

**Task folder:** tasks/meilisearch-geo-bbox-filter-ranking-bundler/
**Platform form only** — not in upload zip.

**Category note:** Choose games on the platform form. Zip metadata uses games for map window playfield playtest simulation, level pack scoring, and playtest atlas win condition sealing. Do not use software-engineering, debugging, or data-processing in task.toml.

## Difficulty Explanation

This one is hard because the playfield is a Bash pipeline under the mbx7 stages, not a single script, and load-level, score-round, and seal-atlas all have to agree on the same rulecard math. Agents often fix window scoring or pin salting in isolation and still miss replica lag caps, floor quorum, or affinity tie-breaks, so the sealed atlas digest and deny set diverge from the authority. Inclusive lon and lat corners and document-kind pin filtering are easy to get almost right, and a lon/lat axis swap or a shard_marker treated like a real pin will still pass a loose paris-core glance. seal-atlas must still write and exit 0 on all-denied rounds, so gating publication on a non-empty admitted set fails lag-shard and floor-starve. The scout_decoy sits next to the real stages and pulls people off the load, score, and seal path. Partial rulecard edits therefore keep failing the hidden axis, inclusive, and pin-kind overlays even when the primary level seems green.

## Solution Explanation

The fix is to align the wrap, pin, rect, lag, floor, rank, tally, and emit stages on the playtest rulecard docs so the three geoboxplay verbs share one playfield path. Load-level must bump load_seq and salt filter pins when packing the roster, and pin rejection must apply only to document-kind rows with real pins. Score-round has to gate on inclusive windows, then lag, then floor quorum, then rank by descending affinity with ascending doc_id and the admit cap, always writing the ledger even when every document is denied. Seal-atlas hashes affinity lines at TB3_PLAY_DIGITS precision and always writes the playtest atlas from that ledger, exiting 0 even when admitted_count is 0. Leave scout_decoy alone and rebuild geoboxplay after the stage edits.

## Verification Explanation

Tests drive geoboxplay through load-level, score-round, and seal-atlas, including the synonym verbs, against bundled levels and hidden overlays. An independent Python authority recomputes admitted sets, deny reasons, and atlas digests so a hard-coded JSON blob cannot pass. Paris-core checks the full happy path, while axis-trap, inclusive-trap, and pin-kind-trap catch swapped coordinates, exact corner admission, and marker-kind pin mistakes. Extra cases cover load_seq growth, pin salt, TB3_PLAY_DIGITS digest shifts, and TB3_LEVEL_DIR overlay roots. NOP on the broken baseline stays below a full reward, and the oracle stage patches are what clear the suite.
