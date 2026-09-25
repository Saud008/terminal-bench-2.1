# Filter and rank order

Search pipeline order:

1. Parse query tokens.
2. Expand typo variants against the full vocabulary.
3. Score every document using expanded tokens (exact, typo, prefix rules).
4. Apply stable docid tie-break on equal scores.
5. Retain only hits whose documents pass the brand filter.
6. Emit facet brand counts for filtered hits only.

Ranking the full corpus before filtering is required so typo correction can surface documents that would be dropped if brand filtering ran first. Facet counts must reflect the filtered hit set, not the entire index.
