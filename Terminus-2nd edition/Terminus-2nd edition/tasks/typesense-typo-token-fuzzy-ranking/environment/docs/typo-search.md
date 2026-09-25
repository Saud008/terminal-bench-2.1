# Typo-tolerant search

Query tokens with length at least four may match index vocabulary entries within TB3_TYPO_DISTANCE Levenshtein edits (default 1). Build a variant list per query token: always include the original query token, then add vocabulary terms within the distance limit when length is at least four.

Ranking compares each document index term against every variant from that list. The match-weight function always receives the variant string as its query-side token, not the raw query token from the user input. Set the typo-expansion flag when the variant string differs from the original query token for that position.

When the variant equals the index term, the weight is 1.0. This equality check is on the variant side: a typo-expanded variant such as laptop matching an index term laptop scores 1.0 even though the user typed laptp. When the variant differs from the index term and the typo-expansion flag is set, the weight is 0.85. Otherwise apply prefix scoring using the variant as the query-side token.

Typo expansion must use the full index vocabulary before any brand filter removes documents from consideration. Ranking must evaluate typo-expanded tokens against every indexed document, then apply brand filters to the ranked hit list.

Prefix matches score 0.5 plus half the ratio of matched prefix length to full token length using UTF-8 byte lengths, not Unicode scalar counts.
