# Xapian-style WDF-IDF weight

Let N be the document count in the index. For each term t, collection frequency cf(t) is the number of distinct documents whose collapsed posting list contains t (each document contributes at most once per term).

After positional collapse (see token-collapse.md), let slots(t, d) be how many collapsed slots in document d carry term t. Within-document frequency is wdf(t, d) = 1 + ln(slots(t, d)) using natural logarithm; slots of zero never occur for indexed terms.

Inverse document frequency is idf(t) = ln((N + 1) / (cf(t) + 1)) for every query term on every branch.

Unique term length len_unique(d) is the count of distinct term strings appearing in the collapsed slot list of d (not raw token count). Length normalization is len_norm(d) = 1 / sqrt(len_unique(d)).

For AND queries, raw weight is the sum over query terms q of effective_wdf(q, d) * idf(q). For OR queries, raw weight is the sum over query terms q of effective_wdf(q, d) * idf(q) (missing terms contribute zero). effective_wdf includes synonym expansion per synonym-policy.md.

Final score is raw_weight * len_norm(d). Rank descending score; tie-break docid ascending lexicographically.
