# Submission explanations — typesense-typo-token-fuzzy-ranking-id-repair

**Task folder:** tasks/typesense-typo-token-fuzzy-ranking-id-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must repair a Rust typesense-search-cli control plane where NFC token dedupe, UTF-8 prefix scoring, docid tie-breaks, brand facet counting, staging snapshot ordering, and search pipeline wiring interact across six editable modules. The seeded image applies brand filtering before typo expansion, uses NFKC dedupe keys, char-count prefix ratios, insertion-order tie-breaks, facet counts over all documents, and writes the index before staging. Partial fixes that only patch prefix scoring or tie-break while leaving filter-rank order wrong still fail hidden traps where typo correction must surface filtered-brand documents and facet tallies must reflect only filtered hits.

## Solution Explanation

The oracle copies golden Rust sources for token_dedupe, prefix_score, tiebreak, counter, search_stage, and store, strips CRLF, rebuilds typesense-search-cli with cargo, and resets state. Search expands typo variants against the full vocabulary, ranks every document, applies docid tie-breaks, then retains brand-filtered hits and emits facet counts from that hit list. Ingest writes /app/state/index-staging.json with written_before_index true before saving /app/work/index.json.

## Verification Explanation

test.sh normalizes CRLF on shell and Python files, rebuilds the CLI, then runs pytest against reference_typesense_search.py. Tests invoke typesense-search-cli index and search via subprocess and compare hits, facets, staging fields, and token_index terms to the independent reference. Bundled fixtures cover typo tolerance, brand filtering, and unicode tokens; hidden fixtures cover filter-rank order, docid tie-break, facet counting, and NFC dedupe traps. Protected docs, fixtures, and decoy modules must remain unchanged. Oracle passes all tests after patching and rebuild. NOP on the seeded image scores zero.
