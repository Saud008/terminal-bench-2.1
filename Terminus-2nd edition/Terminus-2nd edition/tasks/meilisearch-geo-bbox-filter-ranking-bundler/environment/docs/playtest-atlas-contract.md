# Playtest atlas

Default sealed path: /app/output/geo-filter-playtest-atlas.json
(override with seal-atlas --output).

Seal-atlas always publishes from the current round-score ledger. A successful
seal is required even when admitted is empty and every document is denied
(admitted_count == 0). Do not gate the write or exit status on a non-empty
admitted set.

Seal-atlas copies the round score and adds:
- atlas_digest — SHA-256 of audit payload
- focus_docs — echoed from roster

Audit payload: for each admitted row ordered by ascending admit_rank, append
doc_id:affinity_fixed newline where affinity_fixed uses TB3_PLAY_DIGITS digits.
When admitted is empty, the payload is the empty string and atlas_digest is the
SHA-256 of that empty payload.

On success, seal-atlas must exit 0 and leave a non-empty JSON file at the
chosen output path. Missing required flags or unknown arguments exit 2.
