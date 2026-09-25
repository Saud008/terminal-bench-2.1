# Playtest atlas

Default sealed path: /app/output/geo-filter-playtest-atlas.json
(override with seal-atlas --output).

Seal-atlas copies the round score and adds:
- atlas_digest — SHA-256 of audit payload
- focus_docs — echoed from roster

Audit payload: for each admitted row ordered by ascending admit_rank, append
doc_id:affinity_fixed newline where affinity_fixed uses TB3_PLAY_DIGITS digits.
