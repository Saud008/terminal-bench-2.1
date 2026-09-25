# Platform rubric — typesense-typo-token-fuzzy-ranking

**Task folder:** tasks/typesense-typo-token-fuzzy-ranking/
**Written:** 2026-06-25T16:32:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent applies brand filter before typo expansion and ranking, +3
Agent deduplicates index tokens with NFC normalization per token-dedupe contract, +3
Agent scores prefix matches using UTF-8 byte lengths not char counts, +2
Agent tie-breaks equal scores with ascending docid not insertion order, +3
Agent counts facet brands only on documents passing the active filter, +3
Agent writes index-staging.json before persisting /app/work/index.json, +2
Agent rebuilds typesense-search-cli with cargo before export search runs, +2
Agent respects TB3_TYPO_DISTANCE when expanding typo query tokens, +2
Agent ignores typo_wrap decoy module on the search hot path, +1
Agent hardcodes search JSON without running typesense-search-cli search, -3
Agent patches prefix scoring only while filter-rank order stays wrong, -2
Agent merges circled unicode and ASCII a into one index term, -3
Agent ranks higher docid ahead on equal scores, -2
Agent includes filtered-out brands in facet tallies, -2
